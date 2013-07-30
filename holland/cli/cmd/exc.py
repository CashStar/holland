"""
holland.cli.error
~~~~~~~~~~~~~~~~~

Standard exception classes raised by the holland.cli.cmd api

:copyright: 2008-2011 Rackspace US, Inc.
:license: BSD, see LICENSE.rst for details
"""

class CommandError(Exception):
    """Base exception class for command errors"""


class CommandNotFoundError(CommandError):
    """Raised when a command could not be loaded"""
    def __init__(self, name):
        self.name = name
        CommandError.__init__(self, name)

    def __str__(self):
        "Provide a reasonable default error message"
        return "'%s' is not a valid command" % self.name


class CommandRuntimeError(CommandError):
    """Raised when an unexpected exception occurs when running a command"""
