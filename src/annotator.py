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
from tkinter import filedialog, messagebox, LEFT
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
        self.parent.bind(
            "<Control-j>",
            lambda event: self.select_go_to())

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
            lambda event: self.input_new_tag_name())
        self.parent.bind(
            "<Control-a>",
            lambda event: self.input_new_layer())
        self.parent.bind(
            "<Control-t>",
            lambda event: self.input_new_tag())
        self.parent.bind(
            "<Control-n>",
            lambda event: self.input_new_note())
        self.parent.bind(
            "<Control-f>",
            lambda event: self.select_filter_type())

        #################
        # MENU COMMANDS #
        #################

        # file menu
        self.file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        self.file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_file)
        self.file_menu.add_command(label="Import Data...", accelerator="Ctrl+Shift+I", command=self.import_file)
        self.file_menu.add_command(label="Export Data As...", accelerator="Ctrl+Shift+E", command=self.export_file)
        self.file_menu.add_command(label="Close File", accelerator="Ctrl+W", command=self.close_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Quit", accelerator="Esc", command=self.parent.quit)

        # edit menu
        self.edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        self.edit_menu.add_command(label="Redo", accelerator="Ctrl+Shift+Z", command=self.redo)

        # view menu
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Show Legacy Annotations", accelerator="F2", command=self.show_legacy_annotations)
        self.view_menu.add_command(label="Hide Legacy Annotations", accelerator="F3", command=self.hide_legacy_annotations)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Randomize Participant Colors", accelerator="F4", command=self.generate_participant_colors)

        # filter menu
        self.filter_menu.add_command(label="Filter By Active Layer", accelerator="F5", command=self.filter_by_active_layer)
        self.filter_menu.add_command(label="Filter By Active Label", accelerator="F6", command=self.filter_by_active_label)
        self.filter_menu.add_command(label="Filter By Active Qualifier", accelerator="F7", command=self.filter_by_active_qualifier)

        # taxonomy menu
        self.taxonomy_menu.add_command(label="Import Taxonomy...", accelerator="Ctrl+Alt+I", command=self.import_taxonomy)
        self.taxonomy_menu.add_command(label="Export Taxonomy As...", accelerator="Ctrl+Alt+E", command=self.export_taxonomy)
        self.taxonomy_menu.add_separator()
        self.taxonomy_menu.add_command(label="Set Active Layer As Default", command=self.set_layer_as_default)
        self.taxonomy_menu.add_separator()
        self.taxonomy_menu.add_command(label="Remove Active Label From Taxonomy", command=self.remove_label)
        self.taxonomy_menu.add_command(label="Remove Active Qualifier From Taxonomy", command=self.remove_qualifier)
        self.taxonomy_menu.add_command(label="Remove Active Layer From Taxonomy", command=self.remove_layer)

        ##################
        # INITIALIZATION #
        ##################

        # attempt to load previous save
        self.sc = SegmentCollection.load(SegmentCollection.read_save_path_from_tmp())

        if not self.sc:
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

        # show legacy annotations
        self.show_legacy = True

        # display update
        self.update()

    ################
    # VIEW METHODS #
    ################

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

    def colorize(self):
        """
        Initializes colors
        """
        self.generate_layer_colors()
        self.generate_link_colors()
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

        buttons.update({"[C]hange Layer": self.select_layer})
        buttons.update({"[E]rase Annotation": self.erase_annotation})
        buttons.update({"[L]ink Segment": self.select_link_type})
        buttons.update({"[U]nlink Segment": self.unlink_segment})
        buttons.update({"[S]plit Segment": self.select_split_token})
        buttons.update({"[M]erge Segment": self.merge_segment})
        buttons.update({"[A]dd Layer": self.input_new_layer})
        buttons.update({"Add [T]ag": self.input_new_tag})
        buttons.update({"[R]ename": self.input_new_tag_name})
        buttons.update({"[F]ilter": self.select_filter_type})
        buttons.update({"Add [N]ote": self.input_new_note})

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
            title="Open file",
            filetypes=(("Pickle serialized files", "*.pic"), ("all files", "*.*"))
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
            messagebox.showerror("Open File Error", "The file could not be loaded.\n\nIt may be corrupted or is in the wrong format.")

    def save_file(self):
        """
        Saves a .pic file through dialogue
        """
        path = filedialog.asksaveasfilename(
            initialdir=SegmentCollection.save_dir,
            title="Save as",
            filetypes=(("Pickle serialized files", "*.pic"), ("all files", "*.*"))
        )

        if path == "":
            return  # no path selected

        success = self.sc.save(path=path)

        if not success:
            messagebox.showerror("Save File Error", "The target path is invalid.\n\nThe file could not be saved.")

    def import_file(self):
        """
        Loads a .csv file through dialogue
        """
        path = filedialog.askopenfilename(
            initialdir=SegmentCollection.csv_dir,
            title="Import data file",
            filetypes=(("CSV data files", "*.csv"), ("all files", "*.*"))
        )

        if path == "":
            return  # no file selected

        success = self.sc.import_collection(path)

        if success:
            # choose a taxonomy
            self.import_taxonomy()

            stack().clear()  # reinitializes undo history

            self.colorize()
            self.update()
        else:
            messagebox.showerror("Open File Error", "The file could not be loaded.\n\nIt may be corrupted or is in the wrong format.")

    def export_file(self):
        """
        Saves a .csv or .json file through dialogue
        """
        path = filedialog.asksaveasfilename(
            initialdir=SegmentCollection.out_dir,
            title="Export as",
            filetypes=(("CSV data files", "*.csv"), ("JSON data files", "*.json"))
        )

        if path == "":
            return  # no path selected

        success = self.sc.export_collection(path)

        if not success:
            messagebox.showerror("Export File Error", "The target path is invalid.\n\nThe file could not be created.")

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
            title="Open taxonomy file",
            filetypes=(("JSON taxonomy file", "*.json"), ("all files", "*.*"))
        )

        if path == "":
            return  # no path selected

        success = self.sc.import_taxonomy(path)

        if success:
            self.colorize()
            self.update()
        else:
            messagebox.showerror("Import Taxonomy Error", "The file could not be loaded.\n\nIt may be corrupted or is in the wrong format.")

    def export_taxonomy(self):
        """
        Saves a .json taxonomy file through dialogue
        """
        path = filedialog.asksaveasfilename(
            initialdir=SegmentCollection.custom_taxo_dir,
            title="Export taxonomy as",
            filetypes=(("JSON data files", "*.json"), ("all files", "*.*"))
        )

        if path == "":
            return  # no path selected

        success = self.sc.export_taxonomy(path)

        if not success:
            messagebox.showerror("Export Taxonomy Error", "The target path is invalid.\n\nThe file could not be created.")

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
        self.input("select destination index", [], self.go_to, free=True)

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
        if messagebox.askyesno("Delete Segment", "Are you sure you want to remove the active segment from the collection?"):
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
            self.input("select token on which to split", segment.tokens[:-1], self.split_segment, sort=False)

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
        annotation = segment.annotations[self.sc.layer]

        del segment.annotations[self.sc.layer]

        self.update()

        yield  # undo

        segment.annotations[self.sc.layer] = annotation

    def select_link_type(self):
        """
        Inputs a link type
        """
        if len(self.sc.links.keys()) == 0:
            messagebox.showwarning("No Link Available", "The current taxonomy doesn't have any link types defined.")
            return

        if self.sc.i > 0:  # first segment can't be linked
            self.input("select link type", self.sc.links.keys(), self.select_link_target)

    def select_link_target(self, link_type):
        """
        Set a link type then input link target
        """
        i = self.sc.i - 50 if self.sc.i - 50 >= 1 else 1

        # input target segment
        self.input("select link target", reversed(list(range(i, self.sc.i + 1))), lambda n, link_t=link_type: self.link_segment(n, link_t), sort=False)

    @undoable
    def link_segment(self, number, link_type):
        """
        Links the active segment to another
        """
        number = int(number) - 1

        segment = self.sc.get_active()
        segment.links.append((self.sc.collection[number], link_type))
        self.sc.collection[number].linked.append((segment, link_type))

        self.update()

        yield  # undo

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
        self.input("input note text", [], self.set_note, free=True)

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

    def input_new_layer(self):
        """
        Inputs name of a new layer
        """
        self.input("input new layer name", [], self.add_layer, free=True)

    @undoable
    def add_layer(self, layer):
        """
        Adds a new layer
        """
        self.sc.add_layer(layer)
        self.update()

        yield  # undo

        self.sc.delete_layer(layer)

    def input_new_tag(self):
        """
        Inputs name of a new label or qualifier
        """
        if self.sc.layer in self.sc.qualifiers and self.sc.get_active_label() and not self.sc.get_active_qualifier():
            self.input("input new qualifier name", [], self.add_qualifier, free=True)
        else:
            self.input("input new label name", [], self.add_label, free=True)

    @undoable
    def add_label(self, label):
        """
        Adds a new label
        """
        self.sc.add_label(self.sc.layer, label)
        self.update()

        yield  # undo

        self.sc.delete_label(self.sc.layer, label)

    @undoable
    def add_qualifier(self, qualifier):
        """
        Adds a new label
        """
        self.sc.add_qualifier(self.sc.layer, qualifier)
        self.update()

        yield  # undo

        self.sc.delete_qualifier(self.sc.layer, qualifier)

    @undoable
    def remove_label(self):
        """
        Removes the active segment's label from the taxonomy
        """
        sc = deepcopy(self.sc)

        segment = self.sc.get_active()

        if self.sc.layer in segment.annotations:
            label = segment.annotations[self.sc.layer]["label"]
            if messagebox.askyesno("Delete Label", "Are you sure you want to remove the {} label from the taxonomy?".format(label)):
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
            qualifier = segment.annotations[self.sc.layer]["qualifier"]
            if messagebox.askyesno("Delete Qualifier", "Are you sure you want to remove the {} qualifier from the taxonomy?".format(qualifier)):
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
        if messagebox.askyesno("Delete Layer", "Are you sure you want to remove the {} layer from the taxonomy?".format(self.sc.layer)):
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

    def input_new_tag_name(self):
        """
        Inputs the new name of a label or qualifier
        """
        segment = self.sc.get_active()

        if self.sc.layer in segment.annotations:
            if "qualifier" in segment.annotations[self.sc.layer]:
                self.input(
                    "select layer, label or qualifier to rename",
                    list(segment.annotations[self.sc.layer].values()) + [self.sc.layer],
                    self.select_what_to_rename
                )
            else:
                self.input(
                    "select layer or label to rename",
                    list(segment.annotations[self.sc.layer].values()) + [self.sc.layer],
                    self.select_what_to_rename
                )
        else:
            self.input(
                "input new layer name",
                [],
                self.rename_layer,
                placeholder=self.sc.layer,
                free=True
            )

    def select_what_to_rename(self, text):
        """
        Select either a label or a qualifier to rename
        """
        segment = self.sc.get_active()

        if text == segment.annotations[self.sc.layer]["label"]:
            self.input(
                "input new label name",
                [],
                self.rename_label,
                placeholder=text,
                free=True
            )
        elif text == self.sc.layer:
            self.input(
                "input new layer name",
                [],
                self.rename_layer,
                placeholder=text,
                free=True
            )
        else:
            self.input(
                "input new qualifier name",
                [],
                self.rename_qualifier,
                placeholder=text,
                free=True
            )

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
                segment.annotations[self.sc.layer]["label"],
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
                segment.annotations[self.sc.layer]["qualifier"],
                qualifier
            )

            self.update()

        yield  # undo

        if qualifier:
            self.sc = sc

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

    def input_new_layer_name(self):
        """
        Inputs the new name of the active layer
        """
        self.input("input new layer name", [], lambda name: self.rename_layer(name), placeholder=self.sc.layer, free=True)

    #################
    # VIEW COMMANDS #
    #################

    def select_filter_type(self):
        """
        Selects a filter type
        """
        if not self.sc.filter:
            self.input("select filter type", ["Layer", "Legacy Layer", "Label", "Legacy Label", "Qualifier", "Legacy Qualifier"], self.filter)
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
        if filter_type == "Layer":
            self.input("select layer", self.sc.labels.keys(), self.filter_by_layer)

        if filter_type == "Legacy Layer":
            legacy_layers = []

            for segment in self.sc.full_collection:
                for layer in segment.legacy.keys():
                    legacy_layers.append(layer)

            self.input("select legacy layer", set(legacy_layers), self.filter_by_legacy_layer)

        if filter_type == "Label":
            labels = []

            for layer in self.sc.labels:
                labels += self.sc.labels[layer]

            self.input("select label", set(labels), self.filter_by_label)

        if filter_type == "Legacy Label":
            legacy_labels = []

            for segment in self.sc.full_collection:
                for layer in segment.legacy.keys():
                    if "label" in segment.legacy[layer]:
                        legacy_labels.append(segment.legacy[layer]["label"])

            self.input("select legacy label", set(legacy_labels), self.filter_by_legacy_label)

        if filter_type == "Qualifier":
            qualifiers = []

            for layer in self.sc.qualifiers:
                qualifiers += self.sc.qualifiers[layer]

            self.input("select qualifier", set(qualifiers), self.filter_by_qualifier)

        if filter_type == "Legacy Qualifier":
            legacy_qualifiers = []

            for segment in self.sc.full_collection:
                for layer in segment.legacy.keys():
                    if "qualifier" in segment.legacy[layer]:
                        legacy_qualifiers.append(segment.legacy[layer]["qualifier"])

            self.input("select legacy qualifier", set(legacy_qualifiers), self.filter_by_legacy_qualifier)

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
                if "label" in segment.annotations[layer] and label == segment.annotations[layer]["label"]:
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
                if "label" in segment.legacy[layer] and label == segment.legacy[layer]["label"]:
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
                if "qualifier" in segment.annotations[layer] and qualifier == segment.annotations[layer]["qualifier"]:
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
                if "qualifier" in segment.legacy[layer] and qualifier == segment.legacy[layer]["qualifier"]:
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
            messagebox.showwarning("No Other Layers", "The current taxonomy doesn't have any other layers.")
            return

        self.input("select layer", self.sc.labels.keys(), self.set_active_layer)

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
            self.input("select qualifier to apply", self.sc.qualifiers[self.sc.layer], self.annotate_qualifier, sort=False)
        else:
            self.input("select label to apply", self.sc.labels[self.sc.layer], self.annotate_label, sort=False)

    @undoable
    def annotate_label(self, annotation):
        """
        Adds a label to the active segment annotations
        """
        segment = self.sc.get_active()

        previous_annotations = segment.annotations.copy()

        # create dict if layer not in annotations
        if self.sc.layer not in segment.annotations:
            segment.annotations[self.sc.layer] = {}

        segment.annotations[self.sc.layer]["label"] = annotation

        if self.sc.layer not in self.sc.qualifiers:
            self.sc.next()

        self.update()

        yield  # undo

        segment.annotations = previous_annotations

        if self.sc.layer not in self.sc.qualifiers:
            self.sc.previous()

    @undoable
    def annotate_qualifier(self, annotation):
        """
        Adds a qualifier to the active segment annotations
        """
        segment = self.sc.get_active()

        # create dict if layer not in annotations
        if self.sc.layer not in segment.annotations:
            segment.annotations[self.sc.layer] = {}

        segment.annotations[self.sc.layer]["qualifier"] = annotation
        self.sc.next()

        self.update()

        yield  # undo

        del segment.annotations[self.sc.layer]["qualifier"]

        self.sc.previous()

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
            status = "Active Layer: |{}|".format(self.sc.layer.title())

            if self.sc.get_active_label():
                status = "{} - Active Label: [{}]".format(status, self.sc.get_active_label().title())

            if self.sc.get_active_qualifier():
                status = "{} - Active Qualifier: [{}]".format(status, self.sc.get_active_qualifier().title())
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
        style = ["participant-{}".format(segment.participant)]

        # active segment is bolded
        if active:
            style.append(Styles.STRONG)

        # segment base text
        text = "{}\t{}\t{}  \t\t{}".format(i + 1, segment.time, segment.participant, segment.raw)
        self.output(text, style=style)

        # offset for displaying addendums
        offset = len(text) + 1

        # ignore legacy layers where there is already an annotation
        legacy_layers_to_ignore = []

        # annotations display
        for layer in reversed(sorted(segment.annotations.keys())):
            if "label" in segment.annotations[layer]:
                if "qualifier" in segment.annotations[layer]:
                    addendum = " [{} ➔ {}]".format(segment.annotations[layer]["label"], segment.annotations[layer]["qualifier"])
                else:
                    addendum = " [{}]".format(segment.annotations[layer]["label"])

                self.add_to_last_line(addendum, style="layer-{}".format(layer), offset=offset)
                offset += len(addendum)
                legacy_layers_to_ignore.append(layer)

        # legacy annotations display
        if self.show_legacy:
            for layer in reversed(sorted(segment.legacy.keys())):
                if "label" in segment.legacy[layer] and layer not in legacy_layers_to_ignore:
                    if "qualifier" in segment.legacy[layer]:
                        addendum = " (({} ➔ {}))".format(segment.legacy[layer]["label"], segment.legacy[layer]["qualifier"])
                    else:
                        addendum = " (({}))".format(segment.legacy[layer]["label"])

                    self.add_to_last_line(addendum, style="layer-{}".format(layer), offset=offset)
                    offset += len(addendum)

        # links display
        for ls, lt in segment.links:
            if ls in self.sc.collection:
                addendum = " ⟲ {}".format(self.sc.collection.index(ls) + 1)
            else:
                addendum = " ⟲"

            self.add_to_last_line(addendum, style="link-{}".format(lt), offset=offset)
            offset += len(addendum)

        # note display
        if segment.note is not None:
            self.output("\t\t\t\t ⤷ {}".format(segment.note), style=Styles.ITALIC)
