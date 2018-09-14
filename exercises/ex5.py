# Solution to exercises 5-1 and 5-2: 
# Use callLater() to make the client timeout if the poem hasn't finished after a given interval.
# Use the loseConnection() method on the transport to close the connection on a timeout.
# Cancel the timeout if the poem finishes on time.
# Use the stacktrace() method to analyze the callback sequence that occurs when connectionLost() is invoked.

import traceback, optparse, datetime
from twisted.internet.protocol import Protocol, ClientFactory

def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 2.0.
Run it like this:

  python ex5-1+2.py port1 port2 port3 ...
"""

    parser = optparse.OptionParser(usage)
    _, addresses = parser.parse_args()
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
    return map(parse_address, addresses)


class PoetryProtocol(Protocol):
    poem = ''
    task_num = 0

    def dataReceived(self, data):
        self.poem += data
        msg = 'Task %d: got %d bytes of poetry from %s'
        print msg % (self.task_num, len(data), self.transport.getPeer())

    def connectionLost(self, reason):
        from twisted.internet import reactor  
        if self.timeout.active(): 
            self.timeout.cancel()
        self.poemReceived(self.poem)

        # For the solution to exercise 5-2, uncomment the following two lines! 
        # print('Connection for task %d lost, printing stack trace: ' % self.task_num)
        # traceback.print_stack()

    def poemReceived(self, poem):
        self.factory.poem_finished(self.task_num, poem)

    def makeConnection(self, transport): 
        Protocol.makeConnection(self, transport)
        from twisted.internet import reactor
        self.timeout = reactor.callLater(20, self.transport.loseConnection)
        print('Connection established for task %d' % self.task_num)


class PoetryClientFactory(ClientFactory):
    task_num = 1
    protocol = PoetryProtocol  # Tell base class what proto to build

    def __init__(self, poetry_count):
        self.poetry_count = poetry_count
        self.poems = {}  # Task num -> poem

    def buildProtocol(self, address):
        protocol = ClientFactory.buildProtocol(self, address)
        protocol.task_num = self.task_num
        self.task_num += 1
        return protocol

    def poem_finished(self, task_num=None, poem=None):
        if task_num is not None:
            self.poems[task_num] = poem

        self.poetry_count -= 1

        if self.poetry_count == 0:
            self.report()
            from twisted.internet import reactor
            reactor.stop()

    def report(self):
        for i in self.poems:
            print 'Task %d: %d bytes of poetry' % (i, len(self.poems[i]))

    def clientConnectionFailed(self, connector, reason):
        print 'Failed to connect to:', connector.getDestination()
        self.poem_finished()


def poetry_main():
    addresses = parse_args()
    start = datetime.datetime.now()
    factory = PoetryClientFactory(len(addresses))
    from twisted.internet import reactor
    for address in addresses:
        host, port = address
        reactor.connectTCP(host, port, factory)
    reactor.run()
    elapsed = datetime.datetime.now() - start
    print 'Got %d poems in %s' % (len(addresses), elapsed)


if __name__ == '__main__':
    poetry_main()
