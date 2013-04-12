#!/usr/bin/env python

import sys

from optparse import make_option
from simpleconsole import ConsoleProgram, ConsoleError

class ExampleProgram(ConsoleProgram):
    
    args = "<arg arg ...>"
    help = "A test program to show how python command line programs can be written with simpleconsole"

    opts = ConsoleProgram.opts + (
        make_option('-c', '--colorize', default=False, action="store_true",
            help="An option added in the test program"),
        make_option('-e', '--error', default=False, action="store_true",
            help="Raise an artificial error"),
    )

    version = ('1', '0')

    def handle(self, *args, **opts):
        """
        This is the thing that needs to be overriden to do all the work! The args
        are the args from the command line, and the opts is a dictionary of the
        options specified by the opts property and make_option!
        """

        if opts.get('error', False):
            raise ConsoleError("Stop execution of program by raising console error")

        output = [
            'Test program running....',
            'Args are: %s' % ', '.join(args),
            'Opts are:',
        ]

        output.extend(['\t%s: %s' % item for item in opts.items()])
        output.append('')

        if opts.get('colorize', False):
            output.append('Output can be colorized with the style property')
            output.append('')
            return self.style.STRONG('\n'.join(output))

        # Return output, but keep in mind, you need to append a new line!
        # You can also issue print statements, then return empty string or None
        return '\n'.join(output)

if __name__ == "__main__":
    # To execute your program, ensure you have these lines included! 
    ExampleProgram().load(sys.argv)
