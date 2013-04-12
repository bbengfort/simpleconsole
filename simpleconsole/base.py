"""
Base classes for writing console commands
"""

import os
import sys
import traceback

from color import color_style
from optparse import make_option, OptionParser

def handle_default_options(options):
    """
    Include any default options that all commands should
    accept here.
    """
    if hasattr(options, 'pythonpath'):
        sys.path.insert(0, options.pythonpath)

class CommandError(Exception):
    """
    Exception class indicating a problem while executing
    a console command. 

    If this exception is raised during the execution of
    a command, it will be caught and turned into a nicely
    printed error message to the appropriate output stream
    e.g. stderr. 

    Therefore raising this exception is preferable to other
    exceptions (catching them and raising this error 
    instead).
    """
    pass

class BaseCommand(object):
    """
    The base command from which all console commands are derived.

    The work flow of command parsing and execution is as follows:

    1. The Utility loads the command class and calls it's load method

    2. The load method calls create_parser to get an OptionParser for
       the arguments and then parses them, performs environment 
       changes, then calls execute.

    3. The execute() method attempts to carry out the command by 
       calling the handle() method with the parsed arguments. 
       Any output produced by handle will be printed to stdout

    4. If handle( ) raised a CommandError, execute( ) will print
       the error to stderr. 

    Several attributes affecgt command behavior:
   
    args
        A string listing the arguments accepted by the command, 
        suitable for use in help messages.

    import_django
        A boolean indicating whether the command needs to be able
        to import Django settings. If True, execute( ) will verify
        the Django environment before proceeding.

    help
        A short descripting of the command

    opts
        A list of optparse options which will be fed into the 
        command's OptionParser for parsing arguments.
    """

    opts = (
        make_option('-v', '--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2', '3'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output'),
        make_option('--pythonpath',
            help='A directory to add to the Python path, e.g. "/home/user/projects/myproject/".'),
        make_option('--traceback', action='store_true',
            help='Print traceback on exception'),
    )

    help = ''
    args = ''

    import_django = False

    def __init__(self):
        self.style = color_style( )

    def get_version(self):
        """
        @todo: Each command can have a version, or return the
        main class version.
        """
        if self.version:
            return '.'.join(self.version)
        return "unknown"

    def usage(self, subcommand):
        """
        Return a brief description of how to use the command,
        derived from the attribute self.help
        """
        usage = '%%prog %s [options] %s' % (subcommand, self.args)
        if self.help:
            return '%s\n\n%s' % (usage, self.help)
        else:
            return usage

    def create_parser(self, prog_name, subcommand):
        """
        Create and return the OptionParser which will be used
        to parse the arguments to the command.
        """
        opkw = {
            'prog':        prog_name,
            'usage':       self.usage(subcommand),
            'version':     self.get_version( ),
            'option_list': self.opts,
        }
        return OptionParser(**opkw)

    def print_help(self, prog_name, subcommand):
        """
        Print the help message for this command, from self.usage( )
        """
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help( )

    def load(self, argv):
        """
        Setup the environment, either Python or Django,
        then run this command.
        """
        parser = self.create_parser(argv[0], argv[1])
        opts, args = parser.parse_args(argv[2:])
        handle_default_options(opts)
        self.execute(*args, **opts.__dict__)

    def execute(self, *args, **opts):
        """
        Try to execute this command.
        """
        show_traceback = opts.get('traceback', False)

        try:
            self.stdin  = opts.get('stdin', sys.stdin)
            self.stdout = opts.get('stdout', sys.stdout)
            self.stderr = opts.get('stderr', sys.stderr)

            output = self.handle(*args, **opts)

            if output:
                self.stdout.write(output)
        except CommandError, e:
            if show_traceback:
                traceback.print_exc()
            else:
                self.stderr.write(self.style.ERROR('Error: %s\n' % e))
            sys.exit(1)

    def handle(self, *args, **opts):
        """
        The actual logic of the command, subclasses must implement.
        """
        raise NotImplementedError( )

class LabelCommand(BaseCommand):
    """
    A command which takes one ore more arbitraty arguments on the
    command line, and does something with each of the them. 

    Rather than implement handle( ), subclasses must implement 
    handle_label(), which will be called once for each label.
    """

    args  = '<label label ...>'
    label = 'label'

    def handle(self, *lables, **opts):
        if not labels:
            raise CommandError('Enter at least one %s.' % self.label)

        output = [ ]

        for label in labels:
            label_output = self.handle_label(label, **opts)
            if label_output:
                output.append(label_output)
        return '\n'.join(output)

    def handle_label(self, label, **opts):
        """
        Perform the command's action for label which will be 
        the string as given on the command line.
        """
        raise NotImplementedError()

class NoArgsCommand(BaseCommand):
    """
    A command which takes no arguments on the command line.

    Rather than implementing handle(), subclasses must implement
    handle_noargs, to ensure no args are passed on the command line. 

    Attempting to pass arguments will raise CommandError
    """
    args = ''

    def handle(self, *args, **opts):
        if args:
            raise CommandError("Command doesn't accept any arguments.")
        return self.handle_noargs(**opts)

    def handle_noargs(self, **opts):
        """
        Perform this command's actions
        """
        raise NotImplementedError()
