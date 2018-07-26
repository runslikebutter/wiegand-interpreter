#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################
#   Written by Brad Shannon for ButterflyMX
#   project begun 4-2018
#
#   OBJECTIVE:
#       Create a means of observing the outputs of the Faytech All-In-One card
#       reader over two interfaces:
#           1)  USB (as HID keyboard)
#           2)  Wiegand Output terminals (D0 & D1)
#
################################################

import os, sys

# add ../../Sources to the PYTHONPATH
cwd = os.getcwd()
#print("{}".format(cwd))
sys.path.append(os.path.join("{}/YoctoLib/Sources/".format(cwd)))

vars_before = set(dir())

import json

def getpwvhub():
    #   get the pw from the user so we don't have to store it in this Failed
    global pwvhub_in
    pwvhub_in = input("Enter password for VirtualHub local HTTP interface:    ")

def clearscr():
    os.system('cls' if os.name=='nt' else 'clear')

def moduletest(*mods):
   print("****************************************************")
   for mod in mods:
        modulename = mod
        if modulename in vars_after:
            print("*    Successfully loaded module:  {}".format(modulename))
            print("****************************************************")
        else:
            print('*    ERROR:   Failed to load module:  {}'.format(modulename))
            print("****************************************************")

getpwvhub()
vhub_addr = "http://admin:{0}@127.0.0.1:4444".format(pwvhub_in)
#print("vhub_addr =   {}".format(vhub_addr))

#import yocto_api
from yocto_api import *
#import yocto_serialport
from yocto_serialport import *

vars_after = set(dir()) - vars_before - {'vars_before'}

clearscr()

moduletest("json","yocto_api","yocto_serialport")

# Setup the API to use local USB devices. You can
# use an IP address instead of 'usb' if the device
# is connected to a network.

errmsg = YRefParam()
if YAPI.RegisterHub(vhub_addr, errmsg) != YAPI.SUCCESS:
    sys.exit("init error" + errmsg.value)

if len(sys.argv) > 1:
    serialPort = YSerialPort.FindSerialPort(sys.argv[1] + ".serialPort")
    if not serialPort.isOnline():
        sys.exit('Module not connected')
else:
    serialPort = YSerialPort.FirstSerialPort()
    if serialPort is None:
        sys.exit('No module connected (check cable)')

    serialPort.set_serialMode("Wiegand")
    serialPort.set_protocol("Wiegand-ASCII")
    serialPort.reset()
    modecheck = serialPort.get_serialMode()
    protcheck = serialPort.get_protocol()
    print("Mode = ", modecheck)
    print("Protocol = ", protcheck)
    print(" ")
    msg_check = serialPort.get_lastMsg()

#print("Waiting for input...")

while True:
    keyboard_in = input("Waiting for input:    ")
    msg_check_again = serialPort.get_lastMsg()
    YAPI.Sleep(1000)

    if msg_check_again != msg_check:
        #   raw binary string:
        rbstr = msg_check_again.replace(' ', '')
        #   inverted binary string:
        ibstr_a = rbstr.replace('0', 'z')
        ibstr_b = ibstr_a.replace('1', '0')
        ibstr = ibstr_b.replace('z', '1')
        #   length of raw binary string:
        rblen = len(rbstr)
        #   raw binary string translated to hex:
        rb_as_hstr = '%0*X' % ((len(rbstr) + 3) // 4, int(rbstr, 2))
        #   raw binary string translated as ascii:
        rb_as_text = ''.join(chr(int(rbstr[i:i+8], 2)) for i in range(0, rblen, 8))
        #   raw binary string translated as decimal number
        rb_as_int = int(rbstr, base=2)

        #   binary string with first and last bit truncated:
        btrunc = rbstr[1:rblen-1]
        btrunclen = len(btrunc)
        #   truncated binary string translated to hex:
        tb_as_hstr = '%0*X' % ((len(btrunc) + 3) // 4, int(btrunc, 2))
        #   truncated binary string translated as ascii:
        tb_as_text = ''.join(chr(int(btrunc[i:i+8], 2)) for i in range(0, len(btrunc), 8))
        #   truncated binary string translated as decimal number
        tb_as_int = int(btrunc, base=2)
        #   fac. code binary string translated to hex:
        fc_as_hstr = '%0*X' % ((len(btrunc[:8]) + 3) // 4, int(btrunc[:8], 2))
        #   unique ID binary string translated to ascii:
        ui = btrunc[8:]
        ui_as_text = ''.join(chr(int(ui[i:i+8], 2)) for i in range(0, len(ui), 8))
        #   fac.code binary string translated to decimal
        fc_as_int = int(btrunc[:8], base=2)
        #   unique ID binary string translated to decimal
        ui_as_int = int(ui, base=2)
        #   fac. code binary string translated to hex:
        ui_as_hstr = '%0*X' % ((len(ui) + 3) // 4, int(ui, 2))

        #   inv binary string with first and last bit truncated:
        iblen = len(ibstr)
        ibtrunc = ibstr[1:iblen-1]
        ibtrunclen = len(ibtrunc)
        #   inv truncated binary string translated to hex:
        itb_as_hstr = '%0*X' % ((len(ibtrunc) + 3) // 4, int(ibtrunc, 2))
        #   inv truncated binary string translated as ascii:
        itb_as_text = ''.join(chr(int(ibtrunc[i:i+8], 2)) for i in range(0, len(ibtrunc), 8))
        #   inv truncated binary string translated as decimal number
        itb_as_int = int(ibtrunc, base=2)
        #   inv fac. code binary string translated to hex:
        ifc_as_hstr = '%0*X' % ((len(ibtrunc[:8]) + 3) // 4, int(ibtrunc[:8], 2))
        #   inv unique ID binary string translated to ascii:
        iui = ibtrunc[8:]
        iui_as_text = ''.join(chr(int(iui[i:i+8], 2)) for i in range(0, len(iui), 8))
        #  inv fac.code binary string translated to decimal
        ifc_as_int = int(ibtrunc[:8], base=2)
        #   unique ID binary string translated to decimal
        iui_as_int = int(iui, base=2)
        #   fac. code binary string translated to hex:
        iui_as_hstr = '%0*X' % ((len(iui) + 3) // 4, int(iui, 2))

        #   result printout:
        print(" ")
        print("Received via reader as kb:    ", keyboard_in)
        print("Received via Wiegand Output:")
        print("    raw bit length:      ", rblen)
        print("    raw binary:          ", rbstr)
        print(" ")
        print("                         ", rbstr[0], " ", rbstr[1:9], " ", rbstr[9:25], " ", rbstr[25])
        print("                          P   AAAAAAAA   BBBBBBBBBBBBBBBB   P")
        print(" ")
#        print("    raw as hex:          ", rb_as_hstr)
#        print("    raw as decimal:      ", rb_as_int)
#        print("    raw as ascii:        ", rb_as_text)
#        print(" ")
        print("    truncated length:    ", btrunclen)
        print("    trunc'd binary:       ", btrunc)
        print(" ")
        print("    trunc'd as hex:      ", tb_as_hstr)
        print("    trunc'd as decimal:  ", tb_as_int)
        print("    trunc'd as ascii:    ", tb_as_text)
        print(" ")
        print("                          ", btrunc[:8], " ", btrunc[8:])
        print("                           | pt A |   |     pt B     |")
        print("                           --------   ----------------")
        print("                facility code ^^^           ^^^ unique card ID")
        print(" ")
        print("   facility code as hex: ", fc_as_hstr)
        print("    unique ID as hex:    ", ui_as_hstr)
        print(" ")
        print("*  facility code as dec: ", fc_as_int)
        print("*   unique ID as dec:    ", ui_as_int)
        print(" ")
        print("*  INVERTED fac.code as dec:     ", ifc_as_int)
        print("*  INVERTED unique ID as dec:    ", iui_as_int)
        print(" ")

        #   reset for next loop
        msg_check = msg_check_again

YAPI.FreeAPI()

input()
