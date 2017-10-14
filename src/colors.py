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
    # generates random RGB
    r = (random.randrange(1, 256) + 255) / 2
    g = (random.randrange(1, 256) + 255) / 2
    b = (random.randrange(1, 256) + 255) / 2

    # clamp function
    clamp = lambda x: int(max(0, min(x, 255)))

    # returns hexadecimal color code
    return "#{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))
