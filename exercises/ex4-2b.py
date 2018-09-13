# Solution to exercise 4-2: 

# Use callLater() to make the client timeout if a poem hasn't finished after a given interval. 
# Read about the return value of callLater so you can cancel the timeout if the poem finishes on time.

# NOTE: This should not be used as the basis for production code.
# It uses low-level Twisted APIs as a learning exercise.

import datetime, errno, optparse, socket

from twisted.internet import main


def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 1.0.
Run it like this:

  python ex4-2b.py port1 port2 port3 ...

If you are in the base directory of the twisted-intro package,
you could run it like this:

  python twisted-client-1/ex4-2b.py 10001 10002 10003

to grab poetry from servers on ports 10001, 10002, and 10003.

Of course, there need to be servers listening on those ports
for that to work.
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


class PoetrySocket(object):

    poem = ''

    def __init__(self, task_num, address, complete_timeout=5):
        self.task_num = task_num
        self.address = address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.sock.connect_ex(address) == 0:  # Like connect(address), but returns error indicator instead of raising an exception for errors returned by the C-level connect() call
            self.sock.setblocking(0)

            # Tell the Twisted reactor to monitor this socket for reading
            from twisted.internet import reactor
            reactor.addReader(self)
        else: 
            print("Could not connect to task %d" % self.task_num)
        self.timeout = reactor.callLater(complete_timeout, self.forceClose)

    def fileno(self):
        try:
            return self.sock.fileno()  # Returns the object's file descriptor (a small int)
        except socket.error:
            return -1

    def forceClose(self): 
        self.connectionLost("Poem was not completed within allowed timeframe")

    def connectionLost(self, reason=None):
        self.sock.close()

        # Stop monitoring this socket
        from twisted.internet import reactor
        print("Reactor no longer monitored: %s" % reason)
        reactor.removeReader(self)

        # See if there are any poetry sockets left
        for reader in reactor.getReaders():
            if isinstance(reader, PoetrySocket):
                return

        reactor.stop()  # No more poetry

    def doRead(self):
        bytes = ''

        while True:
            try:
                bytesread = self.sock.recv(1024)
                if not bytesread:
                    break
                else:
                    bytes += bytesread
            except socket.error, e:
                if e.args[0] == errno.EWOULDBLOCK:  # Operation would block
                    break
                return main.CONNECTION_LOST

        if not bytes:
            print 'Task %d finished' % self.task_num
            self.timeout.cancel()
            return main.CONNECTION_DONE
        else:
            msg = 'Task %d: got %d bytes of poetry from %s'
            print  msg % (self.task_num, len(bytes), self.format_addr())

        self.poem += bytes

    def logPrefix(self):
        return 'poetry'

    def format_addr(self):
        host, port = self.address
        return '%s:%s' % (host or '127.0.0.1', port)


def poetry_main():
    addresses = parse_args()

    start = datetime.datetime.now()

    sockets = [PoetrySocket(i + 1, addr) for i, addr in enumerate(addresses)]

    from twisted.internet import reactor
    reactor.run()

    elapsed = datetime.datetime.now() - start

    for i, sock in enumerate(sockets):
        print 'Task %d: %d bytes of poetry' % (i + 1, len(sock.poem))

    print 'Got %d poems in %s' % (len(addresses), elapsed)


if __name__ == '__main__':
    poetry_main()

