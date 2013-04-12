"""
Sets up a terminal color scheme-- learned from Django.
"""

import os
import sys
import terminal

def supports_color():
    """
    Returns True if the system's terminal supports color.
    """
    unsupported = (sys.platform in ('win32', 'Pocket PC'))
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    if unsupported or not is_a_tty:
        return False
    return True

def color_style():
    """
    Returns a style object with the color scheme
    """

    if not supports_color():
        palette = NoColorPalette( )
    else:
        COLORS = os.environ.get('COLORS', None)
        if COLORS:
            palette = terminal.DefaultPalette.parse_color_settings(COLORS)
        else:
            palette = terminal.DefaultPalette( )
    return palette.get_style( )

def no_style( ):
    """
    Return an instance of NoColorPalette.get_style( )
    """
    return terminal.NoColorPalette( ).get_style( )
