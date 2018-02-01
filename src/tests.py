#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# DiAnnotator
#
# Author: Soufian Salim <soufi@nsal.im>
#
# URL: <http://github.com/bolaft/diannotator>

"""
Unit test suite
"""


from unittest import main, TestCase

import colors

from strings import Strings


class TestColors(TestCase):
    def setUp(self):
        self.generated_color = colors.generate_random_color()

    def test_generated_color_length(self):
        self.assertTrue(len(self.generated_color) == 7)

    def test_generated_color_is_code(self):
        self.assertTrue(self.generated_color.startswith("#"))


class TestStrings(TestCase):
    def setUp(self):
        self.strings = Strings()

    def test_data(self):
        self.assertTrue(self.strings.data, list)

    def test_get(self):
        self.strings.data = {
            "test_key": "test_string"
        }

        self.assertIs(self.strings.get("test_key"), "test_string")

    def test_get_with_params(self):
        self.strings.data = {
            "test_key": "test_string_with_param_<?>"
        }

        self.assertEqual(self.strings.get("test_key", "X"), "test_string_with_param_X")


if __name__ == "__main__":
    main()
