"""
Script to update the DS keys on a GoDaddy Domain.
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
import simplejson
import urllib
import uuid


# Check the input arguments
domain = sys.argv[1]
assert os.path.exists(domain), "domain file not found: %s" % domain
dsset = "dsset-%s." % domain
assert os.path.exists(dsset), "dsset file not found: %s" % dsset

# Load the configuration
config = ConfigParser.ConfigParser()
config.readfp(open('config.ini'))


def unescape(s):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()

def get_viewstate(br):
  groups = re.search('<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="([^"]*)"', br.response().read())
  return groups.groups()[0]

# The crappy mechanized virtual browser
br = mechanize.Browser()
br.set_handle_robots(False)
br.set_debug_responses(True)
br.set_debug_http(True)
br.set_debug_redirects(True)

# Login to the GoDaddy website
br.open("http://www.godaddy.com/")
br.select_form(name="pchFL")

br.form["loginname"]=config.get('godaddy', 'username')
br.form["password"]=config.get('godaddy', 'password')
br.submit()

# Go to the admin interface
br.open("https://dcc.godaddy.com/")

# Figure out the IDs for the domain we care about
soup = BeautifulSoup(br.response())
rows = soup.find("table", attrs={
  "class": "grid", "id": "ctl00_cphMain_DomainList_gvDomains"}).findAll("a")

for row in rows:
  if row.string.lower() == domain.lower():
    break

# We need to do a json request to get the full domain id
callback = dict(row.attrs)['onclick']
groups = re.search(r"OpenDetailsIdentifer\(([^,]+), ([01]), ([01]), ([01]),\\'([^\\]*)\\', ([^\)]+)\);", callback)
domain_short_id = groups.groups()[0]
sInput = """\
{"sInput":"<PARAMS><PARAM name=\\"domainID\\" value=\\"%s\\" /><PARAM name=\\"activeview\\" value=\\"%s\\" /><PARAM name=\\"filtertype\\" value=\\"%s\\" /><PARAM name=\\"action\\" value=\\"%s\\" /><PARAM name=\\"querystring\\" value=\\"%s\\" /><PARAM name=\\"isKHView\\" value=\\"%s\\" /></PARAMS>"}\
""" % groups.groups()

r = mechanize.Request(
    url="https://dcc.godaddy.com/DomainListWS.asmx/GetDomainIdentifier",
    headers={'Content-Type': 'application/json; charset=UTF-8'},
    data=sInput)

br.open(r, data=sInput)
result = simplejson.loads(br.response().get_data())["d"]

get_domain_id_soup = BeautifulSoup(result)
full_domain_id = get_domain_id_soup.find("identifier").string

# Go to the domain's details page
domain_details_url = "https://dcc.godaddy.com/DomainDetails.aspx?identifier=%s&activeview=1&filtertype=1" % urllib.quote(full_domain_id)
br.open(domain_details_url)
domain_details_page = br.response().read()

guid = str(uuid.uuid1()).upper()

# "Open" the Manage DS Records window
# FIXME: This is super fragile......
data1 = {
    "__EVENTTARGET": "ctl00_btnLoadIt",
    "__EVENTARGUMENT": "",
    "__VIEWSTATE": get_viewstate(br),
    "ctl00$hdnSelectedAction": "ActionDnsSec",
    "ctl00$hdnVariableHold": "",
    "ctl00$hdnParentURL": domain_details_url,
    "ctl00$hdnLoaded": "0",
    "ctl00$hdnCustomHeight": "560",
    "ctl00$hdnBottomHeight": "200",
    "ctl00$hdnCustomWidth": "780",
    "ctl00$hdnFrameGetBig": "1",
    "ctl00$hdnSentCICode": "0",
    "ctl00$hdnErrorTitle": "",
    "ctl00$hdnErrorMessage1": "",
    "ctl00$hdnErrorMessage2": "",
    "ctl00$hdnErrorDetails": "",
    "ctl00$hdnShowOkButton": "",
    "ctl00$hdnSelectedDomains": domain_short_id + "|",
    }

br.open(
  "https://dcc.godaddy.com/DropinLoad_Domain.aspx?controlRequest=ActionDnsSec&initiator=1&guid=%s" % guid,
  data=urllib.urlencode(data1))

# "Save" on the Manage DS Records window
dsrecords = []
for line in file(dsset):
  # thousandparsec.com.     IN DS 57841 5 2 DEA43569E59B6F2FEB99B799BCD39927769A3CA369A846122DE11595 D31A728A
  domain, in_, ds_, a, b, c, d = line.split(None, 6)
  d = "".join(d.split())
  dsrecords.append("advanced||%(a)s|%(b)s|%(c)s|%(d)s|||")

# FIXME: This is super fragile......
data2 = {
    "__EVENTTARGET": "ctl00_cphAction1_ctl00_btnOK",
    "__EVENTARGUMENT": "",
    "__VIEWSTATE": get_viewstate(br),
    "ctl00$hdnSelectedAction": "ActionDnsSec",
    "ctl00$hdnVariableHold": "",
    "ctl00$hdnParentURL": domain_details_url,
    "ctl00$hdnLoaded": "1",
    "ctl00$hdnCustomHeight": "660",
    "ctl00$hdnBottomHeight": "285",
    "ctl00$hdnCustomWidth": "780",
    "ctl00$hdnFrameGetBig": "1",
    "ctl00$hdnSentCICode": "1",
    "ctl00$hdnErrorTitle": "",
    "ctl00$hdnErrorMessage1": "",
    "ctl00$hdnErrorMessage2": "",
    "ctl00$hdnErrorDetails": "",
    "ctl00$hdnShowOkButton": "",
    "ctl00$hdnSelectedDomains": domain_short_id + "|",
    "ctl00$cphAction1$ctl00$hdnValidated": "1",
    "ctl00$cphAction1$ctl00$txtKeyTag": "",
    "ctl00$cphAction1$ctl00$ddAlgorithm": "Select one...",
    "ctl00$cphAction1$ctl00$ddDigestType": "Select one...",
    "ctl00$cphAction1$ctl00$txtMaxSigLife": "Not Supported",
    "ctl00$cphAction1$ctl00$txtPublicKey": "",
    "appendBehaviour": "replace",
    "ctl00$cphAction1$ctl00$hdnCommitDSRecords": ";".join(dsrecords),
    "ctl00$cphAction1$ctl00$hdnClientEnabled": "true",
    "ctl00$cphAction1$ctl00$hdnAllowAdvancedMode": "1",
    "ctl00$cphAction1$ctl00$hdnNumberOfRecordsAllowed": "13",
    }

br.open(
  "https://dcc.godaddy.com/DropinLoad_Domain.aspx?controlRequest=ActionDnsSec&initiator=1&guid=%s" % guid,
  data=urllib.urlencode(data2))

print br.response().read()


#############################
#############################
# Check the parameters validate
#sInput = """\
#{"sInput":"<PARAMS><PARAM name=\\"resourceID\\" value=\\"%s\\" /><PARAM name=\\"isAppendMode\\" value=\\"false\\" /><PARAM name=\\"0\\" value=\\"57841|5|1|7582EF9BDD25AA732DD49691EE943D8A033E711D|3600\\" /><PARAM name=\\"1\\" value=\\"57841|5|2|DEA43569E59B6F2FEB99B799BCD39927769A3CA369A846122DE11595D31A728A|3600\\" />
#"""
#"""
#sInput += '<PARAM name=\\"0\\" value=\\"%(a)s|%(b)s|%(c)s|%(d)s|3600\\" />' % locals()
#
#sInput += '</PARAMS>"}';
#r = mechanize.Request(
#    url="https://dcc.godaddy.com/DomainAction_DnsSec.asmx/Validate",
#    headers={'Content-Type': 'application/json; charset=UTF-8'},
#    data=sInput)
#"""
