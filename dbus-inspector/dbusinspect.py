#!/usr/bin/python
# Copyright (C) 2007, Erich Schubert <erich@debian.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA 

import gobject
import dbus, dbus.glib
import os, sys
from xml.dom import minidom

class dbusnode:
	"""
	Generic interface for the introspected tree
	"""
	def __init__(self, parent, xml):
		"""
		Constructor:
		parent -- parent node in tree or DBus Bus
		xml -- xml.dom.minidom.Element with full information
		"""
		self.parent = parent
		self.xml = xml
		self.children = []
		self.name = None

		self._validate()

	def _validate(self):
		"""
		Validation function, to be implemented in derived classes
		"""
		assert(self.parent)
		assert(self.xml)

	def label(self):
		"""
		Return a "pretty label" for this node, to be used in UI.
		"""
		return self.name

	def getBus():
		"""
		Find the bus this node is on.
		"""
		assert(self.parent)
		return self.parent.getBus()

	def getServiceid():
		"""
		Find service ID for this object
		"""
		assert(self.parent)
		return self.parent.getServiceid()

class service(dbusnode):
	"""
	Representation of a DBus service description
	"""
	def __init__(self, parent, xml, path, aliases):
		dbusnode.__init__(self, parent, xml)
		self.path = path
		self.aliases = aliases

		if self.path == "/" or not self.xml.hasChildNodes():
			self._introspect()
		self._expand()
	
	def _validate(self):
		"""
		We can't assert self.xml yet, since we might still need to query it.
		"""
		assert(not self.xml or self.xml.localName == "node")
	
	def getBus(self):
		"""
		Find DBus this service is on
		"""
		if isinstance(self.parent, dbus.Bus):
			return self.parent
		# fallback
		if not isinstance(self.parent, service):
			return self.parent
		return self.parent.getBus()

	def getServiceid(self):
		"""
		Find service ID for this object
		"""
		return self.aliases[0]

	def _expand(self):
		"""
		Expand the nodes in the XML data to Python objects.
		"""
		for c in self.xml.childNodes:
			if c.nodeType != c.ELEMENT_NODE: continue
			if c.localName == "node":
				assert(c.getAttribute("name"))
				cpath = service._extendpath(self.path, c)
				self.children.append(service(self, c, cpath, self.aliases))
			elif c.localName == "interface":
				self.children.append(interface(self, self.path, c))
			else:
				sys.stderr.write("Unhandled node with tag '%s' in Introspect\n" % c.localName)

	def _introspect(self):
		"""
		Do a DBus introspection call for this node.
		"""
		# hack around tracker issue, fixed past 0.80.2
		if self.prettyname().find("Tracker") >= 0:
			if dbus.version <= (0,80,2):
				self.xml = minidom.Element("node")
				self.xml.setAttribute("failed", "yes")
				return

		sv_obj = self.getBus().get_object(self.getServiceid(), self.path)
		intro_if = dbus.Interface(sv_obj, 'org.freedesktop.DBus.Introspectable')
		try:
			ispect = intro_if.Introspect()
		except: # dbus.DBusException:
			sys.stderr.write("Introspection failed for %s, %s\n" % (self.prettyname(), self.path))
			self.xml = minidom.Element("node")
			self.xml.setAttribute("failed", "yes")
			return
		# parse the result document
		dom = minidom.parseString(ispect)
		# find root node
		for node in dom.childNodes:
			if node.nodeType == node.ELEMENT_NODE:
				self.xml = node
		assert(self.xml and self.xml.localName == "node")

	@staticmethod
	def _extendpath(path,node):
		"""
		Path name handling, similar to os.path.join.
		Could be using os.path on most systems, but maybe not on mac?
		"""
		if path == "/":
			return "/" + node.getAttribute("name")
		else:
			return path + "/" + node.getAttribute("name")

	def __str__(self):
		return "service '%s' ( %s )" % (self.path, ", ".join(map(lambda x:x.__str__(), self.children)))
	
	def prettyname(self):
		for alias in self.aliases:
			if alias[0] != ':':
				return "%s (%s)" % (alias, self.aliases[0])
		return self.aliases[0]

	def label(self):
		"""
		Generate a pretty label for this entry.
		"""
		postfix = ""
		if self.xml.hasAttribute("failed"):
			postfix = " (inspection failed)"
		# Top level entries will be labeled 'service'
		if self.path == "/":
			return self.prettyname() + postfix
		return self.path[self.path.rindex("/")+1:] + postfix

class interface(dbusnode):
	"""
	Representation of a DBus interface
	"""
	def __init__(self, parent, path, xml):
		dbusnode.__init__(self, parent, xml)
		self.path = path
		self.name = xml.getAttribute("name")
		self._expand()

	def _validate(self):
		assert(self.xml.localName == "interface")
		assert(self.xml.getAttribute("name"))

	def _expand(self):
		for c in self.xml.childNodes:
			if c.nodeType != c.ELEMENT_NODE: continue
			if c.localName == "method":
				self.children.append(method(self, c))
			elif c.localName == "signal":
				self.children.append(signal(self, c))
			elif c.localName == "property":
				self.children.append(property(self, c))
			elif c.localName == "annotation":
				self.children.append(annotation(self, c))
			else:
				sys.stderr.write("Unhandled tag '%s' in interface %s,%s.\n"
					% (c.localName, self.path, self.name))
	
	def __str__(self):
		return "interface '%s' ( %s )" % (self.name, ", ".join(map(lambda x:x.__str__(), self.children)))

class dbussignature(dbusnode):
	"""
	Shared 'expand' for signals and methods
	"""
	def _expand(self):
		for c in self.xml.childNodes:
			if c.nodeType != c.ELEMENT_NODE: continue
			if c.localName == "arg":
				self.children.append(arg(self, c))
			else:
				sys.stderr.write("Unhandled tag '%s' in method %s.\n"
					% (c.localName, self.name))

class method(dbussignature):
	"""
	Representation of a DBus method
	"""
	def __init__(self, parent, xml):
		dbusnode.__init__(self, parent, xml)
		self.name = xml.getAttribute("name")
		self._expand()

	def _validate(self):
		assert(self.xml.localName == "method")
		assert(self.xml.getAttribute("name"))

	def __str__(self):
		return "method '%s'" % self.name

class signal(dbussignature):
	"""
	Representation of a DBus signal
	"""
	def __init__(self, parent, xml):
		dbusnode.__init__(self, parent, xml)
		self.name = xml.getAttribute("name")
		self._expand()

	def _validate(self):
		assert(self.xml.localName == "signal")
		assert(self.xml.getAttribute("name"))

	def __str__(self):
		return "signal '%s'" % self.name

class property(dbusnode):
	"""
	Representation of a DBus property
	"""
	def __init__(self, parent, xml):
		dbusnode.__init__(self, parent, xml)
		self.name = xml.getAttribute("name")
		print self.xml.toxml()

	def _validate(self):
		assert(self.xml.localName == "property")
		assert(self.xml.getAttribute("name"))

	def __str__(self):
		return "property '%s'" % self.name

class annotation(dbusnode):
	"""
	Representation of a DBus annotation
	"""
	def __init__(self, parent, xml):
		dbusnode.__init__(self, parent, xml)
		self.name = xml.getAttribute("name")
		print self.xml.toxml()

	def _validate(self):
		assert(self.xml.localName == "annotation")
		assert(self.xml.getAttribute("name"))

	def __str__(self):
		return "annotation '%s'" % self.name

class arg(dbusnode):
	"""
	Representation of a DBus method/signal argument
	"""
	def __init__(self, parent, xml):
		dbusnode.__init__(self, parent, xml)

		if self.xml.hasAttribute("direction"):
			self.direction = self.xml.getAttribute("direction")
		elif isinstance(self.parent, signal):
			self.direction = "out"
		else:
			self.direction = "undefined"
		self.type = self.xml.getAttribute("type")
		if self.xml.hasAttribute("name"):
			self.name = self.xml.getAttribute("name")
		else:
			self.name = "*unnamed*"

	def _validate(self):
		assert(self.xml.localName == "arg")
		assert(self.xml.getAttribute("type"))

	def __str__(self):
		return "argument '%s'" % self.name

def discover(bus):
	"""
	Start discovery of a bus.
	returns a list of services discovered.
	"""
	dbus_obj = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
	dbus_if = dbus.Interface(dbus_obj, 'org.freedesktop.DBus')
	services = dbus_if.ListNames()

	servicemap = {}
	for s in services:
		realservice = dbus_if.GetNameOwner(s)
		if servicemap.has_key(realservice):
			servicemap[realservice].append(s)
		else:
			servicemap[realservice] = [s]
	
	servicelist = []
	for serviceid, aliases in servicemap.iteritems():
		aliases.sort()
		# if the service doesn't have aliases, it probably is an anonymous
		# client that doesn't have a dbus event loop.
		if len(aliases) == 0:
			sys.stderr.write("Service with 0 aliases found, shouldn't exist.\n")
			continue
		if len(aliases) == 1:
			if serviceid != aliases[0]:
				sys.stderr.write("Service not an alias of itself?\n")
				continue
			if serviceid[0] == ":":
				# numeric ID only, skip.
				continue
			# non-numeric ID should be a true service
			# only one known case: org.freedesktop.DBus itself
		servicelist.append(service(bus, None, "/", aliases))
	return servicelist

def test():
	sysbus = dbus.SystemBus()
	sesbus = dbus.SessionBus()

	print "System Bus:"
	print discover(sysbus)
	print "Session Bus:"
	print discover(sesbus)

if __name__ == "__main__":
	test()
