#!/usr/bin/python -u
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 et sts=2 ai:
"""
Script to parse out the current DNSKEY values from a signed file.

Must be in the following format;
                        38400   DNSKEY  256 3 5 (
                                        AwEAAcc+5wWgFISZqPJRQ31LBi65CoBZmmkB
                                        JAbHGZXDVAmhfY+wl97bhBQASbJBPd0J1jrh
                                        NLUTvvUyzEw3KdAQRAp0JUm9KSt3E5d6TLWn
                                        O+3X/fMnGUh5NSk6i6j0Ci1xD2TcyJc0K/dA
                                        GNAfswVUMuDryUZrFWvwbyO+f4a4dcyx
                                        ) ; key id = 14400
"""

import sys
import os

domain = sys.argv[1]
domainfile = domain+".signed"
assert os.path.exists(domainfile), "domain file not found: %s" % domainfile
f = open(domainfile).readlines()

outputfile = "dnskey-%s." % domain
o = open(outputfile, 'w')

line = None
while len(f) > 0:
  line = f.pop(0)
  if "DNSKEY" not in line:
    continue
  if "RSIG" in line:
    continue

  dnskey = [line]
  while "key id" not in dnskey[-1]:
    dnskey.append(f.pop(0))

  o.write("".join(dnskey))

"""
FIXME: Code for generating DS records

  ttl, dnskey, keytype, y, algorithm, digest, colon, key, id_, equal, keyid = "".join(x.strip() for x in dnskey).split()
  if keytype == "256":
    keytype = "ZSK"
  elif keytype == "257":
    keytype = "KSK"
  else:
    raise SyntaxError("Unknown key type!")

  digest = digest[1:-1]
  print "; %(keytype)s - %(keyid)s" % locals()
  print "%(domain)s. IN DS %(keyid)s %(y)s %(algorithm)s %(digest)s" % locals()
"""
