"""
This program is used to schmooze formats from firefox and add new ones
"""
from ._firefoxFormats import *

if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))