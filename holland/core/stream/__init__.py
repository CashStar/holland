"""
    holland.core.stream
    ~~~~~~~~~~~~~~~~~~~

    Stream plugin API for Holland.

    Stream plugins provide a way to transform output of file or file-like
    objects. This generally means redirecting output of some command through
    compression or encryption filters through a standard API.

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

from holland.core.stream.plugin import open_stream, open_stream_wrapper, \
                                       available_methods, \
                                       load_stream_plugin, \
                                       StreamPlugin, StreamError
from holland.core.stream.base import FileLike, RealFileLike

# ensure compression is registered with the plugin api
from . import compression
del compression

__all__ = [
    'open_stream',
    'open_stream_wrapper',
    'available_methods',
    'load_stream_plugin',
    'StreamPlugin',
    'StreamError',
]
