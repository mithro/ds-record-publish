#!/usr/bin/python -u
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 et sts=2 ai:
"""
Script to update the DS keys on dlv.isc.org "look asside" DNSSEC system.
"""

from BeautifulSoup import BeautifulSoup

import ConfigParser
import htmllib
import logging
import mechanize
import os
import StringIO
import sys
import re
import time
import subprocess

# Check the input arguments
domain = sys.argv[1]
assert os.path.exists(domain), "domain file not found: %s" % domain
dnskey = "dnskey-%s." % domain
assert os.path.exists(dnskey), "dnskey file not found: %s" % dnskey

# Load the configuration
configfile = os.path.join(os.path.dirname(__file__), 'config.ini')
config = ConfigParser.ConfigParser()
config.readfp(open(configfile))


def unescape(s):
  p = htmllib.HTMLParser(None)
  p.save_bgn()
  p.feed(s)
  return p.save_end()

def link_with_authtok(br, string, method, url=""):
  """Method to follow a link which has javascript authtok protection."""
  key_details_soup = BeautifulSoup(br.response())
  a_delete_key = key_details_soup.find(
      lambda tag: tag.name == 'a' and tag.string==string)
  delete_key_groups = re.search("s.setAttribute\('name', 'authenticity_token'\); s.setAttribute\('value', '([^']+)'\);", dict(a_delete_key.attrs)['onclick'])

  new_forms = mechanize.ParseFile(
      StringIO.StringIO("""
<form action="%s" method="POST">
<input type=hidden name="_method" value="%s">
<input type=hidden name="authenticity_token" value="%s">
<input type="submit">
</form>
""" % (br.response().geturl()+url, method, delete_key_groups.groups()[0])),
      br.response().geturl()+url,
      backwards_compat=False,
      )

  br.form = new_forms[0]
  br.submit()

def key_details_page(br, dlvid):
  details_url = "https://dlv.isc.org/zones/%s" % dlvid
  br.open(details_url)
  br.follow_link(text="(details)")

# The crappy mechanized virtual browser
br = mechanize.Browser()

# Login to the dlv.isc.org website
br.open("https://dlv.isc.org/session/new")
br.select_form(nr=1)
br.form["session[login]"]=config.get('dlv', 'username')
br.form["session[password]"]=config.get('dlv', 'password')
br.submit()

# Go to the manage zones page
while True:
  response = br.follow_link(text="Manage Zones")

  # Find the row with the domain we are updating
  soup = BeautifulSoup(br.response())
  rows = soup.find("table", attrs={'class': 'zebra'}).findAll('tr')
  for row in rows[1:]:
    cells = row.findAll('td')

    row_domain = cells[0].text
    status = cells[1].text
    dlvid = dict(cells[3].findAll('a')[0].attrs)['href'][7:]

    if row_domain == domain:
      break

  else:
    assert False, "Did not find domain %s on dlv.isc.org" % domain

  print domain, status, dlvid

  if status == "Good":
    print "Skipping as status was good."
    sys.exit(1)

  if status == "Unconfigured(?)":
    break

  # Go to the details page
  key_details_page(br, dlvid)

  # Remove the old keys
  link_with_authtok(br, "(delete record)", "delete")

# Upload the new keys
br.open("https://dlv.isc.org/zones/%s/dnskeys/new" % dlvid)

br.select_form(nr=1)
br.add_file(open(dnskey), "text/plain", dnskey)
br.submit()

response_soup = BeautifulSoup(br.response())
print response_soup.find(attrs={"id": "content"}).text

br.follow_link(text="(back to zone information)")

# Get the new DLV cookie record
details_soup = BeautifulSoup(br.response())
cookie = unescape(details_soup.find(attrs={"class": "screener tty"}).div.string)

# Write the cookie into the zone file, update the SOA
soa = None
zonedata_in = file(domain, 'r').readlines()
zonedata_out = []
for i, line in enumerate(zonedata_in):
  if "SOA" in line:
    # Figure out the spacing
    soa_line = zonedata_in[i+1]
    soa = soa_line.strip().split()[0]
    print "Current serial %s" % soa
    startpos = soa_line.find(soa)
    endpos = startpos + len(soa)

    new_soa = str(int(soa)+1)
    print "Update serial to %s" % new_soa
    zonedata_in[i+1] = soa_line[:startpos] + str(new_soa) + soa_line[endpos:]
  if not line.startswith('dlv.'):
    zonedata_out.append(line)

zonedata_out.append(cookie)
file(domain, 'w').write("".join(zonedata_out))

# Call zonesigner
subprocess.call(config.get('dlv', 'sign-cmd') % domain, shell=True)

# Wait for the secondary to get the domain information
def wait(domain):
  print "Waiting for secondaries to pick up config."
  servers = subprocess.Popen("dig @localhost %s NS +short" % domain, shell=True, stdout=subprocess.PIPE).stdout.readlines()
  mysoa = subprocess.Popen("dig @localhost %s SOA +short" % domain, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
  print "My SOA is %s" % mysoa
  while True:
    for server in servers:
       soa = subprocess.Popen("dig @%s %s SOA +short" % (server[:-1], domain), shell=True, stdout=subprocess.PIPE).stdout.read().strip()
       if soa != mysoa:
          print "[FAILED] Server %s has SOA %s" % (server[:-1], soa)
          break
       else:
          print "[OK] Server %s has SOA %s" % (server[:-1], soa)
    else:
      break
    time.sleep(5)
    subprocess.call(config.get('dlv', 'notify-cmd') % domain, shell=True)
  return mysoa

subprocess.call(config.get('dlv', 'reload-cmd') % domain, shell=True)
wait(domain)

if config.get('dlv', 'reload')[0].lower() == 'y':
  # Go to the details page
  key_details_page(br, dlvid)

  # Poke the checker
  link_with_authtok(br, "(request re-check)", "put", "/recheck")

  # Output the log
  key_details_soup = BeautifulSoup(br.response())
  logs = key_details_soup.find(attrs={"class": "screener"}).findAll(
      lambda tag: tag.name == 'span' and len(tag.attrs) == 0)

  for log in logs:
    print log.string
