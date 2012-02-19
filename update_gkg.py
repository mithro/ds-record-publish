#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 et sts=2 ai:
"""
Script to update the DS keys on dlv.isc.org "look asside" DNSSEC system.
"""

import ConfigParser
import color
import logging
import pprint
import os
import simplejson
import sys
import urllib2

class DeleteRequest(urllib2.Request):
  def __init__(self, *args, **kwargs):
    self._method = kwargs.pop('method', 'DELETE')
    urllib2.Request.__init__(self, *args, **kwargs)
  def get_method(self):
    return self._method

# Check the input arguments
domain = sys.argv[1]
dsset = "dsset-%s." % domain
assert os.path.exists(dsset), "dsset file not found: %s" % dsset

# Load the configuration
configfile = os.path.join(os.path.dirname(__file__), 'config.ini')
config = ConfigParser.ConfigParser()
config.readfp(open(configfile))

username = config.get('gkg', 'username')
password = config.get('gkg', 'password')

mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
mgr.add_password(
    None,
    'https://www.gkg.net/',
    user=username,
    passwd=password)
auth_handler = urllib2.HTTPBasicAuthHandler(mgr)
opener = urllib2.build_opener(auth_handler)
urllib2.install_opener(opener)

url = "https://www.gkg.net/ws/domain/%s/ds" % domain
current_records = simplejson.loads(urllib2.urlopen(url).read())

# "Save" on the Manage DS Records window
new_records = []
for line in file(dsset):
  # thousandparsec.com.     IN DS 57841 5 2 DEA43569E59B6F2FEB99B799BCD39927769A3CA369A846122DE11595 D31A728A
  ds_domain, in_, ds_, keytag, algorithm, digest_type, digest = line.split(None, 6)

  new_records.append({
      'digest': "".join(digest.split()),
      'digestType': digest_type,
      'algorithm': algorithm,
      'keyTag': keytag,
      'maxSigLife': str(3600*24*90), # FIXME(tansell): Defaulting to 90 days...
      })

to_add = []
for dsrecord in sorted(current_records):
  dsid = dsrecord['keyTag']+" "+dsrecord['algorithm']
  if dsrecord in new_records:
    print color.green("Current %s" % dsid)
  else:
    print color.red("Removing %s" % dsid)
    req = DeleteRequest(
        url="https://www.gkg.net/ws/domain/%s/ds/%s" % (domain, dsrecord['digest']),
        )
    print urllib2.urlopen(req).read()

for dsrecord in sorted(new_records):
  if dsrecord in current_records:
    continue

  dsid = dsrecord['keyTag']+" "+dsrecord['algorithm']
  print color.yellow("Adding %s" % dsid)
  url = "https://www.gkg.net/ws/domain/%s/ds" % domain
  r = urllib2.urlopen(url, data=simplejson.dumps(dsrecord))
  print r.read()
