# DiAnnotator
#
# Author: Soufian Salim <soufi@nsal.im>
#
# URL: <http://github.com/bolaft/diannotator>

"""
Grapical User Interface
"""

from tkinter import Tk, StringVar, Text, Menu, messagebox, BOTH, DISABLED, END, LEFT, BOTTOM, NORMAL, N, X, WORD, NSEW, SUNKEN
from tkinter.ttk import Button, Entry, Frame, Label, Scrollbar
from ttkthemes import ThemedStyle

from styles import Styles

# colors
BLACK = "#000000"
WHITE = "#ffffff"
GRAY = "#0f0e0e"
MEDIUM_GRAY = "#353131"
DARK_GRAY = "#171717"


class GraphicalUserInterface(Frame, Styles):
    """
    Graphical User Interface class
    """
    window_title = "DiAnnotator"  # window title

    padding = 25  # padding for text area
    wrap_length = 960  # max length of labels before automatic newline

    # text parameters
    text_font_family = "mono"
    text_font_size = 12
    text_font_weight = "normal"

    # label parameters
    label_font_family = "mono"
    label_font_size = 12
    label_font_weight = "normal"

    # entry parameters
    entry_font_family = "TkDefaultFont"
    entry_font_size = 14
    entry_font_weight = "normal"

    # menu parameters
    menu_font_family = "modern"

    # special button parameters
    special_button_font_family = "mono"
    special_button_font_size = 11
    special_button_font_weight = "bold"

    special_button_style = "Special.TButton"

    def __init__(self):
        """
        Initializes the graphical user interface
        """
        # main interface object
        self.parent = Tk()
        self.parent.state = False

        # theme
        style = ThemedStyle(self.parent)
        style.set_theme("arc")

        # button style
        style.configure("TButton", font=self.label_font_family)

        # special button style
        style.configure(self.special_button_style, font=(
            self.special_button_font_family,
            self.special_button_font_size,
            self.special_button_font_weight
        ))

        # make buttons change foreground when hovered
        style.map('TButton', foreground=[("active", MEDIUM_GRAY)])

        # root window initialization
        Frame.__init__(self, self.parent)

        w = 1280  # width for the Tk parent
        h = 800  # height for the Tk parent

        # get screen width and height
        ws = self.parent.winfo_screenwidth()  # width of the screen
        hs = self.parent.winfo_screenheight()  # height of the screen

        self.parent.geometry("%dx%d+0+0" % (ws, hs))  # set the dimensions of the window
        self.parent.minsize(w, h)  # minimum size of the window

        # default bindings
        self.parent.bind("<F11>", lambda event: self.toggle_fullscreen())
        self.parent.bind("<Escape>", lambda event: self.exit_prompt())
        self.parent.bind("<Control-KP_Add>", lambda event: self.zoom_in())
        self.parent.bind("<Control-KP_Subtract>", lambda event: self.zoom_out())

        # window title
        self.parent.title(self.window_title)

        # menu bar
        self.menu_bar = Menu(self.parent, font=self.menu_font_family)

        self.file_menu = Menu(self.menu_bar, tearoff=0, font=self.menu_font_family)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        self.edit_menu = Menu(self.menu_bar, tearoff=0, font=self.menu_font_family)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)

        self.view_menu = Menu(self.menu_bar, tearoff=0, font=self.menu_font_family)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(label="Zoom In", accelerator="Ctrl++", command=self.zoom_in)
        self.view_menu.add_command(label="Zoom Out", accelerator="Ctrl+-", command=self.zoom_out)

        self.filter_menu = Menu(self.menu_bar, tearoff=0, font=self.menu_font_family)
        self.menu_bar.add_cascade(label="Filter", menu=self.filter_menu)

        self.taxonomy_menu = Menu(self.menu_bar, tearoff=0, font=self.menu_font_family)
        self.menu_bar.add_cascade(label="Taxonomy", menu=self.taxonomy_menu)

        self.parent.config(menu=self.menu_bar)

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

        # Text widget
        self.text = Text(self.output_frame, borderwidth=3, relief=SUNKEN)
        self.text.grid(row=0, column=0, sticky="nsew", padx=self.padding, pady=(self.padding, 0))
        self.text.config(font=(self.text_font_family, self.text_font_size), undo=True, wrap=WORD, bg=DARK_GRAY, fg=WHITE, highlightbackground=BLACK, highlightcolor=WHITE, state=DISABLED)

        # creates a Scrollbar and associate it with text
        self.scrollbar = Scrollbar(self.output_frame, command=self.text.yview)
        self.scrollbar.grid(row=0, rowspan=3, column=1, sticky=NSEW)
        self.text["yscrollcommand"] = self.scrollbar.set

        # status bar
        self.status = Label(self.output_frame, font=(self.label_font_family, self.label_font_size, "bold"))
        self.status.grid(row=1, column=0, pady=0)

        # binds any typing to the command input field to the update_commands method
        sv = StringVar()
        sv.trace("w", lambda name, index, mode, sv=sv: self.update_commands())

        # input frame
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

        self.prompt = StringVar()
        self.prompt_label = Label(self.commands, font=(self.menu_font_family, self.label_font_size, "bold"), textvariable=self.prompt)
        self.prompt_label.pack(side=LEFT, padx=(10, 15), pady=10)

        # creates the frame containing special buttons
        self.special_commands = Frame(self.input_frame)
        self.special_commands.pack(fill=X, side=BOTTOM)

        Styles.__init__(self)  # initializes style tags

        self.command_list = []  # list of potential commands

        self.action = None  # default command action
        self.default_action = None  # default command action

        self.free_input = False  # sets whether it's possible to input anything in the entry

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
                self.default_action()  # default action
            else:
                # list of buttons in the button list
                commands = self.commands.winfo_children()

                # if there is only one button (plus label), invokes it's function
                if len(commands) == 2:
                    self.commands.winfo_children()[1].invoke()
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

    def update_status_message(self, text):
        """
        Status message
        """
        self.status.config(text=text)

    def update_commands(self):
        """
        Updates the command button list
        """
        for element in self.commands.winfo_children():
            if isinstance(element, Button):
                element.destroy()

        input_text = self.entry.get()

        match = None

        for cmd in self.command_list:
            if cmd.lower() == input_text.lower():
                match = cmd

        # if only one match
        if match:
            self.make_button(match)
        else:
            chunks = input_text.split(" ")

            for s in self.command_list:
                # only if the input text can correspond to the command
                if len([c for c in chunks if c.lower() in s.lower()]) == len(chunks):
                    self.make_button(s)

        self.text.see(END)  # move the scrollbar to the bottom

    def make_button(self, text, bg=DARK_GRAY, fg=WHITE, disabled=False):
        b = Button(self.commands, text=text, command=lambda n=text: self.button_pressed(n))
        b.bind("<Return>", self.return_pressed)  # binds the Return key to the return_pressed method
        b.pack(side=LEFT)

        if disabled:
            b.config(state=DISABLED)

    def zoom_in(self):
        """
        Increases Text widget font
        """
        if self.text_font_size < 20:
            self.text_font_size += 1
            self.update_font_size()

    def zoom_out(self):
        """
        Decreases Text widget font
        """
        if self.text_font_size > 8:
            self.text_font_size -= 1
            self.update_font_size()

    def update_font_size(self):
        """
        Updates Text widget font size
        """
        self.text.config(font=(self.text_font_family, self.text_font_size))
        self.text.tag_config(Styles.STRONG, font=(self.text_font_family, self.text_font_size, "bold"))
        self.text.tag_config(Styles.ITALIC, font=(self.text_font_family, self.text_font_size, "italic"))
        self.text.see(END)  # move the scrollbar to the bottom

    def toggle_fullscreen(self):
        """
        Toggles between windowed and fullscreen
        """
        self.parent.state = not self.parent.state  # Just toggling the boolean
        self.parent.attributes("-fullscreen", self.parent.state)

        return "break"

    def exit_prompt(self):
        """
        Show an exit prompt
        """
        if messagebox.askyesno("Quit", "Do you want to quit?"):
            self.parent.quit()

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

    def add_to_last_line(self, text, style=None, offset=0):
        """
        Adds text to the end of the previous line
        """
        self.text.config(state=NORMAL)  # makes the text editable
        self.text.delete("end-1c linestart", self.text.index(END))
        self.text.config(state=DISABLED)  # makes the text editable

        self.add_text(text, added=True, style=style, offset=offset)

    def add_blank_lines(self, n, delay=1.0):
        """
        Adds blank lines to the text widget
        """
        if n > 0:
            # sleep(self.delay * delay)  # small pause between outputs
            self.add_text("" + "\n" * (n - 1))

    def input(self, prompt, commands, action, prompt_params=[], prompt_delay=0, free=False, sort=True, placeholder=""):
        """
        Manages user input
        """
        self.prompt.set(prompt.title() + ":" if prompt else "")
        self.free_input = free
        self.action = action

        commands = sorted(list(commands)) if sort else list(commands)  # sort commands alphabetically if necessary

        command_list = [str(c) for c in commands]

        if command_list != self.command_list:
            self.command_list = [str(c) for c in commands]
            self.update_commands()

        self.entry.delete(0, END)  # clears the entry field
        self.entry.insert(0, placeholder)  # inserts the placeholder
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
