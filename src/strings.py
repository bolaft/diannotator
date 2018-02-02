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
import locale

from os import path


class Strings():
    """
    Used to convert string keys to formatted strings
    """
    default_locale = "en_US"

    file_path = "../lan/{}.json"

    def __init__(self):
        """
        Initializes string list
        """
        loc = locale.getlocale()[0]

        if path.exists(self.file_path.format(loc)):
            json_path = self.file_path.format(loc)
        else:
            json_path = self.file_path.format(self.default_locale)

        with codecs.open(json_path, encoding="utf-8") as f:
            self.data = json.loads(f.read())

    def get(self, key, *params):
        """
        Returns a formatted string
        """
        if key in self.data:
            text = self.data[key]

            return text.replace("<?>", "{}").format(*params)

        return key
