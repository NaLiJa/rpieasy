#!/usr/bin/env python3
#############################################################################
######################### GPIO helper for RPIEasy ###########################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import rpieGlobals
import rpieTime
import time
import Settings
import misc
import gpios
import commands
import lib.lib_rtttl as rtttllib
import threading

commandlist = ["gpio","pwm","pulse","longpulse","tone","rtttl","status","servo"]

def syncvalue(bcmpin,value):
 for x in range(0,len(Settings.Tasks)):
  if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
   if (Settings.Tasks[x].enabled):
     if (Settings.Tasks[x].pluginid==29) and (Settings.Tasks[x].taskdevicepin[0]==bcmpin): # output on specific pin
      try:
       if Settings.Tasks[x].pininversed:
        Settings.Tasks[x].uservar[0] = (1-value)
       else:
        Settings.Tasks[x].uservar[0] = value
      except:
       pass
      if Settings.Tasks[x].valuenames[0]!= "":
       commands.rulesProcessing(Settings.Tasks[x].taskname+"#"+Settings.Tasks[x].valuenames[0]+"="+str(value),rpieGlobals.RULE_USER)
      Settings.Tasks[x].plugin_senddata()
      break

def syncpwm(bcmpin,value):
 for x in range(0,len(Settings.Tasks)):
  if (Settings.Tasks[x]) and type(Settings.Tasks[x]) is not bool: # device exists
   if (Settings.Tasks[x].enabled):
     if (Settings.Tasks[x].pluginid==213) and (Settings.Tasks[x].taskdevicepin[0]==bcmpin): # pwm on specific pin
      try:
       Settings.Tasks[x].uservar[0] = value
      except:
       pass
      if Settings.Tasks[x].valuenames[0]!= "":
       commands.rulesProcessing(Settings.Tasks[x].taskname+"#"+Settings.Tasks[x].valuenames[0]+"="+str(value),rpieGlobals.RULE_USER)
      Settings.Tasks[x].plugin_senddata()
      break

def timercb(stimerid,ioarray):
  if ioarray[0] > -1:
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BCM"+str(ioarray[0])+": LongPulse ended")
    try:
     gpios.HWPorts.output(ioarray[0],ioarray[1])
     syncvalue(ioarray[0],ioarray[1])
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(ioarray[0])+": "+str(e))

def gpio_commands(cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0] == "gpio":
   pin = -1
   val = -1
   gi = -1
   logline = ""
   try:
    pin = int(cmdarr[1].strip())
    val = int(cmdarr[2].strip())
   except:
    pin = -1
   if pin>-1 and val in [0,1]:
    logline = "BCM"+str(pin)+" set to "+str(val)
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,logline)
    suc = False
    try:
     suc = True
     gpios.HWPorts.output(pin,val)
     syncvalue(pin,val)
     gi = gpios.GPIO_refresh_status(pin,pstate=val,pluginid=1,pmode="output",logtext=logline)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(pin)+": "+str(e))
     suc = False
#    if suc == False:
#     try:
#      gpios.HWPorts.output(pin,val,True) # force output?
#     except Exception as e:
#      print("output failed ",pin,val,e)
#     suc = False
   if gi>-1:
     return gpios.GPIO_get_status(gi)
   res = True
  elif cmdarr[0]=="pwm":
   pin = -1
   prop = -1
   gi = -1
   logline = ""
   try:
    pin = int(cmdarr[1].strip())
    prop = int(float(cmdarr[2].strip()))
   except:
    pin = -1
    prop = -1
   fade = 0
   try:
    fade = int(float(cmdarr[3].strip()))
   except:
    fade = 0
   freq = 1000
   try:
    freq = int(float(cmdarr[4].strip()))
   except:
    freq = 1000
   if pin>-1 and prop>-1:
    suc = False
    try:
     suc = True
     if fade==0:
      gpios.HWPorts.output_pwm(pin,prop,freq)
      logline = "BCM"+str(pin)+" PWM "+str(prop)+"% "+str(freq)+"Hz"
      misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,logline)
     else:
      cs = gpios.GPIO_get_statusid(pin)
      prev_value = 0
      try:
       if cs>-1:
        if gpios.GPIOStatus[cs]["mode"] == "pwm":
         prev_value = int(gpios.GPIOStatus[cs]["state"])
      except:
       prev_value = 0
      step_value = (int(prop - prev_value) << 12) / fade
      curr_value = int(prev_value) << 12
      i = fade
      while i>0:
       curr_value += step_value
       new_value = int(curr_value) >> 12
       gpios.HWPorts.output_pwm(pin,new_value,freq)
       time.sleep(0.001) # 1 millisecond in theory, more in reality..
       i -= 1
      gpios.HWPorts.output_pwm(pin,prop,freq)
     gi = gpios.GPIO_refresh_status(pin,pstate=prop,pluginid=1,pmode="pwm",logtext=logline)
     syncpwm(pin,prop)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(pin)+" PWM "+str(e))
     suc = False
   if gi>-1:
     return gpios.GPIO_get_status(gi)
   res = True
  elif cmdarr[0]=="pulse":
   pin = -1
   val = -1
   gi = -1
   logline = ""
   try:
    pin = int(cmdarr[1].strip())
    val = int(float(cmdarr[2].strip()))
   except:
    pin = -1
   dur = 100
   try:
    dur = float(cmdarr[3].strip())
   except:
    dur = 100
   if pin>-1 and val in [0,1]:
    logline = "BCM"+str(pin)+": Pulse started"
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,logline)
    try:
     syncvalue(pin,val)
     gpios.HWPorts.output(pin,val)
     s = (dur/1000)
     time.sleep(s)
     gpios.HWPorts.output(pin,(1-val))
     syncvalue(pin,(1-val))
     gi = gpios.GPIO_refresh_status(pin,pstate=(1-val),pluginid=1,pmode="output",logtext=logline)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(pin)+": "+str(e))
     suc = False
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"BCM"+str(pin)+": Pulse ended")
   if gi>-1:
     return gpios.GPIO_get_status(gi)
   res = True
  elif cmdarr[0]=="longpulse":
   pin = -1
   val = -1
   gi = -1
   logline = ""
   try:
    pin = int(cmdarr[1].strip())
    val = int(float(cmdarr[2].strip()))
   except:
    pin = -1
   dur = 2
   try:
    dur = float(float(cmdarr[3].strip()))
   except:
    dur = 2
   if pin>-1 and val in [0,1]:
    logline ="BCM"+str(pin)+": LongPulse started"
    misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,logline)
    try:
     gpios.HWPorts.output(pin,val)
     syncvalue(pin,val)
     gi = gpios.GPIO_refresh_status(pin,pstate=val,pluginid=1,pmode="output",logtext=logline)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(pin)+": "+str(e))
     suc = False
    rarr = [pin,(1-val)]
    rpieTime.addsystemtimer(dur,timercb,rarr)
   if gi>-1:
     return gpios.GPIO_get_status(gi)
   res = True
  elif cmdarr[0]=="tone":
   pin  = -1
   freq = -1
   dur  = 0
   gi = -1
   logline = ""
   try:
    pin  = int(cmdarr[1].strip())
    freq = int(cmdarr[2].strip())
    dur  = int(cmdarr[3].strip())
   except:
    pin = -1
    freq = -1
    dur = 0
   if pin>-1 and freq>-1 and dur>0:
    suc = False
    try:
     suc = True
     logline = "BCM"+str(pin)+" "+str(freq)+"Hz"
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,logline)
     play_tone(pin,freq,dur)
     gpios.HWPorts.output_pwm(pin,0,0) # stop sound
     gi = gpios.GPIO_refresh_status(pin,pstate=0,pluginid=1,pmode="pwm",logtext=logline)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(pin)+" Tone "+str(e))
     suc = False
   if gi>-1:
     return gpios.GPIO_get_status(gi)
   res = True

  elif cmdarr[0]=="rtttl":
   cmdarr = cmd.replace(":",",").split(",")
   pin  = -1
   gi = -1
   logline = ""
   try:
    pin  = int(cmdarr[1].strip())
   except:
    pin = -1
   if pin>-1:
    suc = False
    try:
     sp = cmd.find(":")
     if sp > -1:
#      play_rtttl(pin,"t"+cmd[sp:])
      rtproc = threading.Thread(target=play_rtttl, args=(pin,"t"+cmd[sp:])) # play in background - no blocking
      rtproc.daemon = True
      rtproc.start()
     suc = True
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
     suc = False
   res = True

  elif cmdarr[0]=="servo":
   snr  = -1
   pin  = -1
   pos = -1
   gi = -1
   logline = ""
   try:
    snr = int(cmdarr[1].strip())
    pin = int(cmdarr[2].strip())
    pos = int(float(cmdarr[3].strip()))
   except:
    snr = -1
    pin = -1
    pos = 0
   if snr>-1 and pin>-1 and pos>0:
    suc = False
    try:
     suc = True
     logline = "BCM"+str(pin)+" to servo "+str(pos)+" angle"
     misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,logline)
     setservoangle(pin,pos)
     gi = gpios.GPIO_refresh_status(pin,pstate=0,pluginid=1,pmode="servo",logtext=logline)
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BCM"+str(pin)+" Servo "+str(e))
     suc = False
   if gi>-1:
     return gpios.GPIO_get_status(gi)
   res = True

  elif cmdarr[0] == "status":
   pin = -1
   subcmd = ""
   try:
    subcmd = str(cmdarr[1].strip()).lower()
    pin = int(cmdarr[2].strip())
   except:
    pin = -1
    print(e)
   if pin>-1 and subcmd=="gpio":
    gi = gpios.GPIO_refresh_status(pin)
    if gi>-1:
     return gpios.GPIO_get_status(gi)
   res = True

  return res

def setservoangle(servopin,angle):
    if angle>= 0 and angle<= 180:
     try:
      gpios.HWPorts.servo_pwm(servopin,angle)
     except:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Servo command is not supported on this hardware!")

def play_tone(pin,freq,delay):
  gpios.HWPorts.output_pwm(pin,50,freq) # generate 'freq' sound
  try:
   s = float(delay/1000)
  except:
   s = 0.5
  time.sleep(s)

def play_rtttl(pin,notestr):
# print("DEBUG ",notestr)
 notes = []
 try:
  notes = rtttllib.parse_rtttl(notestr)
 except Exception as e:
  misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"RTTTL parse failed: "+str(e))
  return False
 if 'notes' in notes:
  for note in notes['notes']:
   try:
    play_tone(pin,int(note['frequency']),float(note['duration']))
   except:
    pass
  gpios.HWPorts.output_pwm(pin,0,0) # stop sound
