#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import doctest
import sys

from optparse import OptionParser

from annotator import Annotator

APP_TITLE = "DiAnnotator"  # hardcoded game title
VERSION_NUMBER = "alpha 17.10.6"  # hardcoded version number


def parse_args():
    """
    Parses command line options and arguments
    """
    op = OptionParser(usage="usage: %prog [opts]")

    op.add_option(
        "-t", "--test",
        dest="test",
        default=False,
        action="store_true",
        help="executes the test suite")

    op.add_option(
        "-f", "--fullscreen",
        dest="fullscreen",
        default=False,
        action="store_true",
        help="starts the game in fullscreen mode")

    op.add_option(
        "-v", "--version",
        dest="version",
        default=False,
        action="store_true",
        help="displays the current version of the game")

    return op.parse_args()

if __name__ == "__main__":
    options, arguments = parse_args()

    if options.test:
        doctest.testmod()  # unit testing
        sys.exit()

    if options.version:
        sys.exit("{} {}".format(APP_TITLE, VERSION_NUMBER))

    # creates the game engine
    annotator = Annotator()

    if options.fullscreen:
        annotator.toggle_fullscreen()  # toggles fullscreen

    annotator.parent.protocol("WM_DELETE_WINDOW", annotator.quit)  # quit event handler
    annotator.mainloop()  # runs the main tkinter loop
