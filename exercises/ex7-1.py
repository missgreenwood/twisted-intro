import sys
from twisted.internet.defer import Deferred


def got_poem(poem): 
   print(poem) 
   return 'I am got_poem()\'s return value.'

def poem_failed(err): 
    sys.stderr.write('poem download failed')
    sys.stderr.write('I am terribly sorry')
    sys.stderr.write('try again later?')

def poem_done(_): 
    print(_)
    from twisted.internet import reactor
    reactor.stop()

d = Deferred()
d.addCallbacks(got_poem, poem_failed)
d.addBoth(poem_done)
from twisted.internet import reactor
reactor.callWhenRunning(d.callback, 'Another short poem.')
reactor.run()
