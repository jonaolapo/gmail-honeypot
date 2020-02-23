import time
import sys

def honeylogger(error_,message):
  LOGFILE = '_logs/' + str(sys.argv[0]).replace('.py','__.log')
  nownow = time.ctime(time.time())
  logentry = ''
  if error_ == '':
    logentry = "{} | {}\n".format(nownow,message)
  else:
    logentry = "{} | error: {} | {}\n".format(nownow,error_,message)
  print logentry.strip()

  if message.lower().startswith('starting...'):
    with open(LOGFILE, 'w') as fh:
      pass

  with open(LOGFILE, 'ab') as fh:
    fh.write(logentry)
