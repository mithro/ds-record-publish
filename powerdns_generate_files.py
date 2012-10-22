#! /usr/bin/python

"""
Convert the pdnssec show-zone format into ds/dnskey files.
"""
import os
import subprocess
import sys

domain = sys.argv[1]

output = subprocess.Popen(['pdnssec', 'show-zone', domain], stdout=subprocess.PIPE)

dnskey_filename = 'dnskey-%s.' % (domain,)
dsset_filename = 'dsset-%s.' % (domain,)

try:
  os.unlink(dnskey_filename)
except (IOError, OSError):
  pass
try:
  os.unlink(dsset_filename)
except (IOError, OSError):
  pass

dnskey_file = open(dnskey_filename, 'w')
dsset_file = open(dsset_filename, 'w')

for line in output.stdout.readlines():
  line = line.strip()
  if line.startswith('KSK DNSKEY ='):
    dnskey_file.write(line[13:]+'\n')
  elif line.startswith('DS ='):
    # mithis.com IN DS 63601 8 1 7a34ee24d183d330efbc039ba9f4bc6a93a5a43c
    _, a, b, c, d, e, f = line[5:].upper().split()

    maxlen = len("a668beacae23565e854a37108785bb650ab4fbae1a423ab9d6fc0caa")
    f = [f]
    while len(f[-1]) > maxlen:
       f.append(f[-1][maxlen:])
       f[-2] = f[-2][:maxlen]

    dsset_file.write("%s. %s %s %s %s %s %s\n" % (domain, a, b, c, d, e, " ".join(f)))

dnskey_file.close()
dsset_file.close()
