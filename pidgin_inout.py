#!/usr/bin/env python

import dbus, gobject, dbus.glib, sys
from fcla import InOutBoard, INOUT_URL
from optparse import OptionParser

# make an in out board object
try:
  board = InOutBoard(INOUT_URL)
  print 'Connected to in/out board at %s' % INOUT_URL
except IOError:
  sys.stderr.write('Error: cannot connect to the in/out board at %s, is it down?\n' % INOUT_URL)
  sys.exit(1)


# Initiate a connection to the Session Bus
bus = dbus.SessionBus()

# Associate Pidgin's D-Bus interface with Python objects
try:
  obj = bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")
  purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")
  print 'Connected to pidgin'
except dbus.DBusException:
  sys.stderr.write('Error: cannot connect to pidgin, is it running?\n')
  sys.exit(1)



# Process Command Line arguments
parser = OptionParser()
parser.add_option("-a", "--account", dest="account", metavar="ACCOUNT", 
                  help="the pidgin account sync presence to")

parser.add_option("-p", "--protocol", dest="protocol", metavar="PROTOCOL", 
                  help="the pidgin protocol sync presence to")
# TODO load defaults from dbus
parser.set_defaults(account="flazzarino@gmail.com/work", protocol="XMPP")
(options, args) = parser.parse_args(sys.argv)

# TODO Test if pidgin is running with this account
print 'Syncing to account %s://%s' % (options.protocol, options.account)

# Print blank line to show that headers are over
print

def onStatusChanged(acctID, old, new):
  if purple.PurpleAccountGetUsername(acctID) == options.account and \
        purple.PurpleAccountGetProtocolName(acctID) == options.protocol:
    status = purple.PurpleStatusTypeGetName(purple.PurpleStatusGetType(new))
    message = purple.PurpleSavedstatusGetMessage(purple.PurpleSavedstatusGetCurrent())
    print '%s: %s' % (status, message)
    try:
      if status == "Away" or status == "Offline":
        board.mark_out(message)
      else:
        board.mark_in(message)
    except IOError:
      sys.stderr.write('Error: cannot connect to the in/out board at %s, is it down?\n' % INOUT_URL)
      sys.exit(1)

bus.add_signal_receiver(onStatusChanged,
                        dbus_interface="im.pidgin.purple.PurpleInterface",
                        signal_name="AccountStatusChanged")

# Start the main loop
gobject.MainLoop().run()
