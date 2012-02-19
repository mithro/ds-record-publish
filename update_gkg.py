#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 et sts=2 ai:
"""
Script to update the DS keys on dlv.isc.org "look asside" DNSSEC system.
"""

import ConfigParser
import logging
import os
import simplejson
import sys
import urllib2

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

#"https://www.gkg.net/ws/domain/%s/ds" % domain

# "Save" on the Manage DS Records window
dsrecords = []
for line in file(dsset):
  # thousandparsec.com.     IN DS 57841 5 2 DEA43569E59B6F2FEB99B799BCD39927769A3CA369A846122DE11595 D31A728A
  ds_domain, in_, ds_, keytag, algorithm, digest_type, digest = line.split(None, 6)

  dsrecords.append({
      'digest': "".join(digest.split()),
      'digestType': digest_type,
      'algorithm': algorithm,
      'keyTag': keytag,
      'maxSigLife': 3600*24*90, # FIXME(tansell): Defaulting to 90 days...
      })

mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
mgr.add_password(
    None,
    'https://www.gkg.net/',
    user=username,
    passwd=password)
auth_handler = urllib2.HTTPBasicAuthHandler(mgr)
opener = urllib2.build_opener(auth_handler)
urllib2.install_opener(opener)

for dsrecord in dsrecords:
  url = "https://www.gkg.net/ws/domain/%s/ds" % domain
  print url
  try:
    r = urllib2.urlopen(url, data=simplejson.dumps(dsrecord))
    print r.read()
  except urllib2.HTTPError, e:
    if e.code == 403:
      print "DS record already existed."
    else:
      raise
