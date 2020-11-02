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
#
#   CHANGES:
#       5-18-2020:  Re-organizing, debugging, cleaning.
#           *   added 3s timeout when prompting for vhub pw
#           *   added checks for specific USB devices
#
#


###############################################
#   INIT
###############################################

vars_before = set(dir())    #   this helps us check whether critical modules are imported later on

import os, sys, re, subprocess, msvcrt, time, win32com.client

# add ../../Sources to the PYTHONPATH
cwd = os.getcwd()
sys.path.append(os.path.join("{}/YoctoLibpy/Sources/".format(cwd)))

is_windows = '1' if os.name=='nt' else '0'

from yocto_api import *
from yocto_serialport import *


###############################################
#   DEFS
###############################################

class TimeoutExpired(Exception):
    pass


def input_with_timeout(prompt, timeout, timer=time.monotonic):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    endtime = timer() + timeout
    result = []
    while timer() < endtime:
        if msvcrt.kbhit():
            result.append(msvcrt.getwche()) #XXX can it block on multibyte characters?
            if result[-1] == '\n':   #XXX check what Windows returns here
                return ''.join(result[:-1])
        time.sleep(0.04) # just to yield to other processes/threads
    raise TimeoutExpired


def usb_rollcall(is_windows=is_windows):
    if is_windows == 0:
        device_re = re.compile("Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$", re.I)
        df = subprocess.check_output("lsusb")
        devices = []
        for i in df.split('\n'):
            if i:
                info = device_re.match(i)
                if info:
                    dinfo = info.groupdict()
                    dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
                    devices.append(dinfo)
        print(devices)


#wmi = win32com.client.GetObject ("winmgmts:")
#for usb in wmi.InstancesOf ("Win32_USBHub"):
#    print(usb.DeviceID)
#    usb.getattr()



def getpwvhub():
    #   get the pw from the user so we don't have to store it in this Failed
    global pwvhub_in
    #pwvhub_in = input(prompt) or "butterfly"
    prompt = "Enter password for VirtualHub local HTTP interface, or wait 3s to use default:    "

    try:
        pwvhub_in = input_with_timeout(prompt, 3)
    except TimeoutExpired:
        pwvhub_in = "butterfly"
        print('Using default.')
    else:
        print('Got %r' % pwvhub_in)


#   this doesn't work the way i want it to. oh well.
clearscr = lambda: os.system('cls' if os.name=='nt' else 'clear') or None


def moduletest(*mods):
   print("\n****************************************************")
   for mod in mods:
        modulename = mod
        if modulename in vars_after:
            print("*    Successfully loaded module:  {}".format(modulename))
            print("****************************************************")
        else:
            print('*    ERROR:   Failed to load module:  {}'.format(modulename))
            print("****************************************************")
   print()

def dec_to_bin(x):
    return int(bin(x)[2:])

def bin_to_dec(n):
    return int(n,2)

###############################################
#   WORK
###############################################

#   check modules
vars_after = set(dir()) - vars_before - {'vars_before'}
clearscr()
moduletest("YDevice","YSerialPort")

#   check for USB devices

usb_rollcall()

#   check for virtualhub



#   prompt user for virtualhub password
getpwvhub()
vhub_addr = "http://admin:{0}@127.0.0.1:4444".format(pwvhub_in)






#print(vars_after)

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
    print("Yocto-Serial mode and protocol have been set. These should appear below:")
    print("Mode = ", modecheck)
    print("Protocol = ", protcheck)
    print(" ")
    msg_check = serialPort.get_lastMsg()

#print("Waiting for input...")

while True:
    keyboard_in = input("Waiting for input and newline:    ")
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
        #   KB-typed fac. code dec translated to bina
        raw = str(keyboard_in)
        makeup_len = 24 - len(str(dec_to_bin(int(raw))))
        pre_str = makeup_len * "0"
        kb_bin = "x" + pre_str + str(dec_to_bin(int(raw))) + "x"
#        print(kb_bin,"<<<<<<<<<<<<<<<<<<<<<<<")
        #   fac. code binary string translated to hex:
        fc_as_hstr = '%0*X' % ((len(btrunc[:8]) + 3) // 4, int(btrunc[:8], 2))
        #   fac. code binary string translated to hex:
        fc_as_hstr = '%0*X' % ((len(btrunc[:8]) + 3) // 4, int(btrunc[:8], 2))
        #   unique ID binary string translated to ascii:
        ui = btrunc[8:]
        ui_as_text = ''.join(chr(int(ui[i:i+8], 2)) for i in range(0, len(ui), 8))

        #################################
        #   fac.code binary string translated to decimal
        fc_as_int = int(btrunc[:8], base=2)
        #   unique ID binary string translated to decimal
        ui_as_int = int(ui, base=2)
        ##################################

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
        print("Received via USB \"keyboard\" (binary to decimal):    ", keyboard_in)
        print("Received via Wiegand Output (binary to decimal):   ", (10-len(str(bin_to_dec(rbstr[1:25]))))*" ", bin_to_dec(rbstr[1:25]))
        print("    raw bit length:      ", rblen)
        print("    raw binary:          ", rbstr)
        print(" ")
        if rblen >= 26:
            print("                         ", rbstr[0], " ", rbstr[1:9], " ", rbstr[9:25], " ", rbstr[25])
            print("                          P   AAAAAAAA   BBBBBBBBBBBBBBBB   P")
#           print(" ")
#        print("    raw as hex:          ", rb_as_hstr)
#        print("    raw as decimal:      ", rb_as_int)
#        print("    raw as ascii:        ", rb_as_text)
#        print(" ")
#        print("    truncated length:    ", btrunclen)
#        print("    trunc'd binary:       ", btrunc)
#        print(" ")
#        print("    trunc'd as hex:      ", tb_as_hstr)
#        print("    trunc'd as decimal:  ", tb_as_int)
#        print("    trunc'd as ascii:    ", tb_as_text)
#        print(" ")
        print("                   facility code ^^^           ^^^ unique card ID")
        print(" ")
        print(" ---------------------------------")
        print("*  Wiegand Output facility code (binary to decimal): ", fc_as_int)
        print("*  Wiegand Output unique ID (binary to decimal):    ", ui_as_int)
        print(" ---------------------------------")
        print(" ")
        print("   facility code as hex: ", fc_as_hstr)
        print("    unique ID as hex:    ", ui_as_hstr)
        print(" ")
        print("*  INVERTED fac.code as dec:     ", ifc_as_int)
        print("*  INVERTED unique ID as dec:    ", iui_as_int)
#        print(" ")

        #   reset for next loop
        msg_check = msg_check_again

YAPI.FreeAPI()

input()
