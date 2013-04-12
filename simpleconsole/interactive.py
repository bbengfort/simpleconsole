"""
Framework for creating command line programs with an interactive prompt. 
"""

import re
import sys
import getopt
import traceback
import readline
import rlcompleter

from base import CommandError, BaseCommand

class InteractiveError(CommandError):
    pass

class InteractiveCommand:
    """
    Base class for all commands to be added to the Interactive Shell. This is
    essentially an empty shell class that provides an interface to methods that
    must be implemented for all children. If not implemented, a
    C{NotImplementedError} is raised. 
    """

    def get_name(self):
        """
        Getter method for the name of the command- by implementing this method,
        you will set the command name utilized by L{InteractiveShell}. This
        prevents use of a named attribute for the class. 
        
        Usage: C{return 'name'}
        
        @return: The name of the command
        @rtype: C{str}
        """
        raise NotImplementedError, 'Must implement'

    def get_options(self):
        """
        Getter method for the options that manipulate the execution of the
        command. By implementing this method you will set the options of the
        command that are parsed by the interpreter.
        
        The options dictionary is constructed with the name of the option (the
        longopt format is the default) as the key. If the option is a flag or
        required, then set the value to C{None}, else, set it to the default
        value. If the option takes an argument, ensure '=' is appended to the
        option name. 
        
        Usage: C{return {'opt1': None, 'opt2=': 'default', 'required=': None}}
        
        @return: The options dictionary, constructed as described above.
        @rtype: C{dict}
        """
        raise NotImplementedError, 'Must implement'

    def handle_command(self, opts, args):
        """
        Called by L{InteractiveShell} when it recieves the name of the command,
        identified by L{get_name}. This method is essentially the worker task of
        the command and is the entrance point for specific program logic.
        
        @param opts: The result of L{get_option_dict}, whose keys are taken from L{get_options}
        @type opts: C{dict}
        @param args: The raw string passed to the command, useful for debugging or capturing non-option args
        @type args: C{str}
        """
        raise NotImplementedError, 'Must implement'

    def get_short_description(self):
        """
        Getter method for the short description of the command. Usually just a
        brief sentence about what the command will do, and what it expects.
        
        @note: Called by L{InteractiveShell} C{help} command, which lists all
        available commands and their descriptions. 
        
        @return: A short description of the command and what it does
        @rtype: C{str}
        """
        return 'No description'
    
    def get_help_message(self):
        """
        Getter method for the usage and instruction of using a command. This is
        a longer docstring that describes the command, the operation of the
        command, usage instructions, and all available options and arguments the
        command will take.
        
        @note: Called by L{InteractiveShell} C{help command} -- returns the
        specific usage instructions for C{command}
        
        @return: The long description of the command including usage and arguments.
        @rtype: C{docstr}
        """
        return 'No help available'


class CustomCompleter(rlcompleter.Completer):
    """
    A custom implementation of global_matches from the rlcompleter module that
    will NOT use __builtin__.__dict__ and python language keywords for
    completion.
    
    @bug: Works?
    
    @todo: Implement doctesting
    """

    def global_matches(self, text):
        """
        Overrides C{rlcompleter.Completer.global_matches} to ignore builtins and
        python language keywords for completion. Computes matches when text is
        a simple name.
        
        @param text: A simple name to be matched in C{self.namespace}
        @type text: C{str}
        
        @return: A list of all keywords, names defined in C{self.namespace} that match
        @rtype: C{list}
        """
        matches = []
        n = len(text)
        for word, val in self.namespace.items():
            if word[:n] == text and word != "__builtins__":
                matches.append(self._callable_postfix(val, word))
        return matches
    
###################################################################### 
## Interactive Shell & Built-In Commands
###################################################################### 

class InteractiveShell:
    """
    Gives the user a custom prompt and the ability to type built in commands to
    the interactive console. This class represents the core of the console
    program, and must contain one or more L{InteractiveCommand}s to provide
    functionality to the user.
    
    @ivar banner: The message to be displayed at the top of the shell, right after the program starts
    @type banner: C{str}
    @ivar prompt: A string that is displayed to the user while awaiting commands
    @type prompt: C{str}
    @ivar commands: A dictionary of available commands, where the key is the command name and the value is the command object
    @type commands: C{dict}
    
    @cvar _HelpCommand: Prints a list of available commands and their descriptions, or the help text of a specific command
    @type _HelpCommand: L{InteractiveCommand}
    @cvar _ExitCommand: Exits the interactive shell
    @type _ExitCommand: L{InteractiveCommand}
    """

    ###################################################################### 
    ## Built-In Commands
    ###################################################################### 

    class _HelpCommand(InteractiveCommand):
        """
        Prints a list of available commands and their descriptions, or the help
        text of a specific command. Requires a list of the available commands in
        order to display text for them. 
        
        @ivar commands: A dictionary of available commands, bound to L{InteractiveShell.commands}
        @type commands: C{dict}
        """
        def __init__(self, commands):
            """
            Constructor function for L{_HelpCommand}.
            
            @param commands: A dictionary of available commands, usually L{InteractiveShell.commands}
            @type commands: C{dict}
            """
            self.commands = commands

        def get_name(self):
            return 'help'
    
        def get_options(self):
            return { }

        def handle_command(self, opts, args):
            """
            Prints a list of available commands and their descriptions if no
            argument is provided. Otherwise, prints the help text of the named
            argument that represents a command. Does not throw an error if the
            named argument doesn't exist in commands, simply prints a warning.
            
            @param opts: Will be an empty dictionary
            @type opts: C{dict}
            @param args: The raw string passed to the command, either a command or nothing
            @type args: C{str}
            
            @return: Returns nothing, sends messages to stdout
            @rtype: None
            """
            if len(args) == 0:
                self.do_command_summary( )
                return

            if args[0] not in self.commands:
                print 'No help available for unknown command "%s"' % args[0]
                return
            
            print self.commands[args[0]].get_help_message( )
            

        def do_command_summary(self):
            """
            If no command is given to display help text for specifically, then
            this helper method is called to print out a list of the available
            commands and their descriptions. Iterates over the list of commands,
            and gets their summary from L{InteractiveCommand.get_short_description}
            
            @return: Returns nothing, sends messages to stdout
            @rtype: C{None}
            """
            print 'The following commands are available:\n'
            cmdwidth = 0
            for name in self.commands.keys( ):
                if len(name) > cmdwidth:
                    cmdwidth = len(name)

            cmdwidth += 2
            for name in sorted(self.commands.keys( )):
                command = self.commands[name]

                if name == 'help':
                    continue
                
                print '  %s   %s' % (name.ljust(cmdwidth),
                                     command.get_short_description( ))
                

        def get_short_description(self):
            return ''
    
        def get_help_message(self):
            return ''

    class _ExitCommand(InteractiveCommand):
        """
        Exits the interactive shell. 
        """
        def get_name(self):
            return 'exit'

        def get_options(self):
            return { }

        def handle_command(self, opts, args):
            sys.exit(0)


        def get_short_description(self):
            return 'Exit the program.'
    
        def get_help_message(self):
            return 'Type exit and the program will exit.  There are no options to this command'

    ###################################################################### 
    ## InteractiveShell Methods
    ######################################################################

    def __init__( self, 
                  banner="Welcome to Interactive Shell",
                  prompt=" >>> "):
        self.banner = banner
        self.prompt = prompt
        self.commands = { }

        helpcmd = InteractiveShell._HelpCommand(self.commands)
        exitcmd = InteractiveShell._ExitCommand( )

        self.add_command(helpcmd)
        self.add_command(exitcmd)

    def add_command(self, command):
        """
        Adds a command to the interactive shell. This should be called before
        L{InteractiveShell.run} in order to give the user some useful commands!
        
        @param command: A command to be added to the interactive shell.
        @type command: L{InteractiveCommand}
        
        @return: Returns nothing, modifies the L{InteractiveShell} in place
        @rtype: C{None}
        """
        if command.get_name( ) in self.commands:
            raise Exception, 'command %s already registered' % command.get_name( )
        
        self.commands[command.get_name( )] = command

    def handle_input(self, input):
        """
        Worker task of the L{InteractiveShell} - takes the user input and
        parses it for commands, options, and arguments, calls the command with
        its correct arguments.
        
        @note: This method is called by L{InteractiveShell.run} method
        
        @param input: The raw string input from the prompt line.
        @type input: C{str}
        
        @return: Returns nothing, operational method
        @rtype: C{None}
        """
        input = input.strip( )

        if input == '':
            print
            return

        # Split the input to allow for quotes option values
        args = re.findall('\-\-\S+\=\"[^\"]*\"|\S+',input)
        
        command = args[0]
        args = args[1:]

        # strip off quotes from args if present
        for i in xrange(0, len(args)):
            parts = args[i].split('=')
            if len(parts) != 2:
                continue

            if len(parts[1]) < 2:
                continue

            if ( parts[1][0] != '"' or
                 parts[1][-1] != '"'):
                continue

            parts[1] = parts[1][1:-1]
            args[i] = '='.join(parts)

        
        if not command in self.commands:
            print 'Unknown command: "%s". Type "help" for a list of commands.' % command
            return
                
        command = self.commands[command]

        if len(command.get_options( )) > 0:
            opts = get_option_dict(args, command.get_options( ).keys( ))
            if opts == None:
                print ('Invalid command or option supplied '
                '(use "help <command>" for usage).')
                return
        else:
            opts = { }
            
        for option, default in command.get_options( ).items( ):
            if option.endswith('='):
                option_name = option[:-1]
            else:
                option_name = option

            if ( default != None and
                 option.endswith('=') and
                 option_name not in opts):
                opts[option_name] = default

            elif ( option_name not in opts and
                   default == None and
                   option.endswith('=') ):
                print 'Error: must supply a value for option "%s"' % option_name
                return
            
        try:
            command.handle_command(opts, args)
        except Exception, e:
            print "Exception occurred while processing command."
            traceback.print_exc( )

    def run(self):
        """
        Starts up the L{InteractiveShell} with the correct command prompt,
        completer, and banner; then listens for commands from the user and
        executes them when it receives them.
        
        @return: Returns nothing, operational method
        @rtype: C{None}
        """
        namespace = { }
        
        
        for name,command in self.commands.items( ):
            namespace[name] = None
            for option in command.get_options( ):
                namespace[option] = None

        readline.set_completer( CustomCompleter(namespace).complete )

        readline.parse_and_bind("tab: complete")
            
        print self.banner
        print
        print 'Type "help" at any time for a list of commands.'

        while True:
            try:
                print
                input = raw_input(self.prompt)
            except (KeyboardInterrupt, EOFError):
                break

            self.handle_input(input)

###################################################################### 
## Main Method (i.e. Testing)
###################################################################### 

if __name__ == '__main__':

    class TestCommand(InteractiveCommand):
        
        def get_name(self):
            return 'test'

        def get_options(self):
            return { 'opt1': None,
                     'opt2=': 'default',
                     'required=': None}

        def handle_command(self, opts, args):
            print 'Test command running with options:'

            for k,v in opts.items( ):
                print '%s => %s' % (str(k), str(v))
            
            print 'Args is: %s' % args
            
        def get_short_description(self):
            return 'I am a test command hear me roar'

        def get_help_message(self):
            return 'test --opt1=value [--opt2=value2]'

        
    tc = TestCommand( )

    shell = InteractiveShell( banner='Welcome to TestLand',
                           prompt=' TEST >>> ')

    shell.add_command(tc)

    shell.run( )
        
                    
                    
