#!/usr/bin/env python

import dbus, gobject, dbus.glib, urllib

# authroitative account
ACCOUNT = "flazzarino@gmail.com/work"
PROTOCOL = "XMPP"
INOUT_URL = "http://calvin/clockwork/index.php"

class InOutBoard:

  def __init__(self, url):
    self.url = url
    self.parse_info()
    
  def parse_info(self):
    self.params = {}
    info_url = self.url + '?go=1'
    # TODO get the info URL and scrape it
    # scrape hidden info
#    params['user_id'] /html/body/table/tbody/tr/td/input/@value
#    params['modifier'] /html/body/table/tbody/tr/td/input[2]/@value
#    params['person_id'] /html/body/table/tbody/tr/td/input[3]/@value

    # scrape user info
#    params['time_back']
#    params['in_out']
#    params['phone']
#    params['email'] = '---'
#    params['comment']

  def mark_out(self, message):
    self.mark(message, 0)

  def mark_in(self, message):
    self.mark(message, 1)

  def mark(self, message, presence):
    self.params['comment'] = message
    self.params['in_out'] = presence
    urllib.urlopen(self.url, urllib.urlencode(self.params))

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
    print '!'
    if status == "Away" or status == "Offline":
      board.mark_out(message)
    else:
      board.mark_in(message)

bus.add_signal_receiver(onStatusChanged,
                        dbus_interface="im.pidgin.purple.PurpleInterface",
                        signal_name="AccountStatusChanged")

# Start the main loop
gobject.MainLoop().run()
