"""
Todo: refactor the daemon command so that the execute is a jumptable, e.g. 

start -> method
restart -> method
stop -> method
status -> method

etc. 
"""

import os
import sys
import time
import atexit
import traceback

from signal import SIGTERM
from optparse import make_option
from simpleconsole import ConsoleProgram, ConsoleError

class DaemonProgram(ConsoleProgram):
    """
    A command that runs in the background and includes special methods for
    handling stdin, stdout, and stderr. A special requirement of this type
    of command is a location for a pidfile to be written to. So the 
    interface for DaemonPrograms is slightly different. 

    Also note that the handle method will execute run or a function.
    """
    
    opts = (
        make_option('--traceback', action='store_true', help='Print traceback on exception'),
    )

    help = "A Daemon process"
    args = "start|stop|restart"

    def __init__(self, pidfile, **kwargs):
        """
        The init of a Daemon Command can take the path for a process id
        file (pid), otherewise the pid will be in /var/run and the name of
        the file will be the name of the Command.
        """
        super(DaemonProgram, self).__init__()
        self.pidfile = pidfile

        # The standard file descriptors can also be set as kwargs
        self.stdin  = kwargs.pop('stdin', '/dev/null')
        self.stdout = kwargs.pop('stdout', '/dev/null')
        self.stderr = kwargs.pop('stderr', '/dev/null')

    def daemonize(self):
        """
        Do the UNIX double-fork magic. See Stevens' Advanced Programming
        in the UNIX Environment for details. (ISBN 0201563177)
        """

        # Perform first fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                sys.exit(0)
        except OSError as e:
            raise ConsoleError("Fork #1 failed: %s" % str(e))

        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # Perform second fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent
                sys.exit(0)
        except OSError as e:
            raise ConsoleError("Fork #2 failed: %s" % str(e))

        # Test ability to write to pidfile
        self.testpid()

        # Redirect standard file descriptors 
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile and cleanup
        atexit.register(self.cleanup)
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as pidfile:
            pidfile.write("%s\n" % pid)

    def testpid(self):
        try:
            with open(self.pidfile, 'w+') as pidfile:
                pidfile.write("test\n")
            os.remove(self.pidfile)
            return True
        except IOError as e:
            raise ConsoleError("Cannot write to pidfile %s: %s" % (self.pidfile, str(e)))

    def cleanup(self):
        """
        Cleanup the process atexit.
        """
        os.remove(self.pidfile)

    def getpid(self):
        """
        Reads the pidfile if it exists and returns the pid or None.
        """
        try:
            with open(self.pidfile, 'r') as pidfile:
                return int(pidfile.read().strip())
        except IOError:
            return None

    def start(self, **opts):
        """
        Start the daemon.
        """

        if self.getpid() is not None:
            message = "A pidfile %s already exists. Perhaps the Daemon is already running?"
            raise ConsoleError(message % self.pidfile)
        else:
            self.daemonize()
            self.handle_daemon(**opts)

    def stop(self, **opts):
        """
        Stops the daemon
        """

        # Get the pid from the pidfile
        pid = self.getpid()

        if pid is None:
            message = "The pidfile %s does not exist. Perhaps the Daemon is not running?"
            raise ConsoleError(message % self.pidfile)
        
        # Attempt to kill the Daemon process
        try:
            while True:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as error:
            if str(error).find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                raise ConsoleError(str(error))

    def restart(self, **opts):
        """
        Restart the daemon
        """
        self.stop(**opts)
        self.start(**opts)

    def execute(self, *args, **opts):
        """
        Handles the execution of the program with correct passing of
        standard file desriptors, unlike the super class, which doesn't
        expect immediate passing to /dev/null.
        """
        self.stdin  = opts.get('stdin', self.stdin)
        self.stdout = opts.get('stdout', self.stdout)
        self.stderr = opts.get('stderr', self.stderr) 

        show_traceback = opts.get('traceback', False)

        try:
            output = self.handle(*args, **opts)

            if output:
                self.stdout.write(output)
                self.stdout.write("\n")
                self.stdout.flush()
        except ConsoleError as e:
            if show_traceback:
                traceback.print_exc()
            sys.stderr.write(self.style.ERROR("Error: %s\n" % str(e)))
            sys.stderr.flush()
            sys.exit(1)

    def handle(self, *args, **opts):
        """
        Checks the last argument for a daemon command - start, stop, or 
        restart and then passes the control to the correct method for that
        argument. In the case of start and restart, the arguments are
        passed through because start calls handle_daemon which is the same
        as the run command on a thread. 
        """
        jumptable = {
            'start':   self.start,
            'stop':    self.stop,
            'restart': self.restart,
        }

        if len(args) != 1:
            raise ConsoleError("Expected only Daemon argument - %s" % args)
        else:
            if args[0] in jumptable:
                return jumptable[args[0]](**opts)
            else:
                raise ConsoleError("Unknown Daemon arg '%s' as command argument" % args[0])

        return None

    def handle_daemon(self, **opts):
        """
        This is the method that should be overrode instead of handle.
        """
        raise NotImplementedError("Must override this method when DaemonProgram is subclassed.")

if __name__ == "__main__":

    class TestDaemon(DaemonProgram):
        
        opts = DaemonProgram.opts + (
            make_option('-w', dest='logfile', action='store', default='/dev/null', metavar='PATH', help="Path to a log file to write to."),
        )

        def log(self, entry):
            with open(self.logfile, 'a+') as out:
                out.write("This is entry number %i\n" % entry)

        def handle_daemon(self, **opts):
            
            self.logfile = opts.get('logfile', '/dev/null')

            start = 0
            while start < 100:
                self.log(start)
                start += 1 
                time.sleep(5)

    TestDaemon(pidfile="/Users/benjamin/Desktop/test.pid").load(sys.argv)
