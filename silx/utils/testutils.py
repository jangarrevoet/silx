# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2016-2017 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""Utilities for writing tests.

- :class:`ParametricTestCase` provides a :meth:`TestCase.subTest` replacement
  for Python < 3.4
- :class:`TestLogging` with context or the :func:`test_logging` decorator
  enables testing the number of logging messages of different levels.
"""

__authors__ = ["T. Vincent"]
__license__ = "MIT"
__date__ = "17/01/2018"


import contextlib
import functools
import logging
import sys
import unittest

_logger = logging.getLogger(__name__)


if sys.hexversion >= 0x030400F0:  # Python >= 3.4
    class ParametricTestCase(unittest.TestCase):
        pass
else:
    class ParametricTestCase(unittest.TestCase):
        """TestCase with subTest support for Python < 3.4.

        Add subTest method to support parametric tests.
        API is the same, but behavior differs:
        If a subTest fails, the following ones are not run.
        """

        _subtest_msg = None  # Class attribute to provide a default value

        @contextlib.contextmanager
        def subTest(self, msg=None, **params):
            """Use as unittest.TestCase.subTest method in Python >= 3.4."""
            # Format arguments as: '[msg] (key=value, ...)'
            param_str = ', '.join(['%s=%s' % (k, v) for k, v in params.items()])
            self._subtest_msg = '[%s] (%s)' % (msg or '', param_str)
            yield
            self._subtest_msg = None

        def shortDescription(self):
            short_desc = super(ParametricTestCase, self).shortDescription()
            if self._subtest_msg is not None:
                # Append subTest message to shortDescription
                short_desc = ' '.join(
                    [msg for msg in (short_desc, self._subtest_msg) if msg])

            return short_desc if short_desc else None


class TestLogging(logging.Handler):
    """Context checking the number of logging messages from a specified Logger.

    It disables propagation of logging message while running.

    This is meant to be used as a with statement, for example:

    >>> with TestLogging(logger, error=2, warning=0):
    >>>     pass  # Run tests here expecting 2 ERROR and no WARNING from logger
    ...

    :param logger: Name or instance of the logger to test.
                   (Default: root logger)
    :type logger: str or :class:`logging.Logger`
    :param int critical: Expected number of CRITICAL messages.
                         Default: Do not check.
    :param int error: Expected number of ERROR messages.
                      Default: Do not check.
    :param int warning: Expected number of WARNING messages.
                        Default: Do not check.
    :param int info: Expected number of INFO messages.
                     Default: Do not check.
    :param int debug: Expected number of DEBUG messages.
                      Default: Do not check.
    :param int notset: Expected number of NOTSET messages.
                       Default: Do not check.
    :raises RuntimeError: If the message counts are the expected ones.
    """

    def __init__(self, logger=None, critical=None, error=None,
                 warning=None, info=None, debug=None, notset=None):
        if logger is None:
            logger = logging.getLogger()
        elif not isinstance(logger, logging.Logger):
            logger = logging.getLogger(logger)
        self.logger = logger

        self.records = []

        self.count_by_level = {
            logging.CRITICAL: critical,
            logging.ERROR: error,
            logging.WARNING: warning,
            logging.INFO: info,
            logging.DEBUG: debug,
            logging.NOTSET: notset
        }

        super(TestLogging, self).__init__()

    def __enter__(self):
        """Context (i.e., with) support"""
        self.records = []  # Reset recorded LogRecords
        self.logger.addHandler(self)
        self.logger.propagate = False
        # ensure no log message is ignored
        self.entry_level = self.logger.level * 1
        self.logger.setLevel(logging.DEBUG)

    def __exit__(self, exc_type, exc_value, traceback):
        """Context (i.e., with) support"""
        self.logger.removeHandler(self)
        self.logger.propagate = True
        self.logger.setLevel(self.entry_level)

        for level, expected_count in self.count_by_level.items():
            if expected_count is None:
                continue

            # Number of records for the specified level_str
            count = len([r for r in self.records if r.levelno == level])
            if count != expected_count:  # That's an error
                # Resend record logs through logger as they where masked
                # to help debug
                for record in self.records:
                    self.logger.handle(record)
                raise RuntimeError(
                    'Expected %d %s logging messages, got %d' % (
                        expected_count, logging.getLevelName(level), count))

    def emit(self, record):
        """Override :meth:`logging.Handler.emit`"""
        self.records.append(record)


def test_logging(logger=None, critical=None, error=None,
                 warning=None, info=None, debug=None, notset=None):
    """Decorator checking number of logging messages.

    Propagation of logging messages is disabled by this decorator.

    In case the expected number of logging messages is not found, it raises
    a RuntimeError.

    >>> class Test(unittest.TestCase):
    ...     @test_logging('module_logger_name', error=2, warning=0)
    ...     def test(self):
    ...         pass  # Test expecting 2 ERROR and 0 WARNING messages

    :param logger: Name or instance of the logger to test.
                   (Default: root logger)
    :type logger: str or :class:`logging.Logger`
    :param int critical: Expected number of CRITICAL messages.
                         Default: Do not check.
    :param int error: Expected number of ERROR messages.
                      Default: Do not check.
    :param int warning: Expected number of WARNING messages.
                        Default: Do not check.
    :param int info: Expected number of INFO messages.
                     Default: Do not check.
    :param int debug: Expected number of DEBUG messages.
                      Default: Do not check.
    :param int notset: Expected number of NOTSET messages.
                       Default: Do not check.
    """
    def decorator(func):
        test_context = TestLogging(logger, critical, error,
                                   warning, info, debug, notset)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with test_context:
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


# Simulate missing library context
class EnsureImportError(object):
    """This context manager allows to simulate the unavailability
    of a library, even if it is actually available. It ensures that
    an ImportError is raised if the code inside the context tries to
    import the module.

    It can be used to test that a correct fallback library is used,
    or that the expected error code is returned.

    Trivial example::

        from silx.utils.testutils import EnsureImportError

        with EnsureImportError("h5py"):
            try:
                import h5py
            except ImportError:
                print("Good")

    .. note::

        This context manager does not remove the library from the namespace,
        if it is already imported. It only ensures that any attempt to import
        it again will cause an ImportError to be raised.
    """
    def __init__(self, name):
        """

        :param str name: Name of module to be hidden (e.g. "h5py")
        """
        self.module_name = name

    def __enter__(self):
        """Simulate failed import by setting sys.modules[name]=None"""
        if self.module_name not in sys.modules:
            self._delete_on_exit = True
            self._backup = None
        else:
            self._delete_on_exit = False
            self._backup = sys.modules[self.module_name]
        sys.modules[self.module_name] = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore previous state"""
        if self._delete_on_exit:
            del sys.modules[self.module_name]
        else:
            sys.modules[self.module_name] = self._backup