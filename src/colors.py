# DiAnnotator
#
# Author: Soufian Salim <soufi@nsal.im>
#
# URL: <http://github.com/bolaft/diannotator>

"""
Color functions
"""

import random


def generate_random_color():
    """
    Generates the hexadecimal code of a random pastel color
    """
    r = (random.randrange(1, 256) + 255) / 2
    g = (random.randrange(1, 256) + 255) / 2
    b = (random.randrange(1, 256) + 255) / 2

    return '#%02x%02x%02x' % (r, g, b)
