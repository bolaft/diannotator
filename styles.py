# style names

STRONG = "STRONG"
ITALIC = "ITALIC"
DIALOG = "DIALOG"
PROCESS = "PROCESS"
INFO = "INFO"
DEBUG = "DEBUG"
OK = "OK"
WARNING = "WARNING"
FAIL = "FAIL"
HIGHLIGHT = "HIGHLIGHT"
BLACK = "BLACK"
WHITE = "WHITE"
GRAY = "GRAY"
LIGHT_GRAY = "LIGHT_GRAY"


class Styles:
    """
    Class defining text style tags
    """
    def __init__(self):
        """
        Initializes style tags
        """

        self.add_tag(
            BLACK,
            foreground="#000000"
        )

        self.add_tag(
            WHITE,
            foreground="#ffffff"
        )

        self.add_tag(
            GRAY,
            foreground="#0f0e0e"
        )

        self.add_tag(
            LIGHT_GRAY,
            foreground="#171717"
        )

        self.add_tag(
            STRONG,
            font_weight="bold"
        )

        self.add_tag(
            ITALIC,
            font_weight="italic"
        )

        self.add_tag(
            DIALOG,
            foreground="#54D6EF",
        )

        self.add_tag(
            PROCESS,
            foreground="#808080"
        )

        self.add_tag(
            INFO,
            foreground="#E6DB71"
        )

        self.add_tag(
            DEBUG,
            foreground="#664729"
        )

        self.add_tag(
            OK,
            foreground="#A6E22E"
        )

        self.add_tag(
            WARNING,
            foreground="#FD971F"
        )

        self.add_tag(
            HIGHLIGHT,
            background="#ffffff"
        )

        self.add_tag(
            FAIL,
            foreground="#FC4747"
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
