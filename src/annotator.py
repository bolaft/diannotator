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
from tkinter import Button, filedialog, LEFT

from colors import generate_random_color
from interface import GraphicalUserInterface, WHITE, GRAY
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

        # load / save shortcuts
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
            lambda event: self.filter_by_dimension())
        self.parent.bind(
            "<Control-z>",
            lambda event: self.undo())

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
            lambda event: self.select_dimension())
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

        self.file_menu.add_separator()

        self.file_menu.add_command(label="Quit", accelerator="Esc", command=self.parent.quit)

        # edit menu
        self.edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)

        # view menu
        self.view_menu.add_command(label="Randomize Participant Colors", accelerator="F3", command=self.generate_participant_colors)

        # filter menu
        self.filter_menu.add_command(label="Filter By Active Label", accelerator="Ctrl+F", command=self.filter_by_label)
        self.filter_menu.add_command(label="Filter By Active Dimension", accelerator="F4", command=self.filter_by_dimension)

        # taxonomy menu
        self.taxonomy_menu.add_command(label="Import Taxonomy...", accelerator="Ctrl+Shift+I", command=self.import_taxonomy)
        self.taxonomy_menu.add_command(label="Export Taxonomy As...", accelerator="Ctrl+Shift+T", command=self.export_taxonomy)
        self.taxonomy_menu.add_separator()
        self.taxonomy_menu.add_command(label="Remove Active Label From Taxonomy", command=self.remove_label)

        ##################
        # INITIALIZATION #
        ##################

        # attempt to load previous save
        self.sc = SegmentCollection.load(SegmentCollection.read_save_path_from_tmp())

        if not self.sc:
            # initializing the segment collection
            self.open_file()  # load command

        # colorization
        self.generate_dimension_colors()
        self.generate_link_colors()
        self.generate_participant_colors()

        # make a backup of the collection
        self.sc.save(
            name="{}backup/auto-{}.pic".format(SegmentCollection.save_dir, datetime.now().strftime("%d-%m-%y_%X")),
            backup=True
        )

        # undo history initialization
        self.undo_history = []

        # special buttons
        self.make_special_buttons()

        # display update
        self.update()

    #################
    # COLOR METHODS #
    #################

    def generate_participant_colors(self):
        """
        Adds a color tag per participant to the text widget
        """
        for participant in set([s.participant for s in self.sc.full_collection]):
            self.add_tag(
                "participant-{}".format(participant),
                foreground=generate_random_color()
            )

    def generate_dimension_colors(self):
        """
        Adds a color tag per dimension to the text widget
        """
        for dimension, color in self.sc.colors.items():
            self.add_tag(
                "dimension-{}".format(dimension),
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

        buttons.update({"Select [D]imension": self.select_dimension})
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
                background=WHITE,
                foreground=GRAY,
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
        loaded_sc = SegmentCollection.load(filedialog.askopenfilename(
            initialdir=SegmentCollection.save_dir,
            title="Open data file",
            filetypes=(("Pickle serialized files", "*.pic"), ("CSV data files", "*.csv"), ("all files", "*.*"))
        ))

        if loaded_sc:
            self.sc = loaded_sc

            self.undo_history = []  # reinitializes undo history

            # choose a taxonomy if none is set
            if self.sc.taxonomy is None:
                self.import_taxonomy()

            self.update(annotation_mode=False)

    def save_file(self):
        """
        Saves a .pic file through dialogue
        """
        self.sc.save(name=filedialog.asksaveasfilename(
            initialdir=SegmentCollection.save_dir,
            title="Save as",
            filetypes=(("Pickle serialized files", "*.pic"), ("all files", "*.*"))
        ))

        self.update(annotation_mode=False)

    def export_file(self):
        """
        Saves a .csv or .json file through dialogue
        """
        self.sc.export_collection(filedialog.asksaveasfilename(
            initialdir=SegmentCollection.data_dir,
            title="Export as",
            filetypes=(("JSON data files", "*.json"), ("CSV data files", "*.csv"))
        ))

        self.update(annotation_mode=False)

    def import_taxonomy(self):
        """
        Loads a .json taxonomy file through dialogue
        """
        taxonomy_path = filedialog.askopenfilename(
            initialdir=SegmentCollection.taxo_dir,
            title="Open taxonomy file",
            filetypes=(("JSON taxonomy file", "*.json"), ("all files", "*.*"))
        )

        self.sc.import_taxonomy(taxonomy_path)
        self.generate_dimension_colors()
        self.generate_link_colors()
        self.update()

    def export_taxonomy(self):
        """
        Saves a .json taxonomy file through dialogue
        """
        taxonomy_path = filedialog.asksaveasfilename(
            initialdir=SegmentCollection.taxo_dir,
            title="Export taxonomy as",
            filetypes=(("JSON taxonomy file", "*.json"), ("all files", "*.*"))
        )

        self.sc.export_taxonomy(taxonomy_path)

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
        self.input(range(1, len(self.sc.collection)), self.go_to)

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
        self.input(segment.tokens[:-1], self.split_segment, sort=False)

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
        Erases the active segment's annotation for the active dimension
        """
        segment = self.sc.get_active()

        if self.sc.dimension in segment.annotations:
            del segment.annotations[self.sc.dimension]

            self.update()

    def select_link_type(self):
        """
        Inputs a link type
        """
        if self.sc.i > 0:  # first segment can't be linked
            self.input(self.sc.links.keys(), self.select_link_target)

    def select_link_target(self, link_type):
        """
        Set a link type then input link target
        """
        # input target segment
        self.input(range(1, self.sc.i + 1), lambda n, link_t=link_type: self.link_segment(n, link_t))

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
        self.input([], self.set_note, free=True)

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

        if self.sc.dimension in self.sc.values and self.sc.dimension in segment.annotations and segment.annotations[self.sc.dimension] in self.sc.labels[self.sc.dimension]:
            self.input([], self.add_qualifier, free=True)
        else:
            self.input([], self.add_label, free=True)

    def add_label(self, label):
        """
        Adds a new label
        """
        self.sc.add_label(self.sc.dimension, label)
        self.update()

    def add_qualifier(self, qualifier):
        """
        Adds a new label
        """
        self.sc.add_qualifier(self.sc.dimension, qualifier)
        self.update()

    def remove_label(self):
        """
        Removes the active segment's label from the taxonomy
        """
        segment = self.sc.get_active()

        if self.sc.dimension in segment.annotations:
            self.sc.delete_label(self.sc.dimension, segment.annotations[self.sc.dimension])
            self.update()

    def input_new_label_name(self):
        """
        Inputs the name of a new label
        """
        segment = self.sc.get_active()

        if self.sc.dimension in segment.annotations:
            self.input([], self.rename_label, free=True)

    def rename_label(self, label):
        """
        Renames a label
        """
        segment = self.sc.get_active()

        if label:
            self.sc.change_label(
                self.sc.dimension,
                segment.annotations[self.sc.dimension],
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

        if not self.sc.filter and (self.sc.dimension in segment.annotations or self.sc.dimension in segment.legacy):
            if self.sc.dimension in segment.annotations:
                self.sc.collection = [s for s in self.sc.full_collection if self.sc.dimension in s.annotations and s.annotations[self.sc.dimension].startswith(segment.annotations[self.sc.dimension].split(" ➔ ")[0])]
                self.sc.filter = "[{}]".format(segment.annotations[self.sc.dimension].split(" ➔ ")[0])
            elif self.sc.dimension in segment.legacy:
                self.sc.collection = [s for s in self.sc.full_collection if self.sc.dimension in s.legacy and s.legacy[self.sc.dimension].startswith(segment.legacy[self.sc.dimension].split(" ➔ ")[0])]
                self.sc.filter = "(({}))".format(segment.legacy[self.sc.dimension].split(" ➔ ")[0])
        else:
            self.sc.collection = self.sc.full_collection.copy()
            self.sc.filter = False

        for i, s in enumerate(self.sc.collection):
            if s == segment:
                self.sc.i = i

        self.update()

    def filter_by_dimension(self):
        if not self.sc.filter:
            self.sc.collection = [s for s in self.sc.full_collection if self.sc.dimension in s.annotations or self.sc.dimension in s.legacy]
            self.sc.filter = "|{}|".format(self.sc.dimension)

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

    #################
    # UNDO COMMANDS #
    #################

    def undo(self):
        """
        Undoes one change
        """
        # if there is a previous state in history to go to
        if len(self.undo_history) > 1:
            del self.undo_history[-1]  # remove current state from history

            self.sc = self.undo_history[-1]  # change to previous state in history
            self.update(backup=False)  # update without saving state to history

    ######################
    # DIMENSION COMMANDS #
    ######################

    def select_dimension(self):
        """
        Inputs a dimension
        """
        self.input(self.sc.labels.keys(), self.set_active_dimension)

    def set_active_dimension(self, dimension):
        """
        Changes the active dimension
        """
        self.sc.dimension = dimension
        self.update()

    ###################
    # GENERAL METHODS #
    ###################

    def annotation_mode(self):
        """
        Resumes the annotation mode
        """
        segment = self.sc.get_active()

        if self.sc.dimension in self.sc.values and self.sc.dimension in segment.annotations and segment.annotations[self.sc.dimension] in self.sc.labels[self.sc.dimension]:
            self.input(self.sc.values[self.sc.dimension], self.annotate_qualifier, sort=False)
        else:
            self.input(self.sc.labels[self.sc.dimension], self.annotate_label, sort=False)

    def annotate_label(self, annotation):
        """
        Adds a label to the active segment annotations
        """
        segment = self.sc.get_active()
        segment.annotations[self.sc.dimension] = annotation

        if self.sc.dimension not in self.sc.values or self.sc.dimension not in segment.annotations or segment.annotations[self.sc.dimension] not in self.sc.labels[self.sc.dimension]:
            self.sc.next()

        self.update()

    def annotate_qualifier(self, annotation):
        """
        Adds a qualifier to the active segment annotations
        """
        segment = self.sc.get_active()
        segment.annotations[self.sc.dimension] = "{} ➔ {}".format(segment.annotations[self.sc.dimension], annotation)
        self.sc.next()

        self.update()

    def update(self, t=None, backup=True, annotation_mode=True):
        """
        Updates the application state
        """
        self.clear_screen()

        n_previous = self.sc.i if self.sc.i < 50 else 50

        for j in range(self.sc.i - n_previous, self.sc.i):
            self.output_segment(j)

        # dimension in status
        status = "Dimension: {}".format(self.sc.dimension.title())

        # filter in status
        if self.sc.filter:
            status = "{} - Filter: {}".format(status, self.sc.filter)

        # file in status
        status = "{}\nFile: {}".format(status, self.sc.save_file)

        self.update_status_message(status)

        self.output_segment(self.sc.i, active=True)

        if annotation_mode:
            self.annotation_mode()

        if backup:
            if len(self.undo_history) == 100:
                self.undo_history.pop(0)
            self.undo_history.append(deepcopy(self.sc))

        self.sc.save()

    def output_segment(self, i, active=False):
        """
        Outputs a segment to the text field
        """
        segment = self.sc.collection[i]

        style = ["participant-{}".format(segment.participant)]

        if active:
            style.append(Styles.STRONG)

        text = "{}\t{}\t{}  \t\t{}".format(i + 1, segment.time, segment.participant, segment.raw)
        self.output(text, style=style)

        offset = len(text) + 1

        for dimension in reversed(sorted(segment.annotations.keys())):
            addendum = " [{}]".format(segment.annotations[dimension])
            self.add_to_last_line(addendum, style="dimension-{}".format(dimension), offset=offset)
            offset += len(addendum)

        for dimension in reversed(sorted(segment.legacy.keys())):
            if dimension not in segment.annotations:
                addendum = " (({}))".format(segment.legacy[dimension])
                self.add_to_last_line(addendum, style="dimension-{}".format(dimension), offset=offset)
                offset += len(addendum)

        for ls, lt in segment.links:
            if ls in self.sc.collection:
                addendum = " ⟲ {}".format(self.sc.collection.index(ls) + 1)
            else:
                addendum = " ⟲"

            self.add_to_last_line(addendum, style="link-{}".format(lt), offset=offset)
            offset += len(addendum)

        if segment.note is not None:
            self.output("\t\t\t\t ⤷ {}".format(segment.note), style=Styles.ITALIC)
