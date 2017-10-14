# DiAnnotator
#
# Author: Soufian Salim <soufi@nsal.im>
#
# URL: <http://github.com/bolaft/diannotator>

"""
Annotation methods
"""

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, colorchooser, LEFT, END
from tkinter.ttk import Button
from undo import stack, undoable

from colors import generate_random_color
from interface import GraphicalUserInterface
from model import SegmentCollection
from styles import Styles


class Annotator(GraphicalUserInterface):
    """
    Class managing the annotation process
    """
    def __init__(self):
        """
        Initializes the annotator
        """
        GraphicalUserInterface.__init__(self)

        ####################
        # CONTROL BINDINGS #
        ####################

        # navigation shortcuts
        self.parent.bind(
            "<Down>",
            lambda event, arg=1: self.go_down(arg))
        self.parent.bind(
            "<Up>",
            lambda event, arg=1: self.go_up(arg))
        self.parent.bind(
            "<Next>",
            lambda event, arg=10: self.go_down(arg))
        self.parent.bind(
            "<Prior>",
            lambda event, arg=10: self.go_up(arg))

        # load / save / close shortcuts
        self.parent.bind(
            "<Control-o>",
            lambda event: self.open_file())
        self.parent.bind(
            "<Control-S>",
            lambda event: self.save_file())
        self.parent.bind(
            "<Control-I>",
            lambda event: self.import_file())
        self.parent.bind(
            "<Control-E>",
            lambda event: self.export_file())
        self.parent.bind(
            "<Control-w>",
            lambda event: self.close_file())
        self.parent.bind(
            "<Control-Alt-e>",
            lambda event: self.export_taxonomy())
        self.parent.bind(
            "<Control-Alt-i>",
            lambda event: self.import_taxonomy())

        # other shortcuts
        self.parent.bind(
            "<Delete>",
            lambda event: self.delete_segment())
        self.parent.bind(
            "<F2>",
            lambda event: self.show_legacy_annotations())
        self.parent.bind(
            "<F3>",
            lambda event: self.hide_legacy_annotations())
        self.parent.bind(
            "<F4>",
            lambda event: self.generate_participant_colors())
        self.parent.bind(
            "<F5>",
            lambda event: self.filter_by_active_layer())
        self.parent.bind(
            "<F6>",
            lambda event: self.filter_by_active_label())
        self.parent.bind(
            "<F7>",
            lambda event: self.filter_by_active_qualifier())
        self.parent.bind(
            "<Control-z>",
            lambda event: self.undo())
        self.parent.bind(
            "<Control-Z>",
            lambda event: self.redo())

        # special commands
        self.parent.bind(
            "<Control-l>",
            lambda event: self.select_link_type())
        self.parent.bind(
            "<Control-u>",
            lambda event: self.unlink_segment())
        self.parent.bind(
            "<Control-e>",
            lambda event: self.erase_annotation())
        self.parent.bind(
            "<Control-m>",
            lambda event: self.merge_segment())
        self.parent.bind(
            "<Control-s>",
            lambda event: self.select_split_token())
        self.parent.bind(
            "<Control-c>",
            lambda event: self.select_layer())
        self.parent.bind(
            "<Control-r>",
            lambda event: self.select_element())
        self.parent.bind(
            "<Control-a>",
            lambda event: self.select_new_element_type())
        self.parent.bind(
            "<Control-n>",
            lambda event: self.input_new_note())
        self.parent.bind(
            "<Control-f>",
            lambda event: self.select_filter_type())
        self.parent.bind(
            "<Control-j>",
            lambda event: self.select_go_to())

        #################
        # MENU COMMANDS #
        #################

        # file menu
        self.file_menu.add_command(label=self._("menu.open_file"), accelerator="Ctrl+O", command=self.open_file)
        self.file_menu.add_command(label=self._("menu.save_file"), accelerator="Ctrl+Shift+S", command=self.save_file)
        self.file_menu.add_command(label=self._("menu.import_file"), accelerator="Ctrl+Shift+I", command=self.import_file)
        self.file_menu.add_command(label=self._("menu.export_file"), accelerator="Ctrl+Shift+E", command=self.export_file)
        self.file_menu.add_command(label=self._("menu.close_file"), accelerator="Ctrl+W", command=self.close_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self._("menu.parent"), accelerator="Esc", command=self.parent.quit)

        # edit menu
        self.edit_menu.add_command(label=self._("menu.undo"), accelerator="Ctrl+Z", command=self.undo)
        self.edit_menu.add_command(label=self._("menu.redo"), accelerator="Ctrl+Shift+Z", command=self.redo)

        # view menu
        self.view_menu.add_separator()
        self.view_menu.add_command(label=self._("menu.toggle_participant_column"), command=self.toggle_participant_column)
        self.view_menu.add_command(label=self._("menu.toggle_date_column"), command=self.toggle_date_column)
        self.view_menu.add_command(label=self._("menu.toggle_time_column"), command=self.toggle_time_column)
        self.view_menu.add_command(label=self._("menu.toggle_id_column"), command=self.toggle_id_column)
        self.view_menu.add_separator()
        self.view_menu.add_command(label=self._("menu.show_legacy_annotations"), accelerator="F2", command=self.show_legacy_annotations)
        self.view_menu.add_command(label=self._("menu.hide_legacy_annotations"), accelerator="F3", command=self.hide_legacy_annotations)
        self.view_menu.add_separator()
        self.view_menu.add_command(label=self._("menu.generate_participant_colors"), accelerator="F4", command=self.generate_participant_colors)

        # filter menu
        self.filter_menu.add_command(label=self._("menu.filter_by_active_layer"), accelerator="F5", command=self.filter_by_active_layer)
        self.filter_menu.add_command(label=self._("menu.filter_by_active_label"), accelerator="F6", command=self.filter_by_active_label)
        self.filter_menu.add_command(label=self._("menu.filter_by_active_qualifier"), accelerator="F7", command=self.filter_by_active_qualifier)

        # taxonomy menu
        self.taxonomy_menu.add_command(label=self._("menu.import_taxonomy"), accelerator="Ctrl+Alt+I", command=self.import_taxonomy)
        self.taxonomy_menu.add_command(label=self._("menu.export_taxonomy"), accelerator="Ctrl+Alt+E", command=self.export_taxonomy)
        self.taxonomy_menu.add_separator()
        self.taxonomy_menu.add_command(label=self._("menu.set_layer_as_default"), command=self.set_layer_as_default)
        self.taxonomy_menu.add_separator()
        self.taxonomy_menu.add_command(label=self._("menu.remove_label"), command=self.remove_label)
        self.taxonomy_menu.add_command(label=self._("menu.remove_qualifier"), command=self.remove_qualifier)
        self.taxonomy_menu.add_command(label=self._("menu.remove_layer"), command=self.remove_layer)
        self.taxonomy_menu.add_command(label=self._("menu.remove_link_types"), command=self.remove_link_types)
        self.taxonomy_menu.add_separator()
        self.taxonomy_menu.add_command(label=self._("menu.select_element_type_to_colorize"), command=self.select_element_type_to_colorize)

        ##################
        # INITIALIZATION #
        ##################

        # attempt to load previous save
        previous_save = SegmentCollection.read_save_path_from_tmp()

        if previous_save:
            self.sc = SegmentCollection.load(previous_save)

        if not hasattr(self, "sc"):
            # initializing the segment collection
            self.sc = SegmentCollection()  # load command

        # colorization
        self.colorize()

        # make a backup of the collection
        self.sc.save(
            path="{}backup/auto-{}.pic".format(SegmentCollection.save_dir, datetime.now().strftime("%d-%m-%y_%X")),
            backup=True
        )

        # special buttons
        self.make_special_buttons()

        # default action (when return is pressed without context)
        self.default_action = lambda arg=1: self.go_down(arg)

        # clear undo stack
        stack().clear()

        # previous key press, for speed checks
        self.previous_key_press = datetime.now() - timedelta(seconds=10)

        # click is go to segment by default
        self.click_to_link_type = None

        # show legacy annotations
        self.show_legacy = True  # show legacy annotations by defaults

        # show columns
        self.show_participant = True  # show participant by default
        self.show_date = False  # hide date by default
        self.show_time = True  # show time by default
        self.show_id = False  # hide id by default

        # display update
        self.update()

    ################
    # VIEW METHODS #
    ################

    def toggle_participant_column(self):
        """
        Toggles participant column display
        """
        self.show_participant = not self.show_participant
        self.update()

    def toggle_date_column(self):
        """
        Toggles date column display
        """
        self.show_date = not self.show_date
        self.update()

    def toggle_time_column(self):
        """
        Toggles time column display
        """
        self.show_time = not self.show_time
        self.update()

    def toggle_id_column(self):
        """
        Toggles id column display
        """
        self.show_id = not self.show_id
        self.update()

    def show_legacy_annotations(self):
        """
        Sets legacy annotations to be displayed
        """
        self.show_legacy = True
        self.update()

    def hide_legacy_annotations(self):
        """
        Sets legacy annotations to not be displayed
        """
        self.show_legacy = False
        self.update()

    #################
    # COLOR METHODS #
    #################

    def colorize(self, layers=True, links=True, participants=True):
        """
        Initializes colors
        """
        if layers:
            self.generate_layer_colors()
        if links:
            self.generate_link_colors()
        if participants:
            self.generate_participant_colors()

    def generate_participant_colors(self):
        """
        Adds a color tag per participant to the text widget
        """
        for participant in set([s.participant for s in self.sc.full_collection]):
            self.add_tag(
                "participant-{}".format(participant),
                foreground=generate_random_color()
            )

    def generate_layer_colors(self):
        """
        Adds a color tag per layer to the text widget
        """
        legacy_layers = []

        for segment in self.sc.full_collection:
            for layer in segment.legacy.keys():
                if layer not in legacy_layers:
                    legacy_layers.append(layer)

        for layer in list(self.sc.labels.keys()) + legacy_layers:
            if layer not in self.sc.colors.keys():
                self.sc.colors[layer] = generate_random_color()

        for layer, color in self.sc.colors.items():
            self.add_tag(
                "layer-{}".format(layer),
                foreground=color
            )

    def generate_link_colors(self):
        """
        Adds a color tag per link type to the text widget
        """
        for link, color in self.sc.links.items():
            self.add_tag(
                "link-{}".format(link),
                foreground=color
            )

    #####################
    # INTERFACE METHODS #
    #####################

    def make_special_buttons(self):
        """
        Creates special command buttons
        """
        for button in self.special_commands.winfo_children():
            button.destroy()

        buttons = OrderedDict()

        buttons.update({self._("button.select_layer"): self.select_layer})
        buttons.update({self._("button.erase_annotation"): self.erase_annotation})
        buttons.update({self._("button.select_link_type"): self.select_link_type})
        buttons.update({self._("button.unlink_segment"): self.unlink_segment})
        buttons.update({self._("button.select_split_token"): self.select_split_token})
        buttons.update({self._("button.merge_segment"): self.merge_segment})
        buttons.update({self._("button.select_new_element_type"): self.select_new_element_type})
        buttons.update({self._("button.select_element"): self.select_element})
        buttons.update({self._("button.select_go_to"): self.select_go_to})
        buttons.update({self._("button.select_filter_type"): self.select_filter_type})
        buttons.update({self._("button.input_new_note"): self.input_new_note})

        for text, function in buttons.items():
            b = Button(
                self.special_commands,
                text=text,
                style=self.special_button_style,
                command=function
            )

            b.pack(side=LEFT)

    #####################
    # SAVE/OPEN METHODS #
    #####################

    def open_file(self):
        """
        Loads a .pic file through dialogue
        """
        path = filedialog.askopenfilename(
            initialdir=SegmentCollection.save_dir,
            title=self._("dialog.title.open_file"),
            filetypes=(
                (self._("filetype.pickle"), "*.pic"),
                (self._("filetype.all_files"), "*.*")
            )
        )

        if path == "":
            return  # no file selected

        sc = SegmentCollection.load(path)

        if sc:
            self.sc = sc
            stack().clear()  # reinitializes undo history
            self.colorize()
            self.update()
        else:
            messagebox.showerror(
                self._("error.title.open_file"),
                self._("error.text.open_file")
            )

    def save_file(self):
        """
        Saves a .pic file through dialogue
        """
        path = filedialog.asksaveasfilename(
            initialdir=SegmentCollection.save_dir,
            title=self._("dialog.title.save_file"),
            filetypes=(
                (self._("filetype.pickle"), "*.pic"),
                (self._("filetype.all_files"), "*.*")
            )
        )

        if path == "":
            return  # no path selected

        success = self.sc.save(path=path)

        if not success:
            messagebox.showerror(
                self._("error.title.save_file"),
                self._("error.text.save_file")
            )

    def import_file(self):
        """
        Loads a .csv file through dialogue
        """
        path = filedialog.askopenfilename(
            initialdir=SegmentCollection.csv_dir,
            title=self._("dialog.title.import_file"),
            filetypes=(
                (self._("filetype.csv"), "*.csv"),
                (self._("filetype.json"), "*.json"),
                (self._("filetype.all_files"), "*.*")
            )
        )

        if path == "":
            return  # no file selected

        success = self.sc.import_collection(path)

        if success:
            # choose a taxonomy
            self.import_taxonomy()

            # how to use legacy annotations
            if messagebox.askyesno(
                self._("box.title.legacy_annotations"),
                self._("box.text.legacy_annotations")
            ):
                self.sc.legacy_to_annotations()

            stack().clear()  # reinitializes undo history

            self.colorize(participants=False)
            self.update()
        else:
            messagebox.showerror(
                self._("error.title.open_file"),
                self._("box.text.wrong_format")
            )

    def export_file(self):
        """
        Saves a .csv or .json file through dialogue
        """
        path = filedialog.asksaveasfilename(
            initialdir=SegmentCollection.out_dir,
            title=self._("dialog.title.export_file"),
            filetypes=(
                (self._("filetype.csv"), "*.csv"),
                (self._("filetype.json"), "*.json")
            )
        )

        if path == "":
            return  # no path selected

        success = self.sc.export_collection(path)

        if not success:
            messagebox.showerror(
                self._("error.title.export_file"),
                self._("error.text.export_file")
            )

    def close_file(self):
        """
        Closes the current file
        """
        # deletes the "previous save" file
        SegmentCollection.delete_save_path_on_tmp()
        self.clear_screen()
        self.sc = SegmentCollection()  # load command
        self.update()

    def import_taxonomy(self):
        """
        Loads a .json taxonomy file through dialogue
        """
        path = filedialog.askopenfilename(
            initialdir=SegmentCollection.taxo_dir,
            title=self._("dialog.title.import_taxonomy"),
            filetypes=(
                (self._("filetype.json"), "*.json"),
                (self._("filetype.all_files"), "*.*")
            )
        )

        if path == "":
            return  # no path selected

        success = self.sc.import_taxonomy(path)

        if success:
            self.colorize()
            self.update()
        else:
            messagebox.showerror(
                self._("error.title.import_taxonomy"),
                self._("error.text.import_taxonomy")
            )

    def export_taxonomy(self):
        """
        Saves a .json taxonomy file through dialogue
        """
        path = filedialog.asksaveasfilename(
            initialdir=SegmentCollection.custom_taxo_dir,
            title=self._("dialog.title.export_taxonomy"),
            filetypes=(
                (self._("filetype.json"), "*.json"),
                (self._("filetype.all_files"), "*.*")
            )
        )

        if path == "":
            return  # no path selected

        success = self.sc.export_taxonomy(path)

        if not success:
            messagebox.showerror(
                self._("error.title.export_taxonomy"),
                self._("error.text.export_file")
            )

    #######################
    # NAVIGATION COMMANDS #
    #######################

    def is_slow_enough(self, milliseconds=75):
        """
        Checks if the speed limit between key presses is respected
        """
        now = datetime.now()

        delta = now - self.previous_key_press

        if delta.total_seconds() * 1000 < milliseconds:
            return False
        else:
            self.previous_key_press = now

            return True

    def go_down(self, n):
        """
        Moves to an ulterior segment
        """
        if self.is_slow_enough():
            self.cycle_down(n=n)

    @undoable
    def cycle_down(self, n):
        # cycles through the collection
        self.sc.next(n=n)
        self.update()

        yield  # undo

        self.cycle_up(n)

    def go_up(self, n, limit_speed=True):
        """
        Moves to a previous segment
        """
        if self.is_slow_enough():
            self.cycle_up(n=n)

    @undoable
    def cycle_up(self, n):
        # cycles through the collection
        self.sc.previous(n=n)
        self.update()

        yield  # undo

        self.cycle_down(n)

    def select_go_to(self):
        """
        Inputs a target segment to go to
        """
        self.input("prompt.select_go_to", [], self.go_to, free=True)

    @undoable
    def go_to(self, number):
        """
        Moves to a specific segment by index in collection
        """
        i = self.sc.i
        self.sc.i = int(number) - 1

        if self.sc.i >= len(self.sc.collection):
            self.sc.i = len(self.sc.collection) - 1

        if self.sc.i < 0:
            self.sc.i = 0

        self.update()

        yield  # undo

        self.go_to(i)

    ###############################
    # SEGMENT MANAGEMENT COMMANDS #
    ###############################

    def delete_segment(self):
        """
        Deletes the active segment
        """
        if messagebox.askyesno(
            self._("dialog.title.delete_segment"),
            self._("dialog.text.delete_segment")
        ):
            self.apply_delete_segment()

    @undoable
    def apply_delete_segment(self):
        segment = self.sc.get_active()
        i, fi = self.sc.get_segment_indexes(segment)
        self.sc.remove(segment)
        self.update()

        yield  # undo

        self.sc.insert(i, fi, segment)

    def merge_segment(self):
        """
        Merges the active segment to its preceding one
        """
        segment = self.sc.get_active()
        previous = self.sc.collection[self.sc.i - 1]

        if segment.participant == previous.participant:  # can only merge segments from the same participant
            self.apply_merge_segment(segment, previous)

    @undoable
    def apply_merge_segment(self, segment, previous):
        """
        Applies a merge
        """
        i, fi = self.sc.get_segment_indexes(segment)
        original = deepcopy(segment)
        segment.merge(previous)

        self.sc.remove(previous)
        self.sc.previous()

        self.update()

        yield  # undo

        self.sc.remove(segment)
        self.sc.insert(i, fi, original)
        self.sc.insert(i, fi, previous)
        self.sc.next(n=2)

    def select_split_token(self):
        """
        Inputs the token on which the active segment will be split
        """
        segment = self.sc.get_active()

        if len(segment.tokens) > 1:
            self.input("prompt.select_split_token", segment.tokens[:-1], self.split_segment, sort=False)

    @undoable
    def split_segment(self, token):
        """
        Splits the active segment in two
        """
        segment = self.sc.get_active()
        i, fi = self.sc.get_segment_indexes(segment)
        splits = segment.split(token)

        for split in reversed(splits):
            self.sc.insert_after_active(split)

        self.sc.remove(segment)

        self.update()

        yield  # undo

        for split in splits:
            self.sc.remove(split)

        self.sc.insert(i, fi, segment)

    ##################################
    # ANNOTATION MANAGEMENT COMMANDS #
    ##################################

    def erase_annotation(self):
        """
        Erases the active segment's annotation for the active layer
        """
        segment = self.sc.get_active()

        if self.sc.layer in segment.annotations:
            self.apply_erase_annotation(segment)

    @undoable
    def apply_erase_annotation(self, segment):
        """
        Applies an annotation erasure
        """
        label = segment.get(self.sc.layer)
        qualifier = segment.get(self.sc.layer, qualifier=True)

        segment.rem(self.sc.layer)
        segment.rem(self.sc.layer, qualifier=True)

        self.update()

        yield  # undo

        segment.set(self.sc.layer, label)
        segment.set(self.sc.layer, qualifier, qualifier=True)

    def select_link_type(self):
        """
        Inputs a link type
        """
        if len(self.sc.links.keys()) == 0:
            messagebox.showwarning(
                self._("dialog.title.select_link_type"),
                self._("dialog.text.select_link_type")
            )
            return

        if self.sc.i > 0:  # first segment can't be linked
            self.input("prompt.select_link_type", self.sc.links.keys(), self.select_link_target)

    def select_link_target(self, link_type):
        """
        Set a link type then input link target
        """
        # activates click to link segment
        self.click_to_link_type = link_type

        # input target segment
        self.input("prompt.select_link_target", [], lambda n, link_t=link_type: self.link_segment(n, link_t), sort=False, free=True)

    @undoable
    def link_segment(self, number, link_type):
        """
        Links the active segment to another
        """
        # disables click to link segment
        self.click_to_link_type = None

        number = int(number) - 1

        segment = self.sc.get_active()

        success = False

        if number >= 0 and number < self.sc.collection.index(segment):
            if not (self.sc.collection[number], link_type) in segment.links:
                segment.links.append((self.sc.collection[number], link_type))
                self.sc.collection[number].linked.append((segment, link_type))

                success = True

        self.update()

        yield  # undo

        if success:
            segment.links.remove((self.sc.collection[number], link_type))
            self.sc.collection[number].linked.remove((segment, link_type))

    @undoable
    def unlink_segment(self):
        """
        Removes links emanating from the active segment
        """
        segment = self.sc.get_active()
        links = segment.links.copy()

        while segment.links:
            ls, lt = segment.links[0]
            segment.remove_links(ls)

        self.update()

        yield  # undo

        for ls, lt in links:
            segment.create_link(ls, lt)

    def input_new_note(self):
        """
        Inputs a note for the active segment
        """
        segment = self.sc.get_active()
        placeholder = "" if segment.note is None else segment.note
        self.input("prompt.input_new_note", [], self.set_note, placeholder=placeholder, free=True)

    @undoable
    def set_note(self, note):
        """
        Sets the note of the segment
        """
        segment = self.sc.get_active()
        previous_note = segment.note

        if note != "":
            segment = self.sc.get_active()
            segment.note = note
        else:
            segment.note = None

        self.update()

        yield  # undo

        segment.note = previous_note

    ################################
    # TAXONOMY MANAGEMENT COMMANDS #
    ################################

    def select_new_element_type(self):
        """
        Selects the type of element to be added to the taxonomy
        """
        self.input("prompt.select_new_element_type", [
                self._("layer"),
                self._("label"),
                self._("qualifier"),
                self._("link_type")
            ], self.add_new_element)

    def add_new_element(self, element_type):
        """
        Adds a new element to the taxonomy
        """
        if element_type == self._("layer"):
            self.input("prompt.add_new_element_layer", [], self.add_layer, free=True)

        if element_type == self._("label"):
            self.input("prompt.add_new_element_label", [], self.add_label, free=True)

        if element_type == self._("qualifier"):
            self.input("prompt.add_new_element_qualifier", [], self.add_qualifier, free=True)

        if element_type == self._("link_type"):
            self.input("prompt.add_new_element_link_typer", [], self.add_link_type, free=True)

    @undoable
    def add_layer(self, layer):
        """
        Adds a new layer to the taxonomy
        """
        self.sc.add_layer(layer)
        self.update()

        yield  # undo

        self.sc.delete_layer(layer)

    @undoable
    def add_label(self, label):
        """
        Adds a new label to the taxonomy
        """
        self.sc.add_label(self.sc.layer, label)
        self.update()

        yield  # undo

        self.sc.delete_label(self.sc.layer, label)

    @undoable
    def add_qualifier(self, qualifier):
        """
        Adds a new qualifier to the taxonomy
        """
        self.sc.add_qualifier(self.sc.layer, qualifier)
        self.update()

        yield  # undo

        self.sc.delete_qualifier(self.sc.layer, qualifier)

    @undoable
    def add_link_type(self, link_type):
        """
        Adds a new link type to the taxonomy
        """
        self.sc.add_link_type(link_type)
        self.update()

        yield  # undo

        self.sc.delete_link_type(link_type)

    @undoable
    def remove_label(self):
        """
        Removes the active segment's label from the taxonomy
        """
        sc = deepcopy(self.sc)

        segment = self.sc.get_active()

        if self.sc.layer in segment.annotations:
            label = segment.get(self.sc.layer)
            if messagebox.askyesno(
                self._("dialog.title.remove_label"),
                self._("dialog.text.remove_label", label)
            ):
                self.sc.delete_label(self.sc.layer, label)
                self.update()

        yield  # undo

        self.sc = sc

    @undoable
    def remove_qualifier(self):
        """
        Removes the active segment's qualifier from the taxonomy
        """
        sc = deepcopy(self.sc)

        segment = self.sc.get_active()

        if self.sc.layer in segment.annotations:
            qualifier = segment.get(self.sc.layer, qualifier=True)
            if messagebox.askyesno(
                self._("dialog.text.remove_label"),
                self._("dialog.text.remove_qualifier", qualifier)
            ):
                self.sc.delete_qualifier(self.sc.layer, qualifier)
                self.update()

        yield  # undo

        self.sc = sc

    def set_layer_as_default(self):
        """
        Removes the active segment's layer from the taxonomy
        """
        self.sc.default_layer = self.sc.layer

    def remove_layer(self):
        """
        Removes the active segment's layer from the taxonomy
        """
        if messagebox.askyesno(
            self._("dialog.title.remove_layer"),
            self._("dialog.text.remove_layer", self.sc.layer)
        ):
            self.apply_remove_layer(self.sc.layer)

    @undoable
    def apply_remove_layer(self, layer):
        """
        Applies the removal of a layer
        """
        sc = deepcopy(self.sc)

        self.sc.delete_layer(layer)
        self.update()

        yield  # undo

        self.sc = sc

    def remove_link_types(self):
        """
        Removes the active segment's link types from the taxonomy
        """
        lts = []

        for ls, lt in self.sc.get_active().links:
            if lt not in lts:
                lts.append(lt)

        if messagebox.askyesno(
            self._("dialog.title.remove_link_types", "s" if len(lts) > 1 else ""),
            self._("dialog.text.remove_link_types", ", ".join(lts), "s" if len(lts) > 1 else "")
        ):
            self.apply_remove_link_types(lts)

    @undoable
    def apply_remove_link_types(self, link_types):
        """
        Applies the removal of a layer
        """
        sc = self.sc

        for lt in link_types:
            self.sc.delete_link_type(lt)

        self.update()

        yield  # undo

        self.sc = sc

    def select_element_type_to_colorize(self):
        """
        Selects the type of element to be colorized
        """
        element_types = [self._("layer"), self._("link_type")]

        for segment in self.sc.full_collection:
            for layer in segment.legacy.keys():
                # adds Legacy Layer option if there are any original ones
                if layer not in self.sc.labels.keys():
                    element_types.append(self._("legacy_layer"))
                    break
            for ls, lt in segment.legacy_links:
                # adds Legacy Link Type option if there are any original ones
                if lt not in self.sc.links.keys():
                    element_types.append(self._("legacy_link_type"))
                    break

        self.input("select type of element to colorize", set(element_types), self.select_element_to_colorize)

    def select_element_to_colorize(self, element_type):
        """
        Select an element to colorize
        """
        if element_type == self._("layer"):
            self.input("prompt.select_element_to_colorize_layer", self.sc.labels.keys(), self.pick_color_for_layer)

        if element_type == self._("legacy_layer"):
            legacy_layers = []

            for segment in self.sc.full_collection:
                for layer in segment.legacy.keys():
                    if layer not in legacy_layers and layer not in self.sc.labels.keys():
                        legacy_layers.append(layer)

            self.input("prompt.select_element_to_colorize_legacy_layer", legacy_layers, self.pick_color_for_layer)

        if element_type == self._("link_type"):
            self.input("prompt.select_element_to_colorize_link_type", self.sc.links.keys(), self.pick_color_for_link_type)

        if element_type == self._("legacy_link_type"):
            legacy_link_types = []

            for segment in self.sc.full_collection:
                for ls, lt in segment.legacy_links:
                    if lt not in legacy_link_types and lt not in self.sc.links.keys():
                        legacy_link_types.append(lt)

            self.input("prompt.select_element_to_colorize_legacy_link", legacy_link_types, self.pick_color_for_link_type)

    def pick_color_for_layer(self, layer):
        """
        Color picker for a layer
        """
        color = colorchooser.askcolor()

        if len(color) > 0 and color[-1]:
            self.sc.colors[layer] = color[-1]
            self.generate_layer_colors()
            self.update()

    def pick_color_for_link_type(self, link_type):
        """
        Color picker for a link type
        """
        color = colorchooser.askcolor()

        if len(color) > 0 and color[-1]:
            self.sc.links[link_type] = color[-1]
            self.generate_link_colors()
            self.update()

    def select_element(self):
        """
        Selects the element to be renamed
        """
        segment = self.sc.get_active()

        elements = [self.sc.layer]

        if self.sc.layer in segment.annotations:
            if segment.has(self.sc.layer):
                elements.append(segment.get(self.sc.layer))

            if segment.has(self.sc.layer, qualifier=True):
                elements.append(segment.get(self.sc.layer, qualifier=True))

        for ls, lt in segment.links:
            elements.append(lt)

        self.input(
            "prompt.select_element",
            elements,
            self.input_element_new_name
        )

    def input_element_new_name(self, text):
        """
        Select either a layer, a label or a qualifier to rename
        """
        segment = self.sc.get_active()

        if text == self.sc.layer:
            self.input(
                "prompt.input_element_new_name_layer",
                [],
                self.rename_layer,
                placeholder=text,
                free=True
            )

        if text == self.sc.get_active_label():
            self.input(
                "prompt.input_element_new_name_label",
                [],
                self.rename_label,
                placeholder=text,
                free=True
            )

        if text == self.sc.get_active_qualifier():
            self.input(
                "prompt.input_element_new_name_qualifier",
                [],
                self.rename_qualifier,
                placeholder=text,
                free=True
            )

        for ls, lt in segment.links:
            if text == lt:
                self.input(
                    "prompt.input_element_new_name_relation_type",
                    [],
                    lambda name: self.rename_link_type(lt, name),
                    placeholder=text,
                    free=True
                )

    @undoable
    def rename_layer(self, name):
        """
        Renames a layer
        """
        sc = self.sc
        success = self.sc.change_layer(self.sc.layer, name)
        self.update()
        self.generate_layer_colors()

        yield  # undo

        if success:
            self.sc = sc
            self.generate_layer_colors()

    @undoable
    def rename_label(self, label):
        """
        Renames a label
        """
        sc = deepcopy(self.sc)
        segment = self.sc.get_active()

        if label:
            self.sc.change_label(
                self.sc.layer,
                segment.get(self.sc.layer),
                label
            )

            self.update()

        yield  # undo

        if label:
            self.sc = sc

    @undoable
    def rename_qualifier(self, qualifier):
        """
        Renames a qualifier
        """
        sc = deepcopy(self.sc)
        segment = self.sc.get_active()

        if qualifier:
            self.sc.change_qualifier(
                self.sc.layer,
                segment.get(self.sc.layer, qualifier=True),
                qualifier
            )

            self.update()

        yield  # undo

        if qualifier:
            self.sc = sc

    @undoable
    def rename_link_type(self, link_type, name):
        """
        Renames a link type
        """
        sc = self.sc
        success = self.sc.change_link_type(link_type, name)
        self.update()

        yield  # undo

        if success:
            self.sc = sc

    #################
    # VIEW COMMANDS #
    #################

    def select_filter_type(self):
        """
        Selects a filter type
        """
        if not self.sc.filter:
            self.input(
                self._("prompt.select_filter_type"), [
                    self._("layer"),
                    self._("legacy_layer"),
                    self._("label"),
                    self._("legacy_label"),
                    self._("qualifier"),
                    self._("legacy_qualifier")
                ], self.filter)
        else:
            self.remove_filter()

    @undoable
    def remove_filter(self):
        """
        Removes a filter
        """
        sc = deepcopy(self.sc)

        if self.sc.collection:
            self.sc.i = self.sc.full_collection.index(self.sc.get_active())

        self.sc.collection = self.sc.full_collection.copy()
        self.sc.filter = False

        self.update()

        yield  # undo

        self.sc = sc

    def filter(self, filter_type):
        """
        Filters the collection
        """
        if filter_type == self._("layer"):
            self.input(
                "prompt.filter_layer",
                self.sc.labels.keys(),
                self.filter_by_layer
            )

        if filter_type == self._("legacy_layer"):
            legacy_layers = []

            for segment in self.sc.full_collection:
                for layer in segment.legacy.keys():
                    legacy_layers.append(layer)

            self.input(
                "prompt.filter_legacy_layer",
                set(legacy_layers),
                self.filter_by_legacy_layer
            )

        if filter_type == self._("label"):
            labels = []

            for layer in self.sc.labels:
                labels += self.sc.labels[layer]

            self.input(
                "prompt.filter_label",
                set(labels),
                self.filter_by_label
            )

        if filter_type == self._("legacy_label"):
            legacy_labels = []

            for segment in self.sc.full_collection:
                for layer in segment.legacy.keys():
                    if segment.has(layer, legacy=True):
                        legacy_labels.append(segment.get(layer, legacy=True))

            self.input(
                "prompt.filter_legacy_label",
                set(legacy_labels),
                self.filter_by_legacy_label
            )

        if filter_type == self._("qualifier"):
            qualifiers = []

            for layer in self.sc.qualifiers:
                qualifiers += self.sc.qualifiers[layer]

            self.input(
                "prompt.filter_qualifier",
                set(qualifiers),
                self.filter_by_qualifier
            )

        if filter_type == self._("legacy_qualifier"):
            legacy_qualifiers = []

            for segment in self.sc.full_collection:
                for layer in segment.legacy.keys():
                    if segment.has(layer, legacy=True, qualifier=True):
                        legacy_qualifiers.append(segment.get(layer, legacy=True, qualifier=True))

            self.input(
                "prompt.filter_legacy_qualifier",
                set(legacy_qualifiers),
                self.filter_by_legacy_qualifier
            )

    def filter_by_active_layer(self):
        """
        Filters the collection by active layer
        """
        if not self.sc.filter:
            self.filter_by_layer(self.sc.layer)
        else:
            self.remove_filter()

    def filter_by_active_label(self):
        """
        Filters the collection by active label
        """
        if not self.sc.filter:
            label = self.sc.get_active_label()

            if label:
                self.filter_by_label(label)
        else:
            self.remove_filter()

    def filter_by_active_qualifier(self):
        """
        Filters the collection by active qualifier
        """
        if not self.sc.filter:
            qualifier = self.sc.get_active_qualifier()

            if qualifier:
                self.filter_by_qualifier(qualifier)
        else:
            self.remove_filter()

    def finish_filter(self):
        """
        Moves the index to an appropriate location in the new collection
        """
        # look first for a target from the active segment to the end, and then backwards from the position of the active segment
        for i in list(range(self.sc.i, len(self.sc.full_collection))) + list(reversed(range(0, self.sc.i))):
            segment = self.sc.full_collection[i]
            if segment in self.sc.collection:
                # adjust the current index in the new collection
                self.sc.i = self.sc.collection.index(segment)
                break

        self.update()

    @undoable
    def filter_by_layer(self, layer):
        """
        Filters the collection by layer
        """
        sc = deepcopy(self.sc)

        self.sc.collection = [s for s in self.sc.full_collection if layer in s.annotations]
        self.sc.filter = "|{}|".format(layer)
        self.finish_filter()

        yield  # undo

        self.sc = sc

    @undoable
    def filter_by_legacy_layer(self, layer):
        """
        Filters the collection by legacy layer
        """
        sc = deepcopy(self.sc)

        self.sc.collection = [s for s in self.sc.full_collection if layer in s.legacy]
        self.sc.filter = "|{}|".format(layer)
        self.finish_filter()

        yield  # undo

        self.sc = sc

    @undoable
    def filter_by_label(self, label):
        """
        Filters the collection by label
        """
        sc = deepcopy(self.sc)

        segments = []

        for segment in self.sc.full_collection:
            for layer in segment.annotations:
                if segment.has(layer, annotation=label):
                    segments.append(segment)

        self.sc.collection = list(set(segments))
        self.sc.filter = "[{}]".format(label)
        self.finish_filter()

        yield  # undo

        self.sc = sc

    @undoable
    def filter_by_legacy_label(self, label):
        """
        Filters the collection by legacy label
        """
        sc = deepcopy(self.sc)

        segments = []

        for segment in self.sc.full_collection:
            for layer in segment.legacy:
                if segment.has(layer, annotation=label, legacy=True):
                    segments.append(segment)

        self.sc.collection = list(set(segments))
        self.sc.filter = "[{}]".format(label)
        self.finish_filter()

        yield  # undo

        self.sc = sc

    @undoable
    def filter_by_qualifier(self, qualifier):
        """
        Filters the collection by qualifier
        """
        sc = deepcopy(self.sc)

        segments = []

        for segment in self.sc.full_collection:
            for layer in segment.annotations:
                if segment.has(layer, annotation=qualifier, qualifier=True):
                    segments.append(segment)

        self.sc.collection = list(set(segments))
        self.sc.filter = "[➔ {}]".format(qualifier)
        self.finish_filter()

        yield  # undo

        self.sc = sc

    @undoable
    def filter_by_legacy_qualifier(self, qualifier):
        """
        Filters the collection by legacy qualifier
        """
        sc = deepcopy(self.sc)

        segments = []

        for segment in self.sc.full_collection:
            for layer in segment.legacy:
                if segment.has(layer, annotation=qualifier, qualifier=True, legacy=True):
                    segments.append(segment)

        self.sc.collection = list(set(segments))
        self.sc.filter = "((➔ {}))".format(qualifier)
        self.finish_filter()

        yield  # undo

        self.sc = sc

    ######################
    # UNDO/REDO COMMANDS #
    ######################

    def undo(self):
        """
        Undo command
        """
        stack().undo()
        self.update()

    def redo(self):
        """
        Redo command
        """
        stack().redo()
        self.update()

    ######################
    # DIMENSION COMMANDS #
    ######################

    def select_layer(self):
        """
        Inputs a layer
        """
        if len(self.sc.labels.keys()) == 1:
            messagebox.showwarning(
                self._("dialog.title.select_layer"),
                self._("dialog.text.select_layer")
            )
            return

        self.input(
            "prompt.select_layer",
            self.sc.labels.keys(),
            self.set_active_layer
        )

    @undoable
    def set_active_layer(self, layer):
        """
        Changes the active layer
        """
        previous_layer = self.sc.layer

        self.sc.layer = layer
        self.update()

        yield  # undo

        self.sc.layer = previous_layer

    ###################
    # GENERAL METHODS #
    ###################

    def annotation_mode(self):
        """
        Resumes the annotation mode
        """
        if not self.sc.collection:
            self.input(None, [], None)
            return

        if self.sc.layer in self.sc.qualifiers and self.sc.get_active_label() and not self.sc.get_active_qualifier():
            self.input(
                "prompt.annotation_mode_qualifier",
                self.sc.qualifiers[self.sc.layer],
                self.annotate_qualifier,
                sort=False
            )
        else:
            self.input(
                "prompt.annotation_mode_label",
                self.sc.labels[self.sc.layer],
                self.annotate_label,
                sort=False
            )

    @undoable
    def annotate_label(self, annotation):
        """
        Adds a label to the active segment annotations
        """
        segment = self.sc.get_active()

        segment.set(self.sc.layer, annotation)  # set annotation

        # go to next segment unless a qualifier needs to be set
        if self.sc.layer not in self.sc.qualifiers:
            self.sc.next()

        self.update()

        yield  # undo

        segment.rem(self.sc.layer)

        if self.sc.layer not in self.sc.qualifiers:
            self.sc.previous()

    @undoable
    def annotate_qualifier(self, annotation):
        """
        Adds a qualifier to the active segment annotations
        """
        segment = self.sc.get_active()

        segment.set(self.sc.layer, annotation, qualifier=True)  # set annotation

        self.sc.next()

        self.update()

        yield  # undo

        segment.rem(self.sc.layer, qualifier=True)

        self.sc.previous()

    def manage_motion(self, start, end, text):
        """
        Mouse motion management
        """
        pass

    def manage_click(self, start, end, text):
        """
        Mouse click management
        """
        index = int(self.text.get(start, end).split("\t")[0])

        if self.click_to_link_type is None:
            self.go_to(index)
        else:
            self.link_segment(index, self.click_to_link_type)

    def update(self, t=None, annotation_mode=True):
        """
        Updates the application state
        """
        self.clear_screen()

        # if the collection is not empty
        if self.sc.collection:
            n_previous = self.sc.i if self.sc.i < 50 else 50

            for j in range(self.sc.i - n_previous, self.sc.i):
                self.output_segment(j)

            self.output_segment(self.sc.i, active=True)

            # title with filepath
            self.parent.title("{} - {}".format(self.window_title, self.sc.save_file))

            # status message
            status = "{}: {}".format(
                self._("active_layer"),
                self.sc.layer.title()
            )

            if self.sc.get_active_label():
                status = "{} - {}: {}".format(
                    status,
                    self._("active_label"),
                    self.sc.get_active_label().title()
                )

            if self.sc.get_active_qualifier():
                status = "{} - {}: {}".format(
                    status,
                    self._("active_qualifier"),
                    self.sc.get_active_qualifier().title()
                )

            link_types = set([lt.title() for ls, lt in self.sc.get_active().links])

            if len(link_types) > 0:
                status = "{} - {}: {}".format(
                    status,
                    self._("active_link_types", "s" if len(link_types) > 1 else ""),
                    ", ".join(link_types)
                )
        else:
            # default title
            self.parent.title(self.window_title)

            # status message
            status = "No Collection"

        # filter in status
        if self.sc.filter:
            status = "{} - Filter: {}".format(status, self.sc.filter)

        self.update_status_message(status)

        if annotation_mode:
            self.annotation_mode()

        self.sc.save()

    def output_segment(self, i, active=False):
        """
        Outputs a segment to the text field
        """
        segment = self.sc.collection[i]

        # participant color
        style = ["participant-{}".format(segment.participant), self.clickable_text_tag]

        # active segment is bolded
        if active:
            style.append(Styles.STRONG)

        # columns to be displayed
        columns = [str(i + 1)]  # the index is the first column

        if self.show_id:
            columns.append(str(segment.id))
        if self.show_date:
            columns.append(segment.datetime.strftime("%d-%m-%y"))
        if self.show_time:
            columns.append(segment.datetime.strftime("%H:%M"))
        if self.show_participant:
            columns.append(segment.participant)

        # base text string
        text = "\t".join(columns + ["\t" + segment.raw])

        # output text
        self.output(text, style=style)

        # offset for displaying addendums
        offset = len(text) + 1

        # ignore legacy layers where there is already an annotation
        legacy_layers_to_ignore = []

        # annotations display
        for layer in reversed(sorted(segment.annotations.keys())):
            if segment.has(layer):
                label = segment.get(layer)

                if segment.has(layer, qualifier=True):
                    addendum = " [{} ➔ {}]".format(label, segment.get(layer, qualifier=True))
                else:
                    addendum = " [{}]".format(label)

                self.add_to_last_line(addendum, style="layer-{}".format(layer), offset=offset)
                offset += len(addendum)
                legacy_layers_to_ignore.append(layer)

        # legacy annotations display
        if self.show_legacy:
            for layer in reversed(sorted(segment.legacy.keys())):
                if segment.has(layer, legacy=True) and layer not in legacy_layers_to_ignore:
                    label = segment.get(layer, legacy=True)

                    if segment.has(layer, legacy=True, qualifier=True):
                        addendum = " (({} ➔ {}))".format(label, segment.get(layer, legacy=True, qualifier=True))
                    else:
                        addendum = " (({}))".format(label)

                    self.add_to_last_line(addendum, style="layer-{}".format(layer), offset=offset)
                    offset += len(addendum)

        # links display
        links_by_type = {}

        for ls, lt in segment.links:
            if lt not in links_by_type:
                links_by_type[lt] = []

            links_by_type[lt].append(ls)

        for lt, lls in links_by_type.items():
            links = [str(self.sc.collection.index(ls) + 1) for ls in lls if ls in self.sc.collection]
            addendum = " [{} ⟲ {}]".format(lt, ", ".join(sorted(links)))

            self.add_to_last_line(addendum, style="link-{}".format(lt), offset=offset)
            offset += len(addendum)

        # legacy links display
        if self.show_legacy:
            links_by_type = {}

            for ls, lt in segment.legacy_links:
                if (ls, lt) not in segment.links:  # do not display legacy annotations when there is a normal one
                    if lt not in links_by_type:
                        links_by_type[lt] = []

                    links_by_type[lt].append(ls)

            for lt, lls in links_by_type.items():
                links = [str(self.sc.collection.index(ls) + 1) for ls in lls if ls in self.sc.collection]
                addendum = " (({} ⟲ {}))".format(lt, ", ".join(sorted(links)))

                self.add_to_last_line(addendum, style="link-{}".format(lt), offset=offset)
                offset += len(addendum)

        # note display
        if segment.note is not None:
            self.output("\t\t\t\t ⤷ {}".format(segment.note), style=Styles.ITALIC)
