#!/usr/bin/python -u
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 et sts=2 ai:
"""
Script to update the DS keys on dlv.isc.org "look asside" DNSSEC system.
"""

import ConfigParser
import color
import os
import subprocess

root = os.path.dirname(__file__)
if not root:
  root = os.path.realpath(".")

# Load the configuration
configfile = os.path.join(root, 'config.ini')
config = ConfigParser.ConfigParser()
config.readfp(open(configfile))

curdir = os.path.realpath(os.curdir)

for domain in sorted(config.sections()):
  if not config.has_option(domain, "publish"):
    continue

  if not os.path.exists(domain):
    print "Could not find directory for %s" % (domain,)
    continue

  if not os.path.isdir(domain):
    print "%s is not a directory!" % (domain,)
    continue

  print domain
  publish_to = config.get(domain, "publish").split(',')
  os.chdir(domain)
  for publisher in publish_to:
    check_prog = "%s/check_%s.py" % (root, publisher)
    if not os.path.exists(check_prog):
      check_prog = "%s/check_root.py" % (root,)
    update_prog = "%s/update_%s.py" % (root, publisher)
    assert os.path.exists(check_prog)

    print " Checking", publisher
    c = subprocess.Popen("python -u %s %s" % (check_prog, domain), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    for line in c.stdout.xreadlines():
      print "   ", line.strip()
    retcode = c.wait()
    if retcode != 0:
      print color.yellow("   Need to update!")
      u = subprocess.Popen("python -u %s %s" % (update_prog, domain), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
      for line in u.stdout.xreadlines():
        print "   ", line.strip()
      retcode = u.wait()
      if retcode != 0:
        print color.red("   Update failed!")
      else:
        print color.green("   Update successful!")
    else:
      print color.green("   Everything up to date!")

    time.sleep(60)
  os.chdir(curdir)
