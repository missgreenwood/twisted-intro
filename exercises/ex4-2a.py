# Solution to exercise 4-2: 

# Use callLater() to make the client timeout if a poem hasn't finished after a given interval. 
# Read about the return value of callLater so you can cancel the timeout if the poem finishes on time.

# NOTE: This should not be used as the basis for production code.
# It uses low-level Twisted APIs as a learning exercise.

import datetime, errno, optparse, socket

from twisted.internet import main


finished = dict()
ID = 0

def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 1.0.
Run it like this:

  python ex4-2a.py port1 port2 port3 ...

If you are in the base directory of the twisted-intro package,
    print(type(sockets))
you could run it like this:

  python twisted-client-1/ex4-2a.py 10001 10002 10003

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

    def __init__(self, task_num, address):
        self.task_num = task_num
        self.address = address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(address)
        self.sock.setblocking(0)
        self.finished = 1
        global ID
        self.id = ID
        ID += 1 
        global finished
        finished[str(self.id)] = self.finished

        # tell the Twisted reactor to monitor this socket for reading
        from twisted.internet import reactor
        reactor.addReader(self)

    def fileno(self):
        try:
            return self.sock.fileno()
        except socket.error:
            return -1

    def connectionLost(self, reason):
        self.sock.close()

        # stop monitoring this socket
        from twisted.internet import reactor
        reactor.removeReader(self)

        # see if there are any poetry sockets left
        for reader in reactor.getReaders():
            if isinstance(reader, PoetrySocket):
                return

        reactor.stop() # no more poetry

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
                if e.args[0] == errno.EWOULDBLOCK:
                    break
                return main.CONNECTION_LOST

        if not bytes:
            print 'Task %d finished' % self.task_num
            finished[str(self.id)] = 0
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


def cancelPoetryReading(sockets): 
    print("There should be the socket closing function")  # TODO


def poetry_main():
    addresses = parse_args()

    start = datetime.datetime.now()

    sockets = [PoetrySocket(i + 1, addr) for i, addr in enumerate(addresses)]

    print(finished)

    from twisted.internet import reactor
    if not all(x==0 for x in finished.values()):
        reactor.callLater(5, cancelPoetryReading, socket)
    reactor.run()

    elapsed = datetime.datetime.now() - start

    for i, sock in enumerate(sockets):
        print 'Task %d: %d bytes of poetry' % (i + 1, len(sock.poem))

    print 'Got %d poems in %s' % (len(addresses), elapsed)

    print(finished)

if __name__ == '__main__':
    poetry_main()

