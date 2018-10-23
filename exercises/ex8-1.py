# Solution to exercise 8-1a: 
# Timeout if the poem isn't received after a given period of time
# Fire the deferred's errback with a custom exeption in that case
# Close the connection in that case

import optparse, sys

from twisted.internet import defer
from twisted.internet.protocol import Protocol, ClientFactory


class TimeoutError(Exception):  # custom exception (that does nothing)
    pass


def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...
"""
    parser = optparse.OptionParser(usage)
    help = "Timeout in seconds."
    parser.add_option('-t', '--timeout', type='float', help=help, default=5.0)
    options, addresses = parser.parse_args()
    if not addresses:
        print parser.format_help()
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

    return map(parse_address, addresses), options


class PoetryProtocol(Protocol): 
    poem = ''

    def dataReceived(self, data): 
        self.poem += data

    def connectionLost(self, reason):
        self.poemReceived(self.poem)

    def poemReceived(self, poem): 
        self.factory.poem_finished(poem)


class PoetryClientFactory(ClientFactory): 
    protocol = PoetryProtocol
    
    def __init__(self, deferred, timeout): 
        self.deferred = deferred
        self.timeout = timeout
        self.timeout_call = None

    def startedConnecting(self, connector): 
        from twisted.internet import reactor
        self.timeout_call = reactor.callLater(self.timeout, self.on_timeout, connector)  # cancel download if it does not finish within given timeout 

    def poem_finished(self, poem): 
        if self.deferred is not None: 
            d, self.deferred = self.deferred, None
            d.callback(poem)
        self.cancel_timeout()

    def clientConnectionFailed(self, connector, reason): 
        if self.deferred is not None: 
            d, self.deferred = self.deferred, None
            d.errback(reason)
        self.cancel_timeout()

    def on_timeout(self, connector): 
        self.timeout_call = None
        if self.deferred is not None: 
            d, self.deferred = self.deferred, None
            d.errback(TimeoutError())  # fire custom exception if poem download failed
            connector.disconnect()  # close connection if poem download failed

    def cancel_timeout(self): 
        if self.timeout_call is not None: 
            call, self.timeout_call = self.timeout_call, None
            call.cancel()


def get_poetry(host, port, timeout): 
    d = defer.Deferred()
    from twisted.internet import reactor
    factory = PoetryClientFactory(d, timeout)
    reactor.connectTCP(host, port, factory)
    return d


def poetry_main():
    addresses, options = parse_args()
    from twisted.internet import reactor
    poems = []
    errors = []
    
    def got_poem(poem): 
        poems.append(poem)

    def poem_failed(err): 
        print >> sys.stderr, 'Poem failed: ', err
        errors.append(err)

    def poem_done(_): 
        if len(poems) + len(errors) == len(addresses): 
            reactor.stop()

    for address in addresses: 
        host, port = address
        d = get_poetry(host, port, options.timeout)
        d.addCallbacks(got_poem, poem_failed)
        d.addBoth(poem_done)

    reactor.run()

    for poem in poems: 
        print(poem)


if __name__ == '__main__':
    poetry_main()
