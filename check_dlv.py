#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:
"""
Script to check if the DLV "look aside" register has your DS records.
"""
import os
import subprocess
import sys

# Check the input arguments
domain = sys.argv[1]
assert os.path.exists(domain), "domain file not found: %s" % domain
dsset = "dsset-%s." % domain
assert os.path.exists(dsset), "dsset file not found: %s" % dsset

subprocess.call(["rndc", "flushname", domain+".dlv.isc.org."])
p = subprocess.Popen(["dig", "+short", "DLV", domain+".dlv.isc.org."], stdout=subprocess.PIPE)
p.wait()

tocheck = []
for line in file(dsset):
  domain, in_, ds_, a, b, c, d = line.split(None, 6)
  tocheck.append("%s %s %s %s" % (a, b, c, d))

tocheck.sort()

ds_records = p.stdout.readlines()
ds_records.sort()

if ds_records == tocheck:
  print "DS records match"
  sys.exit(0)
else:
  print "DS records don't match"
  print "Published records:", ds_records
  print "  On disk records:", tocheck
  sys.exit(1)
