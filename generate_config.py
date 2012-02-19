#!/usr/bin/python -u
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 et sts=2 ai:
"""
Script to generate a config.ini file from the .krf found.
"""

import subprocess

p = subprocess.Popen("find -maxdepth 2 -name \*.krf | sed -e's-./--' | sort | uniq", shell=True, stdout=subprocess.PIPE)

for line in p.stdout.readlines():
  domain, krf = line.strip().split('/')
  print "[%s]" % domain

  publish = []
  if domain.split('.')[-1] in ('com', 'org', 'net'):
    publish.append("gkg")
  publish.append("dlv")
  print "publish=%s" % ",".join(publish)
  print
