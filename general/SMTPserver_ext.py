"""Sinkhole mail server.
Author: Jeremiah Onaolapo 2016

It receives emails and writes them to disk 
without forwarding the emails to the intended destination.

Please specify your mail server's IP address in the MAILSERV_IP string
"""

import smtpd
import asyncore
import time
import random
import re

MAILSERV_IP = "server_IP_address_here"
DUMPATH = "dump"

class CustomSMTPServer(smtpd.SMTPServer):

	def process_message(self, peer, mailfrom, rcpttos, data):
		print 'Receiving message from:', peer
		print 'Message addressed from:', mailfrom
		print 'Message addressed to  :', rcpttos
		print 'Message length 	 :', len(data)
		print 'Data:', data
		print
		print
		
		BEGINRAW = "\n#####BEGIN RAW#####\n"
		ENDRAW = "\n#####END RAW#####\n"
		msg = "Source address - {0}\nReal fromaddr - {1}\nReceipients - {2}\nRaw email - {4}{3}{5}".format(str(peer), str(mailfrom), str(rcpttos), str(data), BEGINRAW, ENDRAW)

		# Reshape src and dst addresses
                if not isinstance(mailfrom, basestring):
                     	mailfrom = mailfrom[0]
		ptrn = re.compile("<([^>]+)>")
		mailfrom = ''.join(ptrn.findall(mailfrom))

                if not isinstance(rcpttos, basestring):
                        rcpttos = rcpttos[0]

		fo = "{}/{}_dst_{}_src_{}_{}.mail".format(DUMPATH, time.time(), rcpttos, mailfrom, random.randint(1111, 99999999))

		# Dump email to file
		with open(fo, "w") as fo:
			print >> fo, msg


smtpserver = CustomSMTPServer((MAILSERV_IP, 25), None)
print 'SMTP Server is up :)'

try:
	asyncore.loop()
except Exception, e:
	print str(e)
	#smtpserver.close()


