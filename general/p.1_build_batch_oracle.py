# -*- coding: utf-8 -*-

"""Batch oracle builder
Author: Jeremiah Onaolapo 2016

Builds a dictionary of honey accounts.
"""

import pickle
import os
import csv
from honeylogger import honeylogger
from loadmeta import loadmeta
from normaddr import normaddr

# Essential lines
metadata = loadmeta('metadata.conf')
honeylogger('','Starting...')

bn_oracle = {}

emailid = 0
n_batches = int(metadata['N_BATCHES'])			
for i in range(1,n_batches+1):
  bnum = i
  fil = "{}/batch{}auth.csv".format(metadata['DIR_CREDS'],bnum)
  fpath, fname = os.path.split(fil)
  with open(fil,'r') as f:
    readr = csv.reader(f)
    for row in readr:
      if row:
        email_addr = normaddr(row[1])
        if email_addr not in bn_oracle:
          emailid += 1
          bn_oracle[email_addr] = {}
          bn_oracle[email_addr]["batchnum"] = bnum
          bn_oracle[email_addr]["emnum"] = emailid

honeylogger('','len(bn_oracle): '+ str(len(bn_oracle)))

with open(metadata['BN_ORACLE'], 'wb') as fo:
  pickle.dump(bn_oracle,fo)

honeylogger('','Built batch oracle successfully.')
honeylogger('','Stopping...')
