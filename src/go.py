#!/usr/bin/env python

import dbus, gobject, dbus.glib
from fcla import InOutBoard, INOUT_URL

# authroitative account
ACCOUNT = "flazzarino@gmail.com/work"
PROTOCOL = "XMPP"

# make an in out board object
board = InOutBoard(INOUT_URL)

# Initiate a connection to the Session Bus
bus = dbus.SessionBus()

# Associate Pidgin's D-Bus interface with Python objects
obj = bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")
purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")

def onStatusChanged(acctID, old, new):
  if purple.PurpleAccountGetUsername(acctID) == ACCOUNT and \
        purple.PurpleAccountGetProtocolName(acctID) == PROTOCOL:
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
