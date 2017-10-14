#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# DiAnnotator
#
# Author: Soufian Salim <soufi@nsal.im>
#
# URL: <http://github.com/bolaft/diannotator>

"""
Strings manager
"""

import codecs
import json


class Strings():
    """
    Used to convert string keys to formatted strings
    """
    language = "en"
    file_path = "../lan/{}.json".format(language)

    def __init__(self):
        """
        Initializes string list
        """
        self.data = json.loads(codecs.open(self.file_path, encoding="utf-8").read())

    def get(self, key, *params):
        """
        Returns a formatted string
        """
        if key in self.data:
            text = self.data[key]

            return text.replace("<?>", "{}").format(*params)
        else:
            return key
