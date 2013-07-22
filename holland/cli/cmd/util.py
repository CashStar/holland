"""
holland.cli.cmd.util
~~~~~~~~~~~~~~~~~~~~

Utility classes used by holland.cli.cmd

:copyright: 2008-2011 Rackspace US, Inc.
:license: BSD, see LICENSE.rst for details
"""

from argparse import ArgumentParser

class ArgparseError(Exception):
    """Raise when Argparse runs into an error"""
    def __init__(self, message, status=0):
        Exception.__init__(self, message)
        self.message = message
        self.status = status


class SafeArgumentParser(ArgumentParser):
    """Subclass of argparse.ArgumentParser that does not call sys.exit
    on error
    """

    def error(self, message):
        raise ArgparseError(message)

    def exit(self, status=0, message=None):
        raise ArgparseError(message, status)
