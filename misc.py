#!/usr/bin/env python3
#############################################################################
################### Miscellenous function for RPIEasy #######################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import platform
import rpieGlobals
from datetime import datetime
import Settings
import socket

supportedsys = ['Not supported', 'Linux-apt (partially supported)', 'Linux-pacman (experimental support)','OPI-Linux-armbian (experimental)','Linux-apk (experimental support)','-Reserved','-Reserved','-Reserved','-Reserved','RockPI-Linux-apt (supported)','RPI-Linux-apt (supported)']

SystemLog = []
ShadowLog = []
shadowlogenabled = False

def getosname(lvl=0):
 if lvl==0:
  return platform.system().lower()
 elif lvl==1:
  return platform.release().lower()
 elif lvl==2:
  try:
   return platform.linux_distribution()[0].lower()
  except:
   return ""

def getsupportlevel(of=0):
 global supportedsys
 if getosname(0)=="linux":
  import linux_os
 lvl = 0
 if rpieGlobals.osinuse=="linux":
  if (linux_os.is_command_found('dpkg')) and (linux_os.is_command_found('apt')):
   lvl = 1
   if linux_os.checkRPI():
    lvl = 10
   elif linux_os.checkRockPI():
    lvl = 9
   elif linux_os.checkOPI():
    lvl = 3
  elif (linux_os.is_command_found('pacman')):
   lvl = 2
  elif (linux_os.is_command_found('apk')):
   lvl = 4
 if of == 0:
  return supportedsys[lvl]
 else:
  return lvl

def WebLog(lvl,logstamp, line):
 global SystemLog
 if len(SystemLog)>rpieGlobals.LOG_MAXLINES:
  tvar = []
  for i in range(0,10):
   SystemLog[i]=SystemLog[rpieGlobals.LOG_MAXLINES-10+i]
  SystemLog = tvar
 SystemLog.append({"t":logstamp,"l":line,"lvl":lvl})

def addLog(logLevel, line):
 global ShadowLog
 lstamp = datetime.now().strftime('%H:%M:%S')
 if int(logLevel)<=int(Settings.AdvSettings["webloglevel"]): # if weblogging enabled
    WebLog(logLevel,lstamp,line)
 if int(logLevel)<=int(Settings.AdvSettings["sysloglevel"]): # if syslogging enabled
    lstamp2 = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    SysLog(logLevel,lstamp2,line)
 if int(logLevel)<=int(Settings.AdvSettings["consoleloglevel"]): # if console logging enabled
    if logLevel==rpieGlobals.LOG_LEVEL_ERROR:
     lstamp += ": !"
    else:
     lstamp += ": "
    print(lstamp+line)
 if shadowlogenabled:
    if len(ShadowLog)>1000:
     ShadowLog = []
    ShadowLog.append({"t":lstamp,"l":line,"lvl":logLevel})

def udpsender(destip,data,dport=514,retrynum=1):
  if destip != "":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if type(data) is bytes:
     dsend = data
    elif type(data) is str:
     dsend = bytes(data,"utf-8")
    else:
     dsend = bytes(data)
    for r in range(retrynum):
     try:
      s.sendto(dsend, (destip,int(dport)))
      if r<retrynum-1:
       time.sleep(0.1)
     except:
      print("UDP send failed with network error.")

def SysLog(lvl,logstamp,line):
   slip = ""
   try:
    slip = Settings.AdvSettings["syslogip"]
   except:
    slip = ""
   if slip != "":
    facility = 0
    prio = (facility*8)
    if (lvl == rpieGlobals.LOG_LEVEL_ERROR):
     prio += 3
    elif (lvl == rpieGlobals.LOG_LEVEL_INFO):
     prio += 5
    else:
     prio += 7
    lstr = "<"+str(prio)+">RPIEasy "+str(Settings.Settings["Name"])+": "+str(line)
    udpsender(slip,lstr)
   else:
    print("Syslog IP is empty!")

def str2num(data):
 try:
  data + ''
  return float(data.replace(',','.'))
 except TypeError:
  return data

def str2num2(data):
 try:
  return round(str2num(data),2)
 except:
  return data

def formatnum(num,decimal):
 res = ""
 try:
  decimal = int(decimal)
 except:
  decimal=0
 try:
  num=float(num)
 except:
  pass
 if decimal<0:
  res = str(num)
 else:
  nformat = "{0:."+str(decimal)+"f}"
  try:
   res = nformat.format(num)
  except:
   res = num
 return res

def get_battery_value():
 bval = 255
 try:
  if Settings.AdvSettings["battery"]["enabled"]:
   bval = float(Settings.Tasks[int(Settings.AdvSettings["battery"]["tasknum"])].uservar[int(Settings.AdvSettings["battery"]["taskvaluenum"])])
  else:
   bval = 255
 except: 
  bval = 255
 if bval!=255:
  if bval<0:
   bval = 0
  elif bval>100:
   bval = 100
 return bval

def get_taskname_taskids(taskname):
  res = []
  for i in range(len(Settings.Tasks)):
   try:
    if type(Settings.Tasks[i]) is not bool:
     if Settings.Tasks[i].taskname.lower() == taskname:
      if i not in res:
       res.append(i)
   except:
    pass
  return res

def timecorrect(timestr):
    tstr = str(timestr)
    try:
     if ':' in tstr:
      tarr = tstr.split(":")
     elif '-' in tstr:
      tarr = tstr.split("-")
     elif '.' in tstr:
      tarr = tstr.split(".")
     elif '/' in tstr:
      tarr = tstr.split("/")
     tstr = '{:02}'.format(int(tarr[0]))  + ":{:02}".format(int(tarr[1]))
    except Exception as e:
     pass
    return tstr

def getfirstfreetask():
  ft = len(Settings.Tasks)
  for i in range(len(Settings.Tasks)):
   try:
    if Settings.Tasks[i] == False:
     return i
   except:
    pass
  return ft
