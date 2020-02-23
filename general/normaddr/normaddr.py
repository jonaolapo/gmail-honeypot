# -*- coding: utf-8 -*-

def normaddr(em):
  # remove dots from username part of email addr
  # and convert whole email address to lowercase
  emadr = em.lower()
  l = emadr.split('@')
  if len(l) == 2:
    uname = l[0].replace('.','')
    serv = l[1]
    emadr = uname + '@' + serv

  return emadr
