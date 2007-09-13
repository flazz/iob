#!/usr/bin/env python

import dbus, gobject, dbus.glib, sys
from fcla import InOutBoard, INOUT_URL
from optparse import OptionParser

# authroitative account

parser = OptionParser()
parser.add_option("-a", "--account", dest="account", metavar="ACCOUNT", 
                  help="the pidgin account sync presence to")

parser.add_option("-p", "--protocol", dest="protocol", metavar="PROTOCOL", 
                  help="the pidgin protocol sync presence to")

# TODO load defaults from dbus
parser.set_defaults(account="flazzarino@gmail.com/work", protocol="XMPP")

(options, args) = parser.parse_args(sys.argv)

# make an in out board object
board = InOutBoard(INOUT_URL)

# Initiate a connection to the Session Bus
bus = dbus.SessionBus()

# Associate Pidgin's D-Bus interface with Python objects
obj = bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")
purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")

def onStatusChanged(acctID, old, new):
  if purple.PurpleAccountGetUsername(acctID) == options.account and \
        purple.PurpleAccountGetProtocolName(acctID) == options.protocol:
    status = purple.PurpleStatusTypeGetName(purple.PurpleStatusGetType(new))
    message = purple.PurpleSavedstatusGetMessage(purple.PurpleSavedstatusGetCurrent())
    if status == "Away" or status == "Offline":
      board.mark_out(message)
    else:
      board.mark_in(message)

bus.add_signal_receiver(onStatusChanged,
                        dbus_interface="im.pidgin.purple.PurpleInterface",
                        signal_name="AccountStatusChanged")

# Start the main loop
gobject.MainLoop().run()
