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
__authors__ = ["T. Vincent", "P. Knobel"]
__license__ = "MIT"
__date__ = "05/01/2017"


import logging
import os
import sys
import unittest


_logger = logging.getLogger(__name__)


def suite():

    test_suite = unittest.TestSuite()

    if sys.platform.startswith('linux') and not os.environ.get('DISPLAY', ''):
        # On Linux and no DISPLAY available (e.g., ssh without -X)
        _logger.warning('silx.gui tests disabled (DISPLAY env. variable not set)')

        class SkipGUITest(unittest.TestCase):
            def runTest(self):
                self.skipTest(
                    'silx.gui tests disabled (DISPLAY env. variable not set)')

        test_suite.addTest(SkipGUITest())
        return test_suite

    elif os.environ.get('WITH_QT_TEST', 'True') == 'False':
        # Explicitly disabled tests
        _logger.warning(
            "silx.gui tests disabled (env. variable WITH_QT_TEST=False)")

        class SkipGUITest(unittest.TestCase):
            def runTest(self):
                self.skipTest(
                    "silx.gui tests disabled (env. variable WITH_QT_TEST=False)")

        test_suite.addTest(SkipGUITest())
        return test_suite

    # Import here to avoid loading QT if tests are disabled

    from ..plot import test as test_plot
    from ..fit import test as test_fit
    from ..hdf5 import test as test_hdf5
    from ..widgets import test as test_widgets
    from ..plot3d import test as test_plot3d
    from ..data import test as test_data
    from . import test_qt
    from . import test_console
    from . import test_icons

    test_suite.addTest(test_qt.suite())
    test_suite.addTest(test_plot.suite())
    test_suite.addTest(test_fit.suite())
    test_suite.addTest(test_hdf5.suite())
    test_suite.addTest(test_widgets.suite())
    test_suite.addTest(test_console.suite())
    test_suite.addTest(test_icons.suite())
    test_suite.addTest(test_plot3d.suite())
    test_suite.addTest(test_data.suite())
    return test_suite
