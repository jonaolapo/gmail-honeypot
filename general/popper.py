"""POP Mail client
Author: Jeremiah Onaolapo 2016

It retrieves notifications from the notification store (sent by honey accounts). Specify the username and password of the notification store account below. 

"""
import poplib
from email import parser
import smtpd
import time
import random

################# CONFIG ############################
POPSPATH = "path/to/POP"
ERRLOGSPATH = "errors"
POPSERVER = 'pop.gmail.com'
PORT = 995
USERNAME = 'notification-store@someservice.com'
PWORD = 'password-here'
SLEEPTIME = 3600 # that is, 1 hour
#####################################################

while True:
	try:
		pop_conn = poplib.POP3_SSL(POPSERVER, PORT)
		pop_conn.user(USERNAME)
		pop_conn.pass_(PWORD)
		print "Login successful...Please wait..."
		# Get messages from server:
		messages = [pop_conn.retr(i) for i in range(1, len(pop_conn.list()[1]) + 1)]
		# Concat message pieces:
		messages = ["\n".join(mssg[1]) for mssg in messages]
		#Parse message into an email object:
		messages = [parser.Parser().parsestr(mssg) for mssg in messages]
		for message in messages:
			print message['subject']
			# Convert message object to string and write to disk
			data = message.as_string()
			nownow = time.time()
			src = str(message['From'])
			rnnd = random.randint(1111,99999999)
			fname = "{}/{}_src_{}_rnd_{}".format(POPSPATH, nownow, src, rnnd)
			fname = fname.replace(" ", "")
			with open(fname, "w") as fo:
				print >> fo, data
		pop_conn.quit()
		# print 'Sleep...'
	except Exception, error:
		now = time.asctime(time.gmtime())
		error = "{}. Error {}: {}".format(now, USERNAME, str(error))
		with open("{}/POPERRORS".format(ERRLOGSPATH), "ab") as fo:
			fo.write(error)
		print error
		print

	time.sleep(SLEEPTIME)
