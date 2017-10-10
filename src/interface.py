import random

from tkinter import Tk, Button, Entry, Frame, Label, Scrollbar, StringVar, Text, Menu, BOTH, DISABLED, END, LEFT, BOTTOM, NORMAL, N, X, WORD, NSEW, SUNKEN
from styles import Styles

# colors

BLACK = "#000000"
WHITE = "#ffffff"
GRAY = "#0f0e0e"
LIGHT_GRAY = "#171717"


class GraphicalUserInterface(Frame, Styles):
    """
    Graphical User Interface class
    """
    __instance = None  # singleton
    __initialized = False  # prevents multiple initializations

    window_title = "DiAnnotator"  # window title

    padding = 25  # padding for text area
    wrap_length = 960  # max length of labels before automatic newline

    text_font_family = "mono"
    text_font_size = 12
    text_font_weight = "normal"

    label_font_family = "mono"
    label_font_size = 12
    label_font_weight = "normal"

    entry_font_family = "TkDefaultFont"
    entry_font_size = 14
    entry_font_weight = "normal"

    def __new__(cls):
        """
        Singleton method
        """
        if GraphicalUserInterface.__instance is None:
            GraphicalUserInterface.__instance = object.__new__(cls)

        return GraphicalUserInterface.__instance

    def __init__(self):
        """
        Initializes the graphical user interface
        """
        if GraphicalUserInterface.__initialized:
            return
        else:
            GraphicalUserInterface.__initialized = True

        self.command_list = []  # list of potential commands

        self.free_input = False  # sets whether it's possible to input anything in the entry

        # main interface object
        self.parent = Tk()
        self.parent.state = False

        Frame.__init__(self, self.parent, background=BLACK)  # initializes the root window

        w = 1024  # width for the Tk parent
        h = 680  # height for the Tk parent

        # get screen width and height
        ws = self.parent.winfo_screenwidth()  # width of the screen
        hs = self.parent.winfo_screenheight()  # height of the screen

        self.parent.geometry("%dx%d+0+0" % (ws, hs))  # set the dimensions of the window
        self.parent.minsize(w, h)  # minimum size of the window

        self.parent.bind("<F11>", self.toggle_fullscreen)
        self.parent.bind("<Escape>", lambda event, arg=None: self.parent.quit())

        # window title
        self.parent.title(self.window_title)

        # menu bar
        menubar = Menu(self.parent)

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load", command=self.load)
        filemenu.add_command(label="Save as", command=self.save_as)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.parent.quit)

        menubar.add_cascade(label="File", menu=filemenu)

        # menubar.add_command(label="test1", command=self.test1)
        # menubar.add_command(label="test2", command=self.test2)

        self.parent.config(menu=menubar)

        # make the frame take the whole window
        self.pack(fill=BOTH, expand=1)

        # input frame
        self.input_frame = None

        # output frame
        self.output_frame = Frame(self)
        self.output_frame.pack(fill=BOTH, anchor=N, expand=1)
        self.output_frame.grid_propagate(False)  # ensure a consistent GUI size
        self.output_frame.grid_rowconfigure(0, weight=30)  # implement stretchability
        self.output_frame.grid_rowconfigure(1, weight=1)  # implement stretchability
        self.output_frame.grid_columnconfigure(0, weight=1)

        # create a Text widget
        self.text = Text(self.output_frame, borderwidth=3, relief=SUNKEN)
        self.text.grid(row=0, column=0, sticky="nsew", padx=self.padding, pady=(self.padding, 0))
        self.text.config(font=(self.text_font_family, self.text_font_size), undo=True, wrap=WORD, bg=LIGHT_GRAY, fg=WHITE, highlightbackground=BLACK, highlightcolor=WHITE, state=DISABLED)

        # status bar
        self.status = Label(self.output_frame, height=0, wraplengt=self.wrap_length, font=(self.label_font_family, self.label_font_size))
        self.status.grid(row=1, column=0, pady=0)

        # create a Scrollbar and associate it with text
        self.scrollbar = Scrollbar(self.output_frame, command=self.text.yview)
        self.scrollbar.grid(row=0, rowspan=3, column=1, sticky=NSEW)
        self.text["yscrollcommand"] = self.scrollbar.set

        self.action = None  # default command action

        # binds any typing to the command input field to the update_commands method
        sv = StringVar()
        sv.trace("w", lambda name, index, mode, sv=sv: self.update_commands())

        self.input_frame = Frame(self)
        self.input_frame.pack(fill=X, side=BOTTOM)

        # makes the command input field
        self.entry = Entry(self.input_frame, font=(self.entry_font_family, self.entry_font_size), textvariable=sv, state=DISABLED)
        self.entry.bind("<Return>", self.return_pressed)  # binds the Return key to the return_pressed() method
        self.entry.bind("<KP_Enter>", self.return_pressed)  # binds the Return key to the return_pressed() method
        self.entry.bind("<Tab>", self.tab_pressed)  # binds the Tab key to the tab_pressed() method
        self.entry.pack(fill=X, side=BOTTOM, padx=2, pady=2)  # places the input field
        self.entry.focus_set()  # sets the focus on the input field

        # creates the frame containing buttons

        self.commands = Frame(self.input_frame)
        self.commands.pack(fill=X, side=BOTTOM)

        self.special_commands = Frame(self.input_frame)
        self.special_commands.pack(fill=X, side=BOTTOM)

        Styles.__init__(self)  # initializes style tags

    def return_pressed(self, e):
        """
        Handles presses of the Return key
        """
        focus = self.parent.focus_get()

        if focus == self.entry:
            # if the input is free, the entry content is captured; else the only corresponding command is captured
            if self.free_input:
                text = self.entry.get()
                self.entry.delete(0, END)  # clears the entry field
                self.process_input(text)
            elif len(self.entry.get()) == 0:
                self.command_continue(None)
            else:
                # list of buttons in the button list
                commands = self.commands.winfo_children()

                # if there is only one button, invokes it's function
                if len(commands) == 1:
                    self.commands.winfo_children()[0].invoke()
        else:
            for button in self.commands.winfo_children():
                if focus == button:
                    self.button_pressed(button.cget("text"))

    def tab_pressed(self, e):
        """
        Handles presses of the Tab key
        """
        self.entry.focus_set()  # sets the focus on the input field

    def button_pressed(self, b):
        """
        Activates command buttons
        """
        self.entry.delete(0, END)  # clears the entry field
        self.process_input(b)  # processes input corresponding to the button to the output canvas

    def process_input(self, t):
        """
        Processes user input
        """
        self.free_input = False
        self.action(t)
        self.annotation_mode()

    def update_status_message(self, text):
        """
        Status message
        """
        self.status.config(text=text)

    def update_commands(self):
        """
        Updates the command button list
        """
        for button in self.commands.winfo_children():
            button.destroy()

        input_text = self.entry.get()

        if input_text in self.command_list:
            self.make_button(input_text)
        else:
            chunks = input_text.split(" ")

            for s in self.command_list:
                # only if the input text can correspond to the command
                if len([c for c in chunks if c.lower() in s.lower()]) == len(chunks):
                    self.make_button(s)

        n_buttons = len(self.commands.winfo_children())

        # highlight button that will trigger if return is hit
        if n_buttons == 1:
            self.commands.winfo_children()[0].config(background=WHITE, foreground=GRAY)

        self.text.see(END)  # move the scrollbar to the bottom

    def make_button(self, text, bg=GRAY, fg=WHITE, disabled=False):
        b = Button(self.commands, text=text, background=bg, foreground=fg, command=lambda n=text: self.button_pressed(n))
        b.bind("<Return>", self.return_pressed)  # binds the Return key to the return_pressed method
        b.pack(side=LEFT)

        if disabled:
            b.config(state=DISABLED)

    def toggle_fullscreen(self, event=None):
        """
        Toggles between windowed and fullscreen
        """
        self.parent.state = not self.parent.state  # Just toggling the boolean
        self.parent.attributes("-fullscreen", self.parent.state)

        return "break"

    def end_fullscreen(self, event=None):
        """
        Returns to a windowed state
        """
        self.parent.state = False
        self.parent.attributes("-fullscreen", False)

        return "break"

    def clear_screen(self):
        """
        Clears the text widget
        """
        self.text.config(state=NORMAL)  # makes the text editable
        self.text.delete("1.0", self.text.index(END))
        self.text.config(state=DISABLED)  # makes the text editable

    def clear_last_line(self):
        """
        Clears the last line
        """
        self.text.config(state=NORMAL)  # makes the text editable
        self.text.delete("end-{}c linestart".format(self.previous_line_length), self.text.index(END))
        self.text.config(state=DISABLED)  # makes the text editable

        self.add_blank_lines(1)

    def add_to_last_line(self, text, style=None, offset=0):
        """
        Adds text to the end of the previous line
        """
        self.text.config(state=NORMAL)  # makes the text editable
        self.text.delete("end-1c linestart", self.text.index(END))
        self.text.config(state=DISABLED)  # makes the text editable

        self.add_text(text, added=True, style=style, offset=offset)

    def add_text(self, text, added=False, style=None, offset=0):
        """
        Adds text to the text widget
        """
        line_number = int(self.text.index(END).split(".")[0]) - 1  # line number relative to the rest of the text

        self.text.config(state=NORMAL)  # makes the text editable
        self.text.insert(END, text + "\n")  # inserts text

        start = "{}.{}".format(line_number, 0 + offset)  # start position of the line to output
        end = "{}.{}".format(line_number, len(text) + offset)  # end position of the line that was outputted

        # adds style to the text
        if len(text) > 0 and style:
            if isinstance(style, list):
                for s in style:
                    self.text.tag_add(s, start, end)
            else:
                self.text.tag_add(style, start, end)

        self.text.config(state=DISABLED)  # disabe the text field
        self.text.see(END)  # move the scrollbar to the bottom

        self.previous_tag_name = style
        self.previous_line_length = len(text)

    def add_blank_lines(self, n, delay=1.0):
        """
        Adds blank lines to the text widget
        """
        if n > 0:
            # sleep(self.delay * delay)  # small pause between outputs
            self.add_text("" + "\n" * (n - 1))

    def input(self, commands, action, prompt_params=[], prompt_delay=0, free=False, sort=True):
        """
        Manages user input
        """
        self.free_input = free
        self.action = action

        commands = sorted(list(set(commands))) if sort else commands  # sort commands alphabetically if necessary

        command_list = [str(c) for c in commands]
        if command_list != self.command_list:
            self.command_list = [str(c) for c in commands]
            self.update_commands()

        self.entry.delete(0, END)  # clears the entry field
        self.entry.config(state=NORMAL)
        self.entry.focus_set()  # sets the focus on the input field

    def output(self, message, style=None, params=[], delay=1.0, blank_before=0, blank_after=0):
        """
        Adds formatted text to the output buffer
        """
        # convert numbers in the message to words
        self.add_blank_lines(blank_before)  # blank lines before the output

        for line in message.split("\n"):
            # sleep(self.delay * delay)  # small pause between outputs

            self.add_text(line, style=style)

        self.add_blank_lines(blank_after, delay=delay)  # blank lines after the output

    def generate_random_color(self):
        r = (random.randrange(1, 256) + 255) / 2
        g = (random.randrange(1, 256) + 255) / 2
        b = (random.randrange(1, 256) + 255) / 2

        return '#%02x%02x%02x' % (r, g, b)
