import time
import datetime

def to_int(v):
  return int(float(v))

def is_valid_time(tstamp,metadata):
  is_prior = 0
  is_valid = 0

  startdate = metadata['EXPERIMENT_START_DATE']
  enddate = metadata['EXPERIMENT_END_DATE']
  st = time.mktime(datetime.datetime.strptime(startdate, "%d/%m/%Y").timetuple())
  et = time.mktime(datetime.datetime.strptime(enddate, "%d/%m/%Y").timetuple())

  if to_int(tstamp) >= to_int(st) and to_int(tstamp) <= to_int(et):
    is_valid = 1 # that is, true
  if to_int(tstamp) < to_int(st):
    is_prior = 1 # access showed up before experiment started

  return (is_valid,is_prior)
