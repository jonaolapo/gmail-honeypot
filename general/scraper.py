"""Honey activity scraper
Author: Jeremiah Onaolapo 2016

Connects to honey accounts to download pages that contain information about accesses. To run this scraper in headless mode, use run_scraper.sh (in the same directory as this file).
"""

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
import codecs
import time
import csv
import random
import os

####### CONFIG SETTINGS #########
gmailURL = "https://accounts.google.com/ServiceLogin?service=mail"
activityURL = "https://security.google.com/settings/security/activity?pli=1"

HERE = os.getcwd()

AUTHCREDS = "name-of-text-file-containing-list-of-honey-usernames-and-passwords"
SCRAPEDUMPS = "folder-to-store-the-downloaded-files"
ERRORLOGSFILE = "errors.txt"

SLEEPTIME = 3600 # Equals 1 hour
#################################


###=
def scrape( emailAddr, passwd ):

	# Create a new instance of the Firefox driver
	driver = webdriver.Firefox()
	try:
		# go to Gmail login
		driver.get(gmailURL)
		# Wait for Gmail login page to finish loading
		time.sleep(10)
		# find the element whose id attribute is Email
		emailInput = driver.find_element_by_id("Email")
		# type email address and press Enter key
		emailInput.send_keys(emailAddr + Keys.RETURN)
		# wait a bit for password field to slide in
		time.sleep(7)
		passwdInput = driver.find_element_by_id("Passwd")

		# Uncheck 'Stay signed in' checkbox if checked
		#checkBox = driver.find_element_by_id("PersistentCookie")
		#if (checkBox.is_selected()):
			#checkBox.click()

		# type password and press Enter key
		passwdInput.send_keys(passwd + Keys.RETURN)

		# Wait for page to load
		driver.implicitly_wait(15)

		print driver.current_url

		# Wait a bit longer before visiting page containing details of accesses
		driver.implicitly_wait(5)

		# Visit page
		driver.get(activityURL)
		driver.implicitly_wait(5)
		print driver.current_url
		
		# Visit page
		driver.get(activityURL)
		driver.implicitly_wait(5)

		print driver.current_url

		# Scrape and dump page to disk (HTML and JS content)
		html = driver.page_source
		fname = "{}/{}_{}_{}.html".format(SCRAPEDUMPS,emailAddr,time.time(),random.randint(1111, 9999))
		with codecs.open(fname, 'w', 'utf8') as fh:
			fh.write(html)	
			
    	except Exception, e:
    		now = time.asctime(time.gmtime())
        	errmsg = "{} {}".format(now,str(e))
        	print errmsg
        	with open(ERRORLOGSFILE, "ab") as logfl:
        		logfl.write(errmsg)

	finally:
		driver.quit()
		

###= START =###
# Read credentials into list of tuples
authlist = []
fl = open(AUTHCREDS,'rt')
try:
	readr = csv.reader(fl)
	for row in readr:
		print row
		if row:
			uname = row[1]
			pword = row[2]
			authlist.append((uname,pword))
finally:
	fl.close()

while True:
	for cred in authlist:
		try:
			print "Ready to scrape {}...".format(cred[0])
			scrape(cred[0], cred[1])
			print "Done scraping {}...".format(cred[0])
		except Exception, e:
			now = time.asctime(time.gmtime())
			errmsg = "{} {}".format(now,str(e))
			print errmsg
			with open(ERRORLOGSFILE, "ab") as logfl:
				logfl.write(errmsg)
	
	time.sleep(SLEEPTIME)
