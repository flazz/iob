#!/usr/bin/env python

import dbus, gobject, dbus.glib, urllib, re
from BeautifulSoup import BeautifulSoup

# authroitative account
ACCOUNT = "flazzarino@gmail.com/work"
PROTOCOL = "XMPP"
INOUT_URL = "http://calvin/clockwork/index.php"

class InOutBoard:

  def __init__(self, url):
    self.url = url

    # get the post vars from the form: inputs (6), selects (2), textareas (1)
    self.params = {}
    html = urllib.urlopen(self.url + '?go=1').read()
    soup = BeautifulSoup(html)

    for input in soup.html.body.findAll('input'):
      self.params[input['name']] = input['value']

    for select in soup.html.body.findAll(['select']):
      name = select['name']
      option = select.find('option', { "selected" : "SELECTED" })
      if option == None:
        self.params[name] = ''
      else:
        self.params[name] = option['value']

    for textarea in soup.html.body.find(['textarea']):
      self.params[textarea['name']] = '\n'.join(textarea.contents)


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
    if status == "Away" or status == "Offline":
      board.mark_out(message)
    else:
      board.mark_in(message)

bus.add_signal_receiver(onStatusChanged,
                        dbus_interface="im.pidgin.purple.PurpleInterface",
                        signal_name="AccountStatusChanged")

# Start the main loop
gobject.MainLoop().run()
