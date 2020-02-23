# -*- coding: utf-8 -*-
import re,glob
import cPickle as pickle
import time
import base64
import os
import pprint as pp
import email
from email.parser import Parser
import unicodedata
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart

def parse_signals_and_emails(txt):
	n = len(txt)
	sigptr = 0
	numsigs = 0
	d = {}
	l = ''

	try:
		for i in range(0,n):
			l = txt[i]
			#l = unicodedata.normalize('NFKD',txt[i]).encode('ascii','ignore')
			if 'there are <strong>' in l.lower():
				# wrapper signal detected
				# extract number of signals
				# fix unicode issues
				l = l.decode('unicode_escape').encode('ascii','ignore')
				numsigs = int(l.split('<strong>')[1].split('</strong>')[0])
				break

		cmailid = -1
		#while parsedcnt < numsigs:
		for i in range(0,n):
			#l = txt[i].decode('unicode_escape').encode('ascii','ignore')
			#l = unicodedata.normalize('NFKD',txt[i]).encode('ascii','ignore')
			# check if line is a signal line
			l = txt[i]
			#print 'BLAOW', l
			if '***BEGINFLAG' in l: 
				# fix unicode issues
				l = l.decode('unicode_escape').encode('ascii','ignore')
				# update list
				txt[i] = l
				if 'there are <strong>' not in l.lower():
					# not a wrapper signal
					# get boundary data
					bdr = l.split('</span></p>')[0]
					if bdr:
						d[cmailid]['email'].append(bdr)
					else:
						# just a text fragment
						d[cmailid]['email'].append(l)

				# New cmailid at this point
				# but sanity checks first!
				if len(l.strip().split('MAILID:')) > 1 and l.strip().split('MAILID:')[0]:
					# valid. parse
					cmailid = l.split('MAILID:')[1].split('</p>')[0].strip()
					d[cmailid] = {}
					if 'SUBJECT:' not in l:
						# there is no subject line
						d[cmailid]['subject'] = ''
					else:
						d[cmailid]['subject'] = l.split('SUBJECT:')[1].split('</p>')[0].strip()
					d[cmailid]['flag'] = l.split('***BEGINFLAG***')[1].split('***ENDFLAG***')[0].strip()
					firsthdr = l.split("font-size:12px'>")[-1]
					d[cmailid]['email'] = [firsthdr]
				else:
					# just another text fragment
					d[cmailid]['email'].append(l)
			elif '</span></p>' in l and '--' in l:
				# the end?
				d[cmailid]['email'].append(l.replace('</span></p>',''))	
			else:
				# just another text fragment
				d[cmailid]['email'].append(l)

		#print "NUMSIGS!numsigs: ", numsigs
		#print "NUMSIGS!len(d):", len(d)
	except Exception, e:
		print "BLAOW: {}".format(str(e)), l

	# join up email strings in d
	for cmailid in d:
		if 'email' in d[cmailid]:
			d[cmailid]['email'] = '\n'.join(d[cmailid]['email'])
	return d


def remove_html(s):
	return re.sub('<[^<]+?>','',s)


def is_base64(s):
	s = ''.join([s.strip() for s in s.split("\n")])
	try:
		enc = base64.b64encode(base64.b64decode(s)).strip()
		return enc == s
	except TypeError:
		return False


def decode(a):
	result = a
	if is_base64(a.strip().replace("\n","")):
		result = base64.decodestring(a.strip().replace("\n",""))
		#print 'YAY!!!', result
	#try:
		#decoded = x.decode('base64', 'strict')
		#if x == decoded.encode('base64').strip():
			#result = decoded
			#print 'YAY!!!decoded', result
	#except:
		#pass
	return result

	
def get_body(mo):
	a = ''
	if mo.is_multipart():
		for part in mo.walk():
			ctype = part.get_content_type()
			if ctype not in ['application/pdf','text/html']:
				a = a + decode(str(part.get_payload()).strip()) + '\n'
				lines = a.splitlines()
				a = '\n'.join(el for el in lines if '<email.message.Message' not in el)
				#print 'Current a: '
				#pp.pprint(a)
				###
				#if part.is_multipart():
					#print '========='
					#for p in part.walk():
						#if 'application/pdf' not in p:
							#print p.get_payload()
					#print '========='
				#else:
					#print part
				###
			else:
				pass
				#print 'PDF!attachment or HTML. Need only plain text payload. Will skip!'
	else:
		a = a + str(decode(mo.get_payload().strip())) + '\n'

	return remove_html(a)

#	bodi = ''
	# get body of email
#	if mo.is_multipart():
#		for payload in mo.get_payload():
#			ctype = payload.get_content_type()
#			if ctype == 'text/plain':
#				bodi = bodi + payload.get_payload() + '\n'
#			else:
#				print "PDF!: Will not skip PDF"
#	else:
#		bodi = bodi + mo.get_payload() + '\n'
#	return bodi


def get_attachment(mo):
	a = ''
	if mo.is_multipart():
		for part in mo.walk():
			ctype = part.get_content_type()
			if ctype in ['text/plain','text/html']:
				a = part.get_payload(decode=True)
				
	return a

###-
def parsepop(f,m_ids):
	actions = []
	emaildata = {}
	read_or_starred = []

	fpath, fname = os.path.split(f)

	try:
		# load email object
		bod = None
		mailobj = None
		
		fstr = ''
		with open(f,'rb') as fh:
			fstr = ''.join(fh.readlines())

		# confirm that file contains attachment of interest
		if 'content-disposition: attachment' not in fstr.lower() and '.txt' not in fstr.lower():
			er = 'invalid: No attachment of interest in file!'
			actions = [er]
		else:
			# load email object
			mailobj = email.message_from_string(fstr)

		if not mailobj:
			er = "invalid: error! loading email object from file! {}".format(f)
			actions = [er]
		else:	
			bod = get_attachment(mailobj)
			#print bod

			cln_bod = bod # was = paranoid_clean_email(bod)
			
			sigemails = None
			lins = cln_bod.splitlines()
			try:
				# extract signalling info and inner email objects
				sigemails = parse_signals_and_emails(lins)
			except Exception, e:
				print "ERROR! could not parse signals and emails", str(e)
				#pp.pprint(lins)

			if sigemails:
				for emid,dat in sigemails.items():
					emo = dat['email']
					innerbody = ''
					innersubject = ''
					isparsed = 0
					try:
						emoemo = email.message_from_string(emo)
						innerbody = get_body(emoemo)
						innersubject = emoemo['subject']
						isparsed = 1
						#print 'EMOEMO! ', innerbody
					except Exception, e:
						print 'error! ', 'could not parse email body from email. subject: {}'.format(dat['subject'])
						innerbody = emo

					#txt = ''
					#if not isparsed:
						# earlier parsing failed
					txt = innerbody

					# if the subject line is empty, fill it using a snippet of the body
					if not innersubject.strip():
						innersubject = 'BODYSNIP - ' + str(txt)[:30]

					#print 'FLAG: ', dat['flag']
					#print 'SUBJECT: ', innersubject
					#print 'TXT: '
					#pp.pprint(txt)
					
					#import sys
					#sys.exit(1)

					if fname not in emaildata:
						emaildata[fname] = {}
					emaildata[fname][emid] = {}
					emaildata[fname][emid]['subject'] = innersubject
					emaildata[fname][emid]['body'] = txt
					emaildata[fname][emid]['flag'] = dat['flag']
										

					if '__ISSENT__' in dat['flag'] and ('__ISDRAFT__' in emo or '__ISSTARRED__' in emo or '__ISSENT__' in emo):
						actions = ['race_condition']
					elif '__ISALIVE__' in dat['flag']:
						actions = ['heartbeat']
					elif '__ISREAD__' in dat['flag']:
						actions.append('__ISREAD__')
						cdet = ('__ISREAD__',innersubject)  
						read_or_starred.append((cdet,txt))
					elif '__ISDRAFT__' in dat['flag']:
						actions.append('__ISDRAFT__')
						cdet = ('__ISDRAFT__',innersubject)
						m_ids.add(emid)
					elif '__ISSTARRED__' in dat['flag']:
						actions.append('__ISSTARRED__')
						#cdet = ('__ISSTARRED__',innersubject)
						#details.append(cdet)
					elif '__ISSENT__' in dat['flag'] and ('__ISDRAFT__' not in emo or '__ISSTARRED__' not in emo or '__ISSENT__' not in emo):
						actions.append('__ISSENT__')
						cdet = ('__ISSENT__',innersubject)
						#details.append(cdet)
												 
			else:
				# new parsing style failed. find flags the old way
				regx = re.compile(r"__\D{6,9}__",re.IGNORECASE) 
				matc = re.findall(regx,cln_bod)
				if matc:
					if "__ISALIVE__" in matc:
						actions = ["heartbeat"]
					if '__ISSENT__' in matc and ('__ISDRAFT__' in matc or '__ISSTARRED__' in matc or '__ISSENT__' in matc):
						actions = ['race_condition']
 		#pp.pprint(sigemails)
	except Exception, e:
		print "modulerror!",e
	
	if not actions:
		er = "invalid: nondescript error! while parsing POP"
		actions = [er]
	s = tuple(set(actions))
	return [s,read_or_starred,emaildata,m_ids]
