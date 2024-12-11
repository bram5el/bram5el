#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, os, argparse, sys, signal
from threading import Timer

parser = argparse.ArgumentParser(description="")
parser.add_argument('-c', '--current', action="store_true", help='Print out current status')
parser.add_argument('-u', '--update', action="store_true")
parser.add_argument('-s', '--service', type=int)
parser.add_argument('-p', '--printout', action="store_true", default="-p")
parser.add_argument('-d', '--debug', action="store_true")
args = parser.parse_args()

STATUS = "/etc/openvpn/server/openvpn.status"
STATUS_DATA = "/var/local/openvpn.data"

DEBUG = False

headers = {
    'cn':    'Common Name',
    'virt':  'Virtual Address',
    'real':  'Real Address',
    'sent':  'Sent',
    'recv':  'Received',
    'since': 'Connected Since',
    'lref': 'Last Ref'
}

sizes = [
    (1<<50L, 'PB'),
    (1<<40L, 'TB'),
    (1<<30L, 'GB'),
    (1<<20L, 'MB'),
    (1<<10L, 'KB'),
    (1,       'B')
]

scrypt_ver_num = '2.4.7'

def byte2str(size):
    for f, suf in sizes:
        if size >= f:
            break
    return "%.2f %s" % (size / float(f), suf)

def printOut(array):
    if len(array) > 0:
      fmt = "%(cn)-25s %(virt)-18s %(real)-13s %(sent)15s %(recv)15s %(since)25s %(lref)25s"
      for a in array:
       a['recv'] = byte2str(a['recvCurr_int'] + a['recvSum_int'])
       a['sent'] = byte2str(a['sentCurr_int'] + a['sentSum_int'])
      print fmt % headers
      print "-"*145
      print "\n".join([fmt % h for h in array])
    else:
      print("  No data for output or no active connections")

def checkVersionNum():
    if (os.path.exists(STATUS)):
      with open(STATUS, 'r') as status_file:
        stats = status_file.readlines()
    else:
      print " Error: Status File \"" + STATUS + "\" not found. Check the path or file access rights."
      sys.exit()

    cols = stats[0].split(',')

    if cols[0] == ('TITLE'):
        num = cols[1].split()[1]
        if num != scrypt_ver_num:
          print "  WARNING: Version of the script " + scrypt_ver_num + " and OpenVPN version " + num + " is defferent"
        return num
    else:
        return -1
            
def statusParser():
    if (os.path.exists(STATUS)):
      with open(STATUS, 'r') as status_file:
        stats = status_file.readlines()
    else:
      print " Error: Status File \"" + STATUS + "\" not found. Check the path or file access rights."
      sys.exit()

    hosts = []
    for line in stats:
        cols = line.split(',')
        if cols[0] == 'CLIENT_LIST':
            host = {}
            host['cn'] = cols[1]
            host['real'] = cols[2].split(':')[0]
            host['virt'] = cols[3]
            host['recvCurr_int'] = int(cols[5])
            host['sentCurr_int'] = int(cols[6])
            host['recvSum_int'] = 0
            host['sentSum_int'] = 0
            host['since'] = cols[7].strip()
            host['state'] = True
            hosts.append(host)

        if cols[0] == 'ROUTING_TABLE':
            for h in hosts:
              if h['cn'] == cols[2]:
                h['lref'] = cols[4]
    return hosts

def dataUpdate(hosts, data):
    for h in hosts:
      newClient = True
      for d in data:
        if d['virt'] == h['virt']:  
          newClient = False
          d['real'] = h['real']
          d['lref'] = h['lref']
          d['since'] = h['since']
          if bool(d['state']):            
              d['recvCurr_int'] = int(h['recvCurr_int'])
              d['sentCurr_int'] = int(h['sentCurr_int'])
          else:
              d['recvSum_int'] = int(d['recvSum_int'] + d['recvCurr_int'])
              d['sentSum_int'] = int(d['sentSum_int'] + d['sentCurr_int'])
              d['recvCurr_int'] = int(h['recvCurr_int'])
              d['sentCurr_int'] = int(h['sentCurr_int'])
              debugOut("Client: " + d['cn'] + " is connected again!")
          break
      if newClient:
        debugOut("New Client added " + h['cn'])
         data.append(h)
    
    for d in data:
      state = d['state']
      d['state'] = False
      for h in hosts:
        if d['virt'] == h['virt']:
          d['state'] = True
          break
      if not bool(d['state']) and state != bool(d['state']):
        d['since'] = ''
        debugOut("Client: " + d['cn'] + " is disconnected")
        
    with open(STATUS_DATA, 'w') as data_file:
        json.dump(data, data_file)
        if len(hosts) > 0: 
          debugOut("Updated: \n" + "; \n".join(['%(cn)-25s %(lref)s' % h for h in hosts]))
        else:
          debugOut("No data for save or update")

def updateTask():
  try:
    h=statusParser()

    if (os.path.exists(STATUS_DATA)):
        with open(STATUS_DATA, 'r') as data_file:
          data = json.load(data_file)
        dataUpdate(h, data)
    else: 
        with open(STATUS_DATA, 'w') as data_file:
          json.dump(h, data_file)
          debugOut('Status data file created')
 
  except KeyboardInterrupt:
    print("Ctrl-C pressed!")
    shutdown()

def repeater(interval, function):
    Timer(interval, repeater, [interval, function]).start()
    function()
    
def shutdown(sig, frame):
  print("Server shutting down...")
  sys.exit()

def debugOut(message):
  if DEBUG:
    print(message)

ver_num = checkVersionNum()
if ver_num == -1:
    print "  Error: Invalid status file format"
    sys.exit()

DEBUG = bool(args.debug)

if args.current:
    printOut(statusParser())
elif args.update:
    updateTask()
elif args.service:
    upd_time = args.service
    if (upd_time > 0):
      print "  Updating status interval "+ str(upd_time) + "sec. Data file: "+ STATUS_DATA 
      repeater(upd_time, updateTask)
    else:
        print "  Update time wrong or less zero"
elif args.printout:
    if (os.path.exists(STATUS_DATA)):
      with open(STATUS_DATA, 'r') as data_file:
        data = json.load(data_file)
        printOut(data)
    else:
      print " Error: Status Data File \"" + STATUS_DATA + "\" not found. Call the program with the -u argument to create it."
else:
    print("  Type --help/-h for usage help")