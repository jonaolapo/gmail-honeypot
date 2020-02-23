# -*- coding: utf-8 -*-

""" Attributor
Author: Jeremiah Onaolapo 2016

Attributes actions in the honey accounts to accesses (cookies).
"""

import re,glob
import os.path
import cPickle as pickle
import time
import json
import pprint as pp
from bs4 import BeautifulSoup
import codecs
from collections import defaultdict
import numpy as np
import sys
import csv

import unicodeheaven
from honeylogger import honeylogger
from loadmeta import loadmeta
from parsepop import parsepop
from normaddr import normaddr
from timestamp_is_in_experiment import is_valid_time

# Essential lines
metadata = loadmeta('metadata.conf')
honeylogger('','Starting...')

###-
COOKIEBOX = metadata['COOKIE_BOX']
ATTRIB = metadata['ATTRIBOX']
POPDIR = metadata['DIR_POP']
CREDS = metadata['DIR_CREDS']
ALL_READ_OR_STARRED = metadata['ALL_R_A_S']
BN_ORACLE = metadata['BN_ORACLE']
COOKIE_WHL = metadata['COOKIE_WHITELIST']

###-
def update_field(oldls, newitem):
	print 'OLD!.....'
	pp.pprint(oldls)
	print 'NEW!....' 
	pp.pprint(newitem) 
	s = set(oldls)
	s.add(newitem)
	return list(s)

###-
def get_dist_range(dis_old_min,dis_old_max,dis_new):
	dmin = min(dis_old_min,dis_new)
	dmax = max(dis_old_max,dis_new)
	
	return (dmin,dmax)
	
###-
def push_to_cookie_box(cookie,tups):
	global cookiejar
	
	if not cookie in cookiejar:
		cookiejar[cookie] = {}
		for t in tups:
			if t[0] == "dist_range":
				dr = get_dist_range(t[1],t[1],t[1])
				cookiejar[cookie]["dist_range"] = [dr[0],dr[1]]
			else:
				cookiejar[cookie][t[0]] = [t[1]]
	else:
		for t in tups:
			if t[0] in cookiejar[cookie]:
				if t[0] == "dist_range":
					oldv = cookiejar[cookie]["dist_range"]
					dr = get_dist_range(oldv[0],oldv[1],t[1])
					cookiejar[cookie][t[0]] = [dr[0],dr[1]]
				else:
					cookiejar[cookie][t[0]] = update_field(cookiejar[cookie][t[0]],t[1])
			else:
				if t[0] == "dist_range":
					dr = get_dist_range(t[1],t[1],t[1])
					cookiejar[cookie]["dist_range"] = [dr[0],dr[1]]
				else:
					cookiejar[cookie][t[0]] = [t[1]]

###- START ###
all_read_or_starred = {}

cbox = None
cookiejar = {}
bn_oracle = pickle.load(open(BN_ORACLE))

wlist_cookies = set([]) 
with open(COOKIE_WHL) as f:
	for line in f:
		wlist_cookies.add(line.strip())
				
# Read cookiebox from disk
with open(COOKIEBOX, 'rb') as f:
	cbox = pickle.load(f)

cnt = defaultdict(int)

# Copy only blacklisted cookies to cookiejar
for cooki,d in cbox.items():
	if cooki in wlist_cookies: 
		honeylogger('','WHITELISTED cookie in cookiebox. Will skip!'.format(cooki))
		continue

	if "email_addr" in d:
		em = d["email_addr"][0]
		d["batchnum"] = [bn_oracle[em]['batchnum']]

	cookiejar[cooki] = d
	# Check if cookie has tstamp_last_seen value and increment appropriate counter
	try:
		cooki_tls = int(str(d['tstamp_last_seen'][0])[:10])
		cnt["has_tstamp_last_seen"] += 1
	except:
		cnt["no_tstamp_last_seen"] += 1

honeylogger("", "tstamp_last_seen stats: {}".format(str(cnt)))

m_ids = set([])

# Start attribution
for fil in glob.glob("{}/*".format(POPDIR)):
	# sanity checks
	if "@gmail.com" not in fil.lower():
		honeylogger("","'@gmail.com' not in filename: {} - NO INTEREST. Will skip!!!".format(fil))
		continue
	if metadata['SAFEHOUSE'] in fil.lower():
		honeylogger("","SAFEHOUSE address in filename: {} - NO INTEREST. Will skip!!!".format(fil))
		continue

	dat = ''
	with open(fil) as fh:
		dat = ''.join(fh.readlines())

	if 'content-disposition: attachment' not in dat.lower() and '.txt' not in dat.lower():
		honeylogger('invalid! No attachment of interest in file!',fil)
		continue
	
	fpath, fname = os.path.split(fil)
	poptstamp,a,email_addr,b,c = fname.split('_')

	if not is_valid_time(poptstamp,metadata):
		honeylogger('poptstamp outside experiment dates! Will skip!',fname)
		continue

	# Remove dots from username part of email_addr
	# and change its chars to lowercase
	email_addr = normaddr(email_addr)

	poptstamp = int(float(poptstamp))
	mindist = 9999999999
	bestcookie = ''
	
	for cooki,d in cookiejar.items():
		try:
			if normaddr(d['email_addr'][0].strip()) != normaddr(email_addr.strip()): 
				# not a cookie of interest
				continue
		except Exception, e:
			#print cooki,d
			honeylogger(str(e),"error while comparing email_addr in cookie {0} dict and popfile {1}".format(cooki,fname))
			
		cooki_tls = []
		try:
			tls = []
			if d['tstamp_last_seen']:
				for t in d['tstamp_last_seen']:
					#print t
					tls.append(int(t))
				cooki_tls = max(tls)
				#print "cooki_tls",cooki_tls
		except:
			cooki_tls = -1
		
		cdist = abs(poptstamp - cooki_tls)
		
		#print "cdist, mindist", cdist, mindist
		if cdist <= mindist:
			mindist = cdist 
			bestcookie = cooki
		#print "bestcookie,mindist", bestcookie,mindist
	
	#print "WIN:bestcookie,mindist", bestcookie,mindist
	# If no cookie is found to correlate with the action, store action in dummycookie
	#ac = parsePOP(fil)
	rdat = parsepop(fil,m_ids)	
	ac = rdat[0]

	# sanity checks before updating stuff
	if "race_condition" in ac: continue 
	if "heartbeat" in ac: continue
	
	for el in ac:
		if 'invalid' in el:
			honeylogger(el,fil)
			continue

	# if sanity checks are passed, update data
	det = rdat[2]
	m_ids = rdat[3]
	ras = rdat[1] 

	s = set(ac)
	acs = ''
	for el in s:
		acs += '{}'.format(el)
	popacts = (email_addr,acs,poptstamp,fname)
	if not bestcookie:
		# If cookie doesn't exist yet, create dummycookie
		k = "dummycookie_{}".format(poptstamp)
		cookiejar[k] = {}
		tupz = [("tstamp_last_seen",0),("email_addr",email_addr),("popacts",popacts),("dist_range",mindist)]
		push_to_cookie_box(k,tupz)
		bestcookie = k
	else:
		tupz = [("popacts",popacts),("dist_range",mindist)]
		push_to_cookie_box(bestcookie,tupz)

	istfidf = 0
	if ac and ras:
		ki = '{}_{}_{}'.format(bestcookie,email_addr,fname)
		all_read_or_starred[ki] = rdat[1]
		istfidf = 1
	
	if 'details' not in cookiejar[bestcookie]:
		cookiejar[bestcookie]['details'] = {}
	
	for popf,d in det.items(): 
		cookiejar[bestcookie]['details'][popf] = d
	cookiejar[bestcookie]['istfidf'] = istfidf 
 
with open(ALL_READ_OR_STARRED, 'wb') as f:
	pickle.dump(all_read_or_starred,f)
	
with open(ATTRIB, 'wb') as f:
	pickle.dump(cookiejar,f)
	
print cnt
honeylogger("", "Stopping...")
