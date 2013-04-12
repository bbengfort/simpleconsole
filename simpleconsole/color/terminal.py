# console.color.terminal

RESET  = '0'
ANSIGC = '\x1b[%sm'

class TerminalStyle(object):
    
    options     = {'bold':'1', 'underscore':'4', 'blink':'5', 'reverse':'7', 'conceal':'8'}
    color_names = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white')

    @property 
    def foreground(self):
        if not hasattr(self, '_foreground'):
            fgc = dict([(name, '3%i' % i) for i, name in enumerate(self.color_names)])
            setattr(self, '_foreground', fgc)
        return self._foreground

    @property
    def background(self):
        if not hasattr(self, '_background'):
            bgc = dict([(name, '4%i' % i) for i, name in enumerate(self.color_names)])
            setattr(self, '_background', bgc)
        return self._background

    def colorize(self, text='', opts=(), **kwargs):
        """
        Returns your text, enclosed in ANSI graphics codes.

        Depends on the keyword arguments 'fg' and 'bg' and
        the contents of the opts tuple/list. 

        Returns RESET if no parameters are given. 

        Valid colors:
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

        Valid options:
            'bold', 'underscore', 'blink', 'reverse', 'conceal', 'noreset'

        Example:
            print colorize('This is red and bold', fg='red', bg='black', opts=('bold',))
        """
        
        codes = [ ]
        if text == '' and 'noreset' not in opts:
            return ANSIGC % RESET

        fg = kwargs.get('fg', None)
        bg = kwargs.get('bg', None)
        
        if fg: codes.append(self.foreground[fg])
        if bg: codes.append(self.background[fg])

        for opt in opts:
            if opt in self.options:
                codes.append(self.options[opt])

        if 'noreset' not in opts:
            text = text + ANSIGC % RESET

        return (ANSIGC % ';'.join(codes)) + text

    def reset(self):
        return self.colorize( )

    def make_style(self, opts=(), **kwargs):
        """
        Returns a function with default parameters for colorize()

        If no opts or kwargs are provided, returns a function 
        that only returns the text supplied, for the case of a 
        style that requires no styling.

        Example:
            bold_red = make_style(opts=('bold',), fg='red')
            print bold_red('hello')
        """
        if len(kwargs) == 0 and len(opts) == 0:
            return lambda text: text
        return lambda text: self.colorize(text, opts, **kwargs)

class BasePalette(object):
    """
    The interface for defining style definitions. 
    
    Contains a series of configurations, for a palette, and can
    be dynamically constructed at run time. The configuration
    itself is simply a dictionary of the keyword arguments to 
    TerminalStyle.make_style

    Note all styles are in uppercase.
    """

    ERROR    = {}
    WARNING  = {}
    NOTICE   = {}
    STRONG   = {}
    EMPHASIS = {}

    def __init__(self, **kwargs):
        for k,v in kwargs.items( ):
            if isinstance(v, dict):
                setattr(self, k.upper(), v)
            else:
                raise TypeError('Configuration must be a dictionary.')

    @classmethod
    def parse_color_settings(klass, config_string):
        """
        Parse an environment variable to produce the system palette

        The general form of a pallete definition is:
            "role=fg;role=fg/bg;role=fg,option,option;role=fg/bg,option,option"

        where:
            role is a style name such as error or strong
            fg is a foreground color
            bg is a background color
            option is a a display option

        Default roles:
            'error', 'warning', 'notice', 'strong', 'emphasis'

        Valid colors:
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

        Valid options:
            'bold', 'underscore', 'blink', 'reverse', 'conceal'
        """
        if not config_string:
            return klass()

        roles = { }
        parts = config_string.lower().split(';')
        for part in parts:
            if '=' in part:
                definition = { }
                role, instructions = part.split('=')
                role = role.upper( )

                styles = instructions.split(',')
                styles.reverse( )

                colors = styles.pop().split('/')
                colors.reverse( )

                fg = colors.pop( )
                if fg in TerminalStyle.color_names:
                    definition['fg'] = fg
                if colors and colors[-1] in TerminalStyle.color_names:
                    definition['bg'] = colors[-1]

                opts = tuple(s for s in styles if s in TerminalStyle.options.keys())
                if opts:
                    definition['opts'] = opts

                if role and definition:
                    roles[role] = definition

        return klass(**roles)

    def get_style(self):

        terminal = TerminalStyle( )
        attrs = dir(self)
        for attr in attrs:
            if attr.startswith('__'):
                continue

            obj = getattr(self, attr)
            if not callable(obj):
                if isinstance(obj, dict):
                    setattr(terminal, attr, terminal.make_style(**obj))
                else:
                    raise TypeError('The only non-callable, non-builtin properties should be style dicts.')
        return terminal

class NoColorPalette(BasePalette):
    pass

class DefaultPalette(BasePalette):
    
    ERROR    = { 'fg': 'red', 'opts':('bold',) }
    WARNING  = { 'fg': 'yellow', 'opts':('bold',) }
    NOTICE   = { 'fg': 'cyan' }
    STRONG   = { 'fg': 'green' }
    EMPHASIS = { 'opts':('underscore',) }

if __name__ == "__main__":

    style = NoColorPalette( ).get_style( )
    print style.ERROR("The fissionable material has lost containment!")
    print style.WARNING("An astroid is coming towards the earth!")
    print style.NOTICE("I have observed Big Foot.")
    print style.STRONG("Notice me!")
    print style.EMPHASIS("He really said this!")
