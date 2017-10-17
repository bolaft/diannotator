# DiAnnotator
#
# Author: Soufian Salim <soufi@nsal.im>
#
# URL: <http://github.com/bolaft/diannotator>

"""
Style management
"""

from config import ConfigFile

config = ConfigFile()  # INI configuration file


class Styles:
    """
    Class defining text style tags
    """
    STRONG = "STRONG"
    ITALIC = "ITALIC"
    HIGHLIGHT = "HIGHLIGHT"

    def __init__(self):
        """
        Initializes style tags
        """

        self.add_tag(
            Styles.STRONG,
            font_weight="bold"
        )

        self.add_tag(
            Styles.ITALIC,
            font_weight="italic"
        )

        self.add_tag(
            Styles.HIGHLIGHT,
            background=config.get_string("select_background", "#332f2f")
        )

    def add_tag(self, name, foreground=None, background=None, justify=None, font_weight=None):
        """
        Creates a new tag
        """
        if foreground:
            self.text.tag_config(name, foreground=foreground)

        if background:
            self.text.tag_config(name, background=background)

        if justify:
            self.text.tag_config(name, justify=justify)

        if font_weight:
            self.text.tag_config(name, font=(self.text_font_family, self.text_font_size, font_weight))
