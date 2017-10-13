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
from datetime import datetime
from tkinter import filedialog, messagebox, LEFT
from tkinter.ttk import Button

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
            "<Control-E>",
            lambda event: self.export_file())
        self.parent.bind(
            "<Control-w>",
            lambda event: self.close_file())
        self.parent.bind(
            "<Control-T>",
            lambda event: self.export_taxonomy())
        self.parent.bind(
            "<Control-I>",
            lambda event: self.import_taxonomy())

        # other shortcuts
        self.parent.bind(
            "<Delete>",
            lambda event: self.delete_segment())
        self.parent.bind(
            "<F3>",
            lambda event: self.generate_participant_colors())
        self.parent.bind(
            "<F4>",
            lambda event: self.filter_by_layer())
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
            "<Control-d>",
            lambda event: self.select_layer())
        self.parent.bind(
            "<Control-r>",
            lambda event: self.input_new_label_name())
        self.parent.bind(
            "<Control-a>",
            lambda event: self.input_new_label())
        self.parent.bind(
            "<Control-n>",
            lambda event: self.input_new_note())
        self.parent.bind(
            "<Control-f>",
            lambda event: self.filter_by_label())

        #################
        # MENU COMMANDS #
        #################

        # file menu
        self.file_menu.add_command(label="Open File...", accelerator="Ctrl+O", command=self.open_file)
        self.file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_file)
        self.file_menu.add_command(label="Export As...", accelerator="Ctrl+Shift+E", command=self.export_file)
        self.file_menu.add_command(label="Close File", accelerator="Ctrl+W", command=self.close_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Quit", accelerator="Esc", command=self.parent.quit)

        # edit menu
        self.edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        self.edit_menu.add_command(label="Redo", accelerator="Ctrl+Shift+Z", command=self.redo)

        # view menu
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Randomize Participant Colors", accelerator="F3", command=self.generate_participant_colors)

        # filter menu
        self.filter_menu.add_command(label="Filter By Active Label", accelerator="Ctrl+F", command=self.filter_by_label)
        self.filter_menu.add_command(label="Filter By Active Layer", accelerator="F4", command=self.filter_by_layer)

        # taxonomy menu
        self.taxonomy_menu.add_command(label="Import Taxonomy...", accelerator="Ctrl+Shift+I", command=self.import_taxonomy)
        self.taxonomy_menu.add_command(label="Export Taxonomy As...", accelerator="Ctrl+Shift+T", command=self.export_taxonomy)
        self.taxonomy_menu.add_separator()
        self.taxonomy_menu.add_command(label="Set Active Layer As Default", command=self.set_layer_as_default)
        self.taxonomy_menu.add_command(label="Remove Active Label From Taxonomy", command=self.remove_label)
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

        # undo/redo history initialization
        self.undo_history = []
        self.redo_history = [self.sc]  # must be pre-filled with current state

        # display update
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

        buttons.update({"Select [D]imension": self.select_layer})
        buttons.update({"[E]rase Annotation": self.erase_annotation})
        buttons.update({"[L]ink Segment": self.select_link_type})
        buttons.update({"[U]nlink Segment": self.unlink_segment})
        buttons.update({"[S]plit Segment": self.select_split_token})
        buttons.update({"[M]erge Segment": self.merge_segment})
        buttons.update({"[A]dd Label": self.input_new_label})
        buttons.update({"[R]ename Label": self.input_new_label_name})
        buttons.update({"[F]ilter By Label": self.filter_by_label})
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
        Loads a .csv or .pic file through dialogue
        """
        path = filedialog.askopenfilename(
            initialdir=SegmentCollection.save_dir,
            title="Open data file",
            filetypes=(("Pickle serialized files", "*.pic"), ("CSV data files", "*.csv"), ("all files", "*.*"))
        )

        if path == "":
            return  # no file selected

        sc = SegmentCollection.load(path)

        if sc:
            self.sc = sc
            self.undo_history = []  # reinitializes undo history

            # choose a taxonomy if none is set
            if self.sc.taxonomy is None:
                self.import_taxonomy()

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

        if success:
            self.update(annotation_mode=False)
        else:
            messagebox.showerror("Save File Error", "The target path is invalid.\n\nThe file could not be saved.")

    def export_file(self):
        """
        Saves a .csv or .json file through dialogue
        """
        path = filedialog.asksaveasfilename(
            initialdir=SegmentCollection.data_dir,
            title="Export as",
            filetypes=(("JSON data files", "*.json"), ("CSV data files", "*.csv"))
        )

        if path == "":
            return  # no path selected

        success = self.sc.export_collection(path)

        if success:
            self.update(annotation_mode=False)
        else:
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
            filetypes=(("JSON taxonomy file", "*.json"), ("all files", "*.*"))
        )

        if path == "":
            return  # no path selected

        success = self.sc.export_taxonomy(path)

        if success:
            self.update(annotation_mode=False)
        else:
            messagebox.showerror("Export Taxonomy Error", "The target path is invalid.\n\nThe file could not be created.")

    #######################
    # NAVIGATION COMMANDS #
    #######################

    def go_down(self, n):
        """
        Moves to an ulterior segment
        """
        # cycles through the collection
        for i in range(0, n):
            self.sc.next()

        self.update()

    def go_up(self, n):
        """
        Moves to a previous segment
        """
        # cycles backards through the collection
        for i in range(0, n):
            self.sc.previous()

        self.update()

    def select_go_to(self):
        """
        Inputs a target segment to go to
        """
        self.input("select destination index", range(1, len(self.sc.collection)), self.go_to)

    def go_to(self, number):
        """
        Moves to a specific segment by index in collection
        """
        self.sc.i = int(number) - 1
        self.update()

    ###############################
    # SEGMENT MANAGEMENT COMMANDS #
    ###############################

    def delete_segment(self):
        """
        Deletes the active segment
        """
        if messagebox.askyesno("Delete Segment", "Are you sure you want to remove the active segment from the collection?"):
            segment = self.sc.get_active()

            self.sc.remove(segment)

            self.update()

    def merge_segment(self):
        """
        Merges the active segment to its preceding one
        """
        segment = self.sc.get_active()
        previous = self.sc.collection[self.sc.i - 1]

        if segment.participant == previous.participant:  # can only merge segments from the same participant
            segment.merge(previous)

            self.sc.remove(previous)
            self.sc.previous()

            self.update()

    def select_split_token(self):
        """
        Inputs the token on which the active segment will be split
        """
        segment = self.sc.get_active()
        if len(segment.tokens) > 1:
            self.input("select token on which to split", segment.tokens[:-1], self.split_segment, sort=False)

    def split_segment(self, token):
        """
        Splits the active segment in two
        """
        segment = self.sc.get_active()
        splits = segment.split(token)

        for split in reversed(splits):
            self.sc.insert_after_active(split)

        self.sc.remove(segment)

        self.update()

    ##################################
    # ANNOTATION MANAGEMENT COMMANDS #
    ##################################

    def erase_annotation(self):
        """
        Erases the active segment's annotation for the active layer
        """
        segment = self.sc.get_active()

        if self.sc.layer in segment.annotations:
            del segment.annotations[self.sc.layer]

            self.update()

    def select_link_type(self):
        """
        Inputs a link type
        """
        if self.sc.i > 0:  # first segment can't be linked
            self.input("select link type", self.sc.links.keys(), self.select_link_target)

    def select_link_target(self, link_type):
        """
        Set a link type then input link target
        """
        # input target segment
        self.input("select link target", range(1, self.sc.i + 1), lambda n, link_t=link_type: self.link_segment(n, link_t))

    def link_segment(self, number, link_type):
        """
        Links the active segment to another
        """
        number = int(number) - 1

        segment = self.sc.get_active()
        segment.links.append((self.sc.collection[number], link_type))
        self.sc.collection[number].linked.append((segment, link_type))

        self.update()

    def unlink_segment(self):
        """
        Removes links emanating from the active segment
        """
        segment = self.sc.get_active()

        while segment.links:
            ls, lt = segment.links[0]
            segment.remove_links(ls)

        self.update()

    def input_new_note(self):
        """
        Inputs a note for the active segment
        """
        self.input("input note text", [], self.set_note, free=True)

    def set_note(self, note):
        """
        Sets the note of the segment
        """
        segment = self.sc.get_active()

        if note != "":
            segment = self.sc.get_active()
            segment.note = note
        else:
            segment.note = None

        self.update()

    ################################
    # TAXONOMY MANAGEMENT COMMANDS #
    ################################

    def input_new_label(self):
        """
        Inputs name of a new label
        """
        segment = self.sc.get_active()

        if self.sc.layer in self.sc.values and self.sc.layer in segment.annotations and "label" in segment.annotations[self.sc.layer] and "qualifier" not in segment.annotations[self.sc.layer]:
            self.input("input new qualifier name", [], self.add_qualifier, free=True)
        else:
            self.input("input new label name", [], self.add_label, free=True)

    def add_label(self, label):
        """
        Adds a new label
        """
        self.sc.add_label(self.sc.layer, label)
        self.update()

    def add_qualifier(self, qualifier):
        """
        Adds a new label
        """
        self.sc.add_qualifier(self.sc.layer, qualifier)
        self.update()

    def remove_label(self):
        """
        Removes the active segment's label from the taxonomy
        """
        segment = self.sc.get_active()

        if self.sc.layer in segment.annotations:
            label = segment.annotations[self.sc.layer]
            if messagebox.askyesno("Delete Label", "Are you sure you want to remove the {} label from the taxonomy?".format(label)):
                self.sc.delete_label(self.sc.layer, label)
                self.update()

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
            self.sc.delete_layer(self.sc.layer)
            self.update()

    def input_new_label_name(self):
        """
        Inputs the name of a new label
        """
        segment = self.sc.get_active()

        if self.sc.layer in segment.annotations:
            if "qualifier" in segment.annotations[self.sc.layer]:
                self.input("select label or qualifier to rename", segment.annotations[self.sc.layer].values(), self.select_label_or_qualifier_to_rename)
            else:
                self.input("input new label name", [], self.rename_label_or_qualifier, free=True)

    def select_label_or_qualifier_to_rename(self, label):
        """
        Select either a label or a qualifier to rename
        """
        segment = self.sc.get_active()

        if label == segment.annotations[self.sc.layer]["label"]:
            self.input("input new label name", [], self.rename_label_or_qualifier, free=True)
        else:
            self.input("input new qualifier name", [], lambda label: self.rename_label_or_qualifier(label, qualifier=True), free=True)

    def rename_label_or_qualifier(self, label, qualifier=False):
        """
        Renames a label
        """
        segment = self.sc.get_active()

        if label:
            if qualifier:
                self.sc.change_qualifier(
                    self.sc.layer,
                    segment.annotations[self.sc.layer]["qualifier"],
                    label
                )
            else:
                self.sc.change_label(
                    self.sc.layer,
                    segment.annotations[self.sc.layer]["label"],
                    label
                )

        self.update()

    #################
    # VIEW COMMANDS #
    #################

    def filter_by_label(self):
        """
        Button to filter segments by label
        """
        segment = self.sc.get_active()

        if not self.sc.filter and (self.sc.layer in segment.annotations or self.sc.layer in segment.legacy):
            if self.sc.layer in segment.annotations:
                self.sc.collection = [s for s in self.sc.full_collection if self.sc.layer in s.annotations and s.annotations[self.sc.layer]["label"].startswith(segment.annotations[self.sc.layer]["label"])]
                self.sc.filter = "[{}]".format(segment.annotations[self.sc.layer]["label"])
            elif self.sc.layer in segment.legacy:
                self.sc.collection = [s for s in self.sc.full_collection if self.sc.layer in s.legacy and s.legacy[self.sc.layer].startswith(segment.legacy[self.sc.layer]["label"])]
                self.sc.filter = "(({}))".format(segment.legacy[self.sc.layer]["label"])
        else:
            self.sc.i = self.sc.full_collection.index(segment)
            self.sc.collection = self.sc.full_collection.copy()
            self.sc.filter = False

        self.update()

    def filter_by_layer(self):
        if not self.sc.filter:
            self.sc.collection = [s for s in self.sc.full_collection if self.sc.layer in s.annotations or self.sc.layer in s.legacy]
            self.sc.filter = "|{}|".format(self.sc.layer)

            # look first for a target from the active segment to the end, and then backwards from the position of the active segment
            for i in list(range(self.sc.i, len(self.sc.full_collection))) + list(reversed(range(0, self.sc.i))):
                segment = self.sc.full_collection[i]
                if segment in self.sc.collection:
                    # adjust the current index in the new collection
                    self.sc.i = self.sc.collection.index(segment)
                    break
        else:
            self.sc.i = self.sc.full_collection.index(self.sc.get_active())
            self.sc.collection = self.sc.full_collection.copy()
            self.sc.filter = False

        self.update()

    ######################
    # UNDO/REDO COMMANDS #
    ######################

    def undo(self):
        """
        Undo command
        """
        # if there is a previous state in history to go to
        if len(self.undo_history) > 1:
            self.redo_history.append(self.undo_history[-1])
            del self.undo_history[-1]
            self.sc = self.undo_history.pop()  # change to previous state in history
            self.update()  # update without saving state to history

    def redo(self):
        """
        Redo command
        """
        # if there is a next state in history to go to
        if len(self.redo_history) > 1:
            self.undo_history.append(self.redo_history[-1])
            del self.undo_history[-1]
            self.sc = self.redo_history.pop()  # change to previous state in history
            self.update()  # update without saving state to history

    ######################
    # DIMENSION COMMANDS #
    ######################

    def select_layer(self):
        """
        Inputs a layer
        """
        self.input("select layer", self.sc.labels.keys(), self.set_active_layer)

    def set_active_layer(self, layer):
        """
        Changes the active layer
        """
        self.sc.layer = layer
        self.update()

    ###################
    # GENERAL METHODS #
    ###################

    def annotation_mode(self):
        """
        Resumes the annotation mode
        """
        if self.sc.layer is None:
            self.input(None, [], None)
            return

        segment = self.sc.get_active()

        if self.sc.layer in self.sc.values and self.sc.layer in segment.annotations and "label" in segment.annotations[self.sc.layer] and "qualifier" not in segment.annotations[self.sc.layer]:
            self.input("select qualifier to apply", self.sc.values[self.sc.layer], self.annotate_qualifier, sort=False)
        else:
            self.input("select label to apply", self.sc.labels[self.sc.layer], self.annotate_label, sort=False)

    def annotate_label(self, annotation):
        """
        Adds a label to the active segment annotations
        """
        segment = self.sc.get_active()

        # create dict if layer not in annotations
        if self.sc.layer not in segment.annotations:
            segment.annotations[self.sc.layer] = {}

        segment.annotations[self.sc.layer]["label"] = annotation

        if self.sc.layer not in self.sc.values:
            self.sc.next()

        self.update()

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

    def update(self, t=None, ignore_history=False, annotation_mode=True):
        """
        Updates the application state
        """
        self.clear_screen()

        # if a file is opened and a layer is set
        if self.sc.layer is not None:
            n_previous = self.sc.i if self.sc.i < 50 else 50

            for j in range(self.sc.i - n_previous, self.sc.i):
                self.output_segment(j)

            self.output_segment(self.sc.i, active=True)

            # title with filepath
            self.parent.title("{} - {}".format(self.window_title, self.sc.save_file))
        else:
            # default title
            self.parent.title(self.window_title)

        # layer in status
        status = "Layer: {}".format(self.sc.layer.title()) if self.sc.layer else "No Collection"

        # filter in status
        if self.sc.filter:
            status = "{} - Filter: {}".format(status, self.sc.filter)

        self.update_status_message(status)

        if annotation_mode:
            self.annotation_mode()

        # undo history management
        if not ignore_history:
            if len(self.undo_history) >= 100:
                del self.undo_history[0]
            self.undo_history.append(deepcopy(self.sc))

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

        # annotations display
        for layer in reversed(sorted(segment.annotations.keys())):
            if "qualifier" in segment.annotations[layer]:
                addendum = " [{} ➔ {}]".format(segment.annotations[layer]["label"], segment.annotations[layer]["qualifier"])
            else:
                addendum = " [{}]".format(segment.annotations[layer]["label"])

            self.add_to_last_line(addendum, style="layer-{}".format(layer), offset=offset)
            offset += len(addendum)

        # legacy annotations display
        for layer in reversed(sorted(segment.legacy.keys())):
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
