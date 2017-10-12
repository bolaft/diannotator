# DiAnnotator
#
# Author: Soufian Salim <soufi@nsal.im>
#
# URL: <http://github.com/bolaft/diannotator>

"""
Style management
"""


class Styles:
    """
    Class defining text style tags
    """
    STRONG = "STRONG"
    ITALIC = "ITALIC"

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

    def add_tag(self, name, foreground=None, background=None, justify=None, font_family=None, font_size=None, font_weight=None):
        """
        Creates a new tag
        """
        if foreground:
            self.text.tag_config(name, foreground=foreground)

        if background:
            self.text.tag_config(name, background=background)

        if justify:
            self.text.tag_config(name, justify=justify)

        if font_family or font_size or font_weight:
            if not font_family:
                font_family = self.text_font_family
            if not font_size:
                font_size = self.text_font_size
            if not font_weight:
                font_weight = self.text_font_weight

            self.text.tag_config(name, font=(font_family, font_size, font_weight))
