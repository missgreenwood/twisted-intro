# Solutions to exercises 6-1 & 6-3: 

# Update client to timeout if the poem isn't received after a given period of time. Invoke the 
# errback with a custom exeption in that case. Close the connection when you do. 

# Use print statements to verify that clientConnectionFailed() is called after get_poetry returns. 

import optparse, sys
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.python.failure import Failure

def parse_args(): 
    usage = """usage: %prog [options] [hostname:]port ...

        This is the Twisted Get Poetry Now! client, Twisted version 3.1.
     Run it like this: 

        python ex6.py port1 port2 port3 ...
    """

    parser = optparse.OptionParser(usage)

    _, addresses = parser.parse_args()

    if not addresses: 
        print(parser.format_help())
        parser.exit() 

    def parse_address(addr): 
        if ':' not in addr: 
            host = '127.0.0.1'
            port = addr
        else: 
            host, port = addr.split(':', 1)
        if not port.isdigit(): 
            parser.error('Ports must be integers.')
            
        return host, int(port)

    return map(parse_address, addresses)
 

class PoetryProtocol(Protocol):
    poem = ''

    def dataReceived(self, data): 
        self.poem += data

    def connectionLost(self, reason): 
        if self.delayed_timeout.active(): 
            print('Cancelling timeout because task is finished')
            self.delayed_timeout.cancel()
        self.poemReceived(self.poem)

    def poemReceived(self, poem): 
        self.factory.poem_finished(poem)

    def connectionMade(self):
        from twisted.internet import reactor
        self.delayed_timeout = reactor.callLater(5, self.timeout, TimeoutException().__str__())

    def timeout(self, failure):
        self.factory.errback(failure)
        self.transport.loseConnection()


class TimeoutException(Exception):
    def __init__(self): 
        self.msg = 'timeout exception occurred'

    def __str__(self): 
        return repr(self.msg)


class PoetryClientFactory(ClientFactory): 

    protocol = PoetryProtocol

    def __init__(self, callback, errback): 
        self.callback = callback
        self.errback = errback

    def poem_finished(self, poem):
        self.callback(poem)

    def clientConnectionFailed(self, connector, reason): 
        print('PoetryClientFactory.clientConnectionFailed() has been called.')
        self.errback(reason)


def get_poetry(host, port, callback, errback): 
    """ Download a poem from the given host and port and invoke callback(poem) 
        when the poem is complete. When there is a failure, invoke errback(err) 
        instead, where err is a twisted.python.failure.Failure instance. 
    """
    from twisted.internet import reactor
    factory = PoetryClientFactory(callback, errback)
    reactor.connectTCP(host, port, factory)


def poetry_main(): 
    addresses = parse_args()

    from twisted.internet import reactor

    poems = []
    errors = []
    
    def got_poem(poem): 
        poems.append(poem)
        poem_done()

    def poem_failed(err): 
        sys.stderr.write('Poem failed: ' + str(err) + '\n')
        errors.append(err)
        poem_done()

    def poem_done(): 
        if len(poems) + len(errors) == len(addresses): reactor.stop()

    for address in addresses: 
        host, port = address
        get_poetry(host, port, got_poem, poem_failed)
    reactor.run()
    for poem in poems: 
        print(poem)


if __name__ == '__main__':
    poetry_main()
