#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# DiAnnotator
#
# Author: Soufian Salim <soufi@nsal.im>
#
# URL: <http://github.com/bolaft/diannotator>

"""
Config file manager
"""

import os

from configparser import ConfigParser

# check if the current file is in a folder name "src"
EXEC_FROM_SOURCE = os.path.dirname(os.path.abspath(__file__)).split("/")[-1] == "src"


class ConfigFile(ConfigParser):
    """
    Manages an INI file
    """
    file_name = "config.ini"
    directory = "../" if EXEC_FROM_SOURCE else "./"

    def __init__(self):
        """
        Builds paths to INI folder and file and creates the directory if necessary
        """
        self.file = "{}/{}".format(self.directory, self.file_name)
        ConfigParser.__init__(self)

        self.read(self.file)

    def get_string(self, key, default):
        """
        Returns an string value from the configuration file
        """
        for section in self.sections():
            try:
                return ConfigParser.get(self, section, key)
            except Exception:
                pass

        return default

    def get_float(self, key, default):
        """
        Returns a float value from the configuration file
        """
        for section in self.sections():
            try:
                return ConfigParser.getfloat(self, section, key)
            except Exception:
                pass

        return default

    def get_int(self, key, default):
        """
        Returns an integer value from the configuration file
        """
        for section in self.sections():
            try:
                return ConfigParser.getint(self, section, key)
            except Exception:
                pass

        return default

    def get_bool(self, key, default):
        """
        Returns an value from the configuration file
        """
        for section in self.sections():
            try:
                return ConfigParser.getboolean(self, section, key)
            except Exception:
                pass

        return default
