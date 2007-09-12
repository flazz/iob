#!/usr/bin/env python

import dbus, gobject, dbus.glib

# Initiate a connection to the Session Bus
bus = dbus.SessionBus()

# Associate Pidgin's D-Bus interface with Python objects
obj = bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")
pidgin = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")

# Associate libnotify's D-Bus interface with Python objects

notify_obj = bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
notify = dbus.Interface(notify_obj, "org.freedesktop.Notifications")

# Create a global Pidgin buddy data cache
buddy_data_cache = {}

def onSignOn(bId):
  # Extract a Pidgin buddy's name and alias
  buddyAlias = pidgin.PurpleBuddyGetAlias(bId)
  buddyName = pidgin.PurpleBuddyGetName(bId)

  # Generate notification text based on the buddy's name and alias

  text = buddyAlias == buddyName and \
    "<b>%s</b> is now online." % buddyName or \
    "<b>%s</b> <i>(%s)</i> is now online." % (buddyAlias, buddyName)

  # Display a notification bubble with a button to launch a conversation
  nId = notify.Notify("DBus Test", 0, "gtk-connect", "Buddy Signed On",
      text, ["message", "Send Message"], {}, 9000)

  # Add the buddy ID and name to the global buddy data cache

  buddy_data_cache[nId] = (pidgin.PurpleBuddyGetAccount(bId), buddyName)

def onNotifyClose(nId):
  # Remove entry from the global buddy data cache when the bubble closes
  if buddy_data_cache.has(nId):
    del buddy_data_cache[nId]

def onNotifyAction(nId, actKey):
  # Launch a new conversation when user clicks the message button

  if actKey == "message":
    pidgin.PurpleConversationNew(1, *buddy_data_cache[nId])

# Bind the onSignOn function with Pidgin's BuddySignedOn event
bus.add_signal_receiver(onSignOn,
  dbus_interface="im.pidgin.purple.PurpleInterface",
  signal_name="BuddySignedOn")

# Bind the onNotifyAction function to libnotify's ActionInvoked event
bus.add_signal_receiver(onNotifyAction,
    dbus_interface="org.freedesktop.Notifications",
    signal_name="ActionInvoked")


# Bind the onNotifyClose function to libnotify's CloseNotification event
bus.add_signal_receiver(onNotifyClose,
    dbus_interface="org.freedesktop.Notifications",
    signal_name="CloseNotification")

# Start the main loop
gobject.MainLoop().run()
