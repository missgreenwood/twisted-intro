# Solution to exercise 7-2b: 
# Modify the code to fire the errback chain. Make sure to fire the errback with an Exception.

import sys

from twisted.internet.defer import Deferred

def got_poem(poem):
    print poem

def poem_failed(err):
    print >>sys.stderr, 'poem download failed'
    print >>sys.stderr, 'I am terribly sorry'
    print >>sys.stderr, 'try again later?'
    print(err)
    from twisted.internet import reactor
    reactor.stop()

def poem_done(_):
    from twisted.internet import reactor
    reactor.stop()

d = Deferred()

d.addErrback(poem_failed)

from twisted.internet import reactor

reactor.callWhenRunning(d.errback, Exception)

reactor.run()
