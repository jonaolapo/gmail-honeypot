# -*- coding: utf-8 -*-
""" Cookie Cruncher
Author: Jeremiah Onaolapo 2016

Extracts information about accesses from (previously) scraped pages of honey accounts.
"""

import unicodeheaven
import re,glob
import os.path
import time
from bs4 import BeautifulSoup
import codecs
import json
import sys
import pickle
import json
import pprint as pp
import unicodedata
import csv

from honeylogger import honeylogger
from loadmeta import loadmeta
from timestamp_is_in_experiment import is_valid_time
from normaddr import normaddr


# Essential lines
metadata = loadmeta('metadata.conf')
honeylogger('','Starting...')

SCRAPEDUMPSDIR = metadata['DIR_SCRAPES']
COOKIEBOX = metadata['COOKIE_BOX']
WHITELISTFILE = metadata['PARSER_WHITELIST']
CREDS = metadata['DIR_CREDS']
EMPTYFILES = metadata['EMPTY_FILES']
WHITELISTEDCOOKIES = metadata['COOKIE_WHITELIST']


ls = []
all_cookies = {}
scripts_box = {}
wh_list = []
wh_cookies = set([])


###-
def check_wh_list(s,whlist):
	wlflag = 0
	if not s:
		s = "None"
	for w in whlist:
		if w.lower() in str(s).lower():
			wlflag = 1
			break
	return wlflag 


###-
def to_json(s):
	# To remove starting tag et al
	regx = re.compile(r"<script>(.*)\{return",re.IGNORECASE)
	# To remove ending tag et al
	regx2 = re.compile(r"\}\);</script>",re.IGNORECASE)
	
	out_ = re.sub(regx,'{"data":',s)
	out_ = re.sub(regx2,'',out_)
	data = None
	try:
		data = json.loads(out_)
	except Exception,e:
		honeylogger(str(e),"")

	return data

###-
def update_field(oldls, newitem):
	s = set(oldls)
	s.add(newitem)
	return list(s)

###-
def push_to_cookie_box(couki,tupsi):
	global all_cookies
	
	if not couki in all_cookies:
		all_cookies[couki] = {}
		for t in tupsi:
			all_cookies[couki][t[0]] = [t[1]]
	else:	
		for t in tupsi:
			if t[0] in all_cookies[couki]:
				all_cookies[couki][t[0]] = update_field(all_cookies[couki][t[0]],t[1])
			else:
				all_cookies[couki][t[0]] = [t[1]]
	
###-
def trim_gtstamp(ts):
	tts = str(ts)[:10]
	return int(tts)

###-
def update_cookie_box(lst,emaddr):
	global wh_list
	global isprior


	if not lst[0] == 'sfe.sc.dr':
		honeylogger('','error in {0} script: first element of lst has unexpected value -- {1}. Will not be processed.'.format(emaddr,str(lst[0])))
	else:
		noippack = lst[2]
		for noip in noippack:
			cookie = noip[0]
			if isprior:
				wh_cookies.add(cookie)
			os = noip[1]
			tstamp_fs = trim_gtstamp(noip[2])
			tstamp_ls = trim_gtstamp(noip[3])
			loca = ""
			if len(noip[13]) > 0:
				loca = noip[13][0][2]
			if not loca:
				loca = "None"

			tupz = [("os",os),("tstamp_first_seen",tstamp_fs),("tstamp_last_seen",tstamp_ls),("location",loca),("email_addr",emaddr)]

			# Run through whitelist
			flg = 0
			for el in [loca]:
				flg = check_wh_list(el,wh_list)
				if flg == 1: break # Match found
			if flg == 0:
				push_to_cookie_box(cookie,tupz)
			else:
				honeylogger("","{} -- COOKIE {} WHITELISTED, HAS LOCATION: {}".format(emaddr,cookie,str(loca)))
				wh_cookies.add(cookie)
		ippack = lst[4]
		for ipp in ippack:
			ippaddr = ipp[3]
			loca = ipp[4]
			browser = ipp[8][0]
			browser_ver = ipp[8][1]
			os = ipp[8][2]
			os_ver = ipp[8][4]
			cookie = ipp[14]
			
			if isprior:
				wh_cookies.add(cookie)

			if not loca:
				loca = "None"
				
			tupz = [("ipaddr",ippaddr),("location",loca),("browser",browser),("browser_ver",browser_ver),("os",os),("os_ver",os_ver),("email_addr",emaddr),("tstamp_last_seen",0)]

			# Run through whitelist
			flg = 0
			for el in [loca, ippaddr]:
				flg = check_wh_list(el,wh_list)
				if flg == 1: break # Match found
			if flg == 0:
				push_to_cookie_box(cookie,tupz)
				
###- START
wh_list = []

eset = None
if os.path.isfile(EMPTYFILES):
	eset = pickle.load(open(EMPTYFILES))
else:
	eset = set([])


###-
def addtoemptyfiles(fp):
	global eset
	eset.add(str(fp))

###-
def isfileempty(fp):
	global eset
	retval = 'False'	
	if eset:
		if set([str(fp)]).intersection(eset):
			retval = 'True'			
	return retval
		
		
###-
with open(WHITELISTFILE, 'rb') as fi:
	for line in fi:
		if line.strip():
			wh_list.append(line.strip())

bn_oracle = pickle.load(open(metadata['BN_ORACLE']))

all_cookies = {}
i = 0

isprior = 0

try:
	for fil in glob.glob("{}/batch*/*".format(SCRAPEDUMPSDIR)):
		fpath, fname = os.path.split(fil)
		a,bt = os.path.split(fpath)
		email_addr,tstamp_scrape,randval = fname.split('_')
		isvalid,isprior = is_valid_time(tstamp_scrape,metadata)
		if not isvalid and not isprior:
			honeylogger('tstamp_scrape NOT in range of experiment dates. Will skip!',fname)
			continue
		email_addr = normaddr(email_addr)
		
		# Update times of scrapes in bn_oracle
		if email_addr not in bn_oracle:
			honeylogger('{} not in bn_oracle'.format(email_addr),'will not processed:{}'.format(fil))
			addtoemptyfiles(str(fil))
			continue
		
		if 'all_t_scrape' not in bn_oracle[email_addr]:
			bn_oracle[email_addr]['all_t_scrape'] = [tstamp_scrape]
		else:
			tsc = bn_oracle[email_addr]['all_t_scrape']
			tsc.append(tstamp_scrape)
			t = list(set(tsc))
			bn_oracle[email_addr]['all_t_scrape'] = t
		
		
		# Check to see if file contains no cookies
		if isfileempty(fil) is 'True': 
			continue
		
		html_doc = ''
		with open(fil, 'rb') as f:
			html_doc = f.read()
		soup = BeautifulSoup(html_doc, 'html.parser')
		# Only scripts needed
		scri = soup.find_all("script")
		#print scri
		scripts = []
		for sc in scri:
			x = str(sc).replace("&quot;", "\"")
			scripts.append(x)
		
		for line in scripts:
			# Search for sequence of timestamps in line
			if not re.search(r',[1][4]\d{11},[1][4]\d{11},',line): 
				addtoemptyfiles(str(fil))
				continue
				
			clnd_scr = line.replace('\n', '').replace('\r', '')
			newjson = to_json(clnd_scr)
		
			if not newjson: 
				honeylogger("", "json parsing failed in one of the scripts in {}".format(fil))
				continue
			update_cookie_box(newjson["data"],email_addr)
except Exception, e:
	honeylogger('Some scrape files not read! Re-run!',str(e))
	with open(EMPTYFILES, 'wb') as f:
		pickle.dump(eset, f)
finally:
	with open(EMPTYFILES, 'wb') as f:
		pickle.dump(eset, f)

# Update values of times of scrape
for cooki in all_cookies:
	t_first_scrape = 0
	t_last_scrape = 0
	email_addr = all_cookies[cooki]['email_addr'][0]
	
	# Add emnum field to all cookies
	all_cookies[cooki]['emnum'] = bn_oracle[email_addr]['emnum']
	
	tsc = bn_oracle[email_addr]['all_t_scrape']
	if tsc:
		t_first_scrape = min(tsc)
		t_last_scrape = max(tsc)
		
	all_cookies[cooki]["t_first_scrape"] = t_first_scrape 
	all_cookies[cooki]["t_last_scrape"] = t_last_scrape

# one last update to list of whitelisted cookies
for cooki,d in all_cookies.items():
	if 'tstamp_last_seen' in d:
		if len(d['tstamp_last_seen']) > 15:
			honeylogger('too many TLS values in cookie! will WHITELIST and skip!!!','')
			wh_cookies.add(cooki)

# Dump all_cookies dict to disk
with open(COOKIEBOX, 'wb') as fo:
	pickle.dump(all_cookies,fo)

with open(metadata['COOKIE_WHITELIST'],'w') as f:
	for c in wh_cookies:
		f.write("{}\n".format(c))

honeylogger("", "Stopping...")
