import os
import sys

from base import BaseCommand, CommandError
from color import color_style
from optparse import OptionParser
from standalone import ConsoleProgram, ConsoleError

try:
    from importlib import import_module
except ImportError:
    # Not Python 2.7!
    from utils.importlib import import_module

_commands = None # Cache of loaded commands

def get_version(version=None):
    """
    Derives a PEP386-compliant version number
    """
    if version is None:
        return

    assert len(version) == 5
    assert version[3] in ('alpha', 'beta', 'rc', 'final')

    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])

    sub = ''

    if version[3] == 'alpha':
        sub = '.dev[%s]' % version[4]
    elif version[3] != 'final':
        mapping = {'alpha': 'a', 'beta':'b', 'rc':'c'}
        sub = mapping[version[3]] + str(version[4])

    return main + sub

def find_commands(management_dir):
    """
    Given a path to the management directory, returns a list
    of all the command names that are available.

    Returns an empty list of no commands are defined.
    """
    command_dir = os.path.join(management_dir, 'commands')
    try:
        return [fname[:-3] for fname in os.listdir(command_dir)
                if not fname.startswith('_') and f.endswith('.py')]
    except OSError:
        return [ ]

def get_commands(path=None):
    """
    Returns a dictionary mapping command names to their callback class

    The dictionary is in the format {command_name: import_path}

    Commands can be loaded via load_command(command_name)

    The dictionary is cached on first call then reused on subsequent
    commands.
    """
    path = path or __path__
    global _commands
    if _commands is None:
        _commands = dict([(name, __package__) for name in find_commands(path[0])])
    return _commands

def load_command_class(package, name):
    """
    Given a command name, returns the Command class instance. 

    All errors raised by process are allowed to propegate. 
    """
    module = import_module('%s.commands.%s' % (package, name))
    return module.Command()

class LaxOptionParser(OptionParser):
    """
    An option parser that doesn't raise any errors on unknown options.

    From Django
    """
    def error(self, msg):
        pass

    def print_help(self):
        pass

    def print_lax_help(self):
        OptionParser.print_help(self)

    def _process_args(self, largs, rargs, values):
        """
        Overrides OptionParser._process_args to exclusively handle 
        default options, and ignore args and other options.

        Overrides the behavior of super class, which stop parsing at
        the first unrecognized option.
        """
        while rargs:
            arg = rargs[0]
            try:
                if arg[0:2] == "--" and len(arg) > 2:
                    self._process_long_opt(rargs, values)
                elif arg[:1] == "-" and len(arg) > 1:
                    self._process_short_opts(rargs, values)
                else:
                    del rargs[0]
                    raise Exception
            except:
                largs.append(arg)

class ConsoleUtility(object):
    """
    Encapsulates the logic of a command line utility that specifies
    scripted python commands from the commands directory.
    """

    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = os.path.basename(self.argv[0])
        self.style = color_style( )
        self.version = None

    def get_version(self):
        return get_version(self.version)

    def main_help_text(self, commands_only=False):
        """
        Returns the script's main help text, as a string
        """
        if commands_only:
            usage = sorted(get_commands().keys())

        else:
            usage = [
                "",
                self.style.STRONG("Type '%s help <subcommand>' for help on a specific subcommand." 
                    % self.prog_name),
                "",
                "Available subcommands:",
            ]
            for cmd in sorted(get_commands().keys()):
                usage.append("")
                usage.append("\t%s" % cmd)
        return '\n'.join(usage)

    def fetch_command(self, subcommand):
        """
        Tries to fetch the given subcommand, printing a message
        with the appropriate command called from teh command line
        if it can't be found.
        """
        try:
            pkg = get_commands()[subcommand]
        except KeyError:
            sys.stderr.write("Unknown command: %r\nType '%s help' for usage.\n" % \
                (subcommand, self.prog_name))
            sys.exit(1)

        if isinstance(pkg, BaseCommand):
            # Command is already loaded
            klass = pkg
        else:
            klass = load_command_class(pkg, subcommand)
        return klass

    def autocomplete(self):
        pass

    def execute(self):
        """
        Given the command-line arguments, this figures out what subcommand
        is being run, creates a parser appropriate to that command, then
        runs it. 
        """

        parser = LaxOptionParser(usage="%prog subcommand [options] [args]",
                                        version=self.get_version(),
                                        option_list=BaseCommand.opts)
        self.autocomplete()
        try:
            opts, args = parser.parse_args(self.argv)
            handle_default_options(opts)
        except:
            pass # Ignore any option errors at this point

        try:
            subcommand = self.argv[1]
        except IndexError:
            subcommand = 'help' # Display help if no arguments were given

        if subcommand == 'help':
            if len(args) <= 2:
                parser.print_lax_help()
                sys.stdout.write(self.main_help_text() + '\n')
            elif args[2] == '--commands':
                sys.stdout.write(self.main_help_text(commands_only=True) + '\n')
            else:
                self.fetch_command(args[2]).print_help(self.prog_name, args[2])
        elif subcommand == 'version':
            sys.stdout.write(parser.get_version() + '\n')
        elif self.argv[1:] == ['--version']:
            # Option Parser already takes care of printing the version
            pass
        elif self.argv[1:] in (['--help'],['-h']):
            parser.print_lax_help()
            sys.stdout.write(self.main_help_text() + '\n')
        else:
            self.fetch_command(subcommand).load(self.argv)

def execute_console_utility(version=None, argv=None):
    """
    A simple method that runs a management utility
    """
    utility = ConsoleUtility(argv)
    if version:
        utility.version = version
    utility.execute( )
