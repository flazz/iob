from Foundation import *
from ScriptingBridge import *
from fcla import *

iChat = SBApplication.applicationWithBundleIdentifier_("com.apple.iChat")

ICHAT_STATUS_CODES = { 
	0x61776179: 'Away',
	0x6176616c: 'Available',
	0x6f66666c: 'Offline',
	0x696e7673: 'Invisible'
}

status = ICHAT_STATUS_CODES[iChat.status()]

# make an in out board object
try:
	board = InOutBoard(INOUT_URL)
	print 'Connected to in/out board at %s' % INOUT_URL
except IOError:
	sys.stderr.write('Error: cannot connect to the in/out board at %s, is it down?\n' % INOUT_URL)
	sys.exit(1)

# sign in or out
try:
	if status == "Away" or status == "Offline":
		print "Marking out"
		board.mark_out()
	else:
		print "Marking in"
		board.mark_in()
except IOError:
	sys.stderr.write('Error: cannot connect to the in/out board at %s, is it down?\n' % INOUT_URL)
	sys.exit(1)
