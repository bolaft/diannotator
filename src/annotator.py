import styles
import taxonomy

from copy import deepcopy
from interface import GraphicalUserInterface, WHITE, GRAY
from model import DialogueActCollection
from datetime import datetime
from tkinter import Button, filedialog, LEFT


class Annotator(GraphicalUserInterface):
    """
    Class managing the annotation process
    """
    def __init__(self):
        """
        Initializes the game
        """
        GraphicalUserInterface.__init__(self)

        # tries to load previous save
        self.dac = DialogueActCollection.load(DialogueActCollection.get_last_save())

        if not self.dac:
            # initializing the dialogue act collection
            self.load()

        # make a backup of the collection
        self.dac.save(name="auto-" + datetime.now().strftime("%d-%m-%y_%X"), backup=True)

        # creating custom colors for each participant
        for participant in set([da.participant for da in self.dac.full_collection]):
            self.add_tag(
                participant,
                foreground=self.generate_random_color()
            )

        # binding controls

        self.parent.bind("<Down>", self.command_continue)
        self.parent.bind("<Up>", self.command_return)
        self.parent.bind("<Next>", lambda event, arg=10: self.command_continue(event, n=arg))
        self.parent.bind("<Prior>", lambda event, arg=10: self.command_return(event, n=arg))
        self.parent.bind("<Delete>", self.command_delete)

        self.parent.bind("<Control-l>", self.button_link)
        self.parent.bind("<Control-r>", self.button_remove)
        self.parent.bind("<Control-m>", self.button_merge)
        self.parent.bind("<Control-s>", self.button_split)
        self.parent.bind("<Control-d>", self.button_dimension)
        self.parent.bind("<Control-j>", self.button_jump)
        self.parent.bind("<Control-u>", self.button_update)
        self.parent.bind("<Control-a>", self.button_add)
        self.parent.bind("<Control-c>", self.button_comment)
        self.parent.bind("<Control-f>", self.button_filter)
        self.parent.bind("<Control-z>", self.button_undo)

        self.parent.bind("<Control-S>", lambda event, arg=None: self.save_as())
        self.parent.bind("<Control-o>", lambda event, arg=None: self.load())

        self.undo_history = []  # initializes undo history

        self.make_special_buttons()  # makes special buttons

        self.update()  # display text

    def load(self):
        self.dac = DialogueActCollection.load(filedialog.askopenfilename(
            initialdir=DialogueActCollection.save_dir,
            title="Open",
            filetypes=(("serialized saves", "*.pic"), ("data files", "*.csv"), ("all files", "*.*"))
        ))

        self.undo_history = []  # reinitializes undo history
        self.update()

    def save_as(self):
        self.dac.save(name=filedialog.asksaveasfilename(
            initialdir=DialogueActCollection.save_dir,
            title="Save as",
            filetypes=(("serialized saves", "*.pic"), ("all files", "*.*"))
        ))

        self.update()

    def make_special_buttons(self):
        for button in self.special_commands.winfo_children():
            button.destroy()

        buttons = {
            "jump": lambda n=0: self.button_jump(n),
            "dimension": lambda n=0: self.button_dimension(n),
            "remove": lambda n=0: self.button_remove(n),
            "link": lambda n=0: self.button_link(n),
            "split": lambda n=0: self.button_split(n),
            "merge": lambda n=0: self.button_merge(n),
            "add": lambda n=0: self.button_add(n),
            "update": lambda n=0: self.button_update(n),
            "filter": lambda n=0: self.button_filter(n),
            "z Undo": lambda n=0: self.button_undo(n),
            "comment": lambda n=0: self.button_comment(n)
        }

        for text, function in sorted(buttons.items()):
            b = Button(
                self.special_commands,
                text="[{}]{}".format(text[0].upper(), text[1:]),
                background=WHITE,
                foreground=GRAY,
                command=function
            )

            b.pack(side=LEFT)

    def command_continue(self, e, n=1):
        """
        Command to continue to a next segment
        """
        # cycles through the collection
        for i in range(0, n):
            self.dac.next()

        self.update()

    def command_return(self, e, n=1):
        """
        Command to return to a previous segment
        """
        # cycles backards through the collection
        for i in range(0, n):
            self.dac.previous()

        self.update()

    def command_delete(self, e, n=1):
        """
        Command to delete a segment
        """
        da = self.dac.get_current()

        # TODO: make a DialogueActCollection "remove" function
        self.dac.collection.remove(da)
        self.dac.full_collection.remove(da)

        self.update()

    def button_link(self, e):
        """
        Button to link a segment to another
        """
        if self.dac.i > 0:  # first DA can't be linked
            da = self.dac.get_current()

            if da.link is not None:  # removing link
                if da in da.link.linked:
                    da.link.linked.remove(da)
                da.link = None
                self.update()
            else:  # adding link
                self.input(range(1, self.dac.i + 1), self.link)

    def link(self, number):
        """
        Links a segment to another
        """
        number = int(number) - 1
        da = self.dac.get_current()
        da.link = self.dac.collection[number]
        self.dac.collection[number].linked.append(da)

        self.update()

    def button_remove(self, e):
        """
        Button to remove annotations for the segment in the current dimension
        """
        da = self.dac.get_current()

        if self.dac.dimension in da.annotations:
            del da.annotations[self.dac.dimension]

            self.update()

    def button_merge(self, e):
        """
        Button to merge two segments
        """
        current = self.dac.get_current()
        previous = self.dac.collection[self.dac.i - 1]

        if current.participant == previous.participant:  # can only merge DA from the same participant
            current.merge(previous)

            del self.dac.collection[self.dac.i - 1]

            for i, act in enumerate(self.dac.full_collection):
                if act == current:
                    del self.dac.full_collection[i - 1]
                    break

            self.dac.previous()
            self.update()

    def button_split(self, e):
        """
        Button to split a segment in two
        """
        da = self.dac.get_current()
        self.input(da.tokens[:-1], self.split, sort=False)

    def split(self, token):
        """
        Splits a segment in two
        """
        da = self.dac.get_current()
        splits = da.split(token)

        del self.dac.collection[self.dac.i]

        for split in reversed(splits):
            self.dac.collection.insert(self.dac.i, split)

        for i, act in enumerate(self.dac.full_collection):
            if act == da:
                del self.dac.full_collection[i]

                for split in reversed(splits):
                    self.dac.full_collection.insert(i, split)
                break

        self.update()

    def button_dimension(self, e):
        """
        Button to change the current dimension
        """
        self.input([dim for dim in self.dac.labels.keys() if dim != taxonomy.GENERAL_PURPOSE], self.change_dimension)

    def change_dimension(self, dimension):
        """
        Changes the current dimension
        """
        self.dac.dimension = dimension
        self.update()

    def button_jump(self, e):
        """
        Button to jump to a specific segment
        """
        self.input(range(1, len(self.dac.collection)), self.jump)

    def jump(self, number):
        """
        Jumps to a specific segment
        """
        self.dac.i = int(number) - 1
        self.update()

    def button_update(self, e):
        """
        Button to update (or delete) a label
        """
        da = self.dac.get_current()

        if self.dac.dimension in da.annotations:
            self.input([], self.update_label, free=True)

    def update_label(self, label):
        """
        Updates (or deletes) a label
        """
        da = self.dac.get_current()

        self.dac.change_label(
            self.dac.dimension,
            da.annotations[self.dac.dimension],
            label
        )

        self.update()

    def button_add(self, e):
        """
        Button to add a new label
        """
        self.input([], self.add_label, free=True)

    def add_label(self, label):
        """
        Adds a new label
        """
        self.dac.add_label(self.dac.dimension, label)

    def button_comment(self, e):
        """
        Button to add (or remove) a comment
        """
        da = self.dac.get_current()

        if da.note is not None:
            da.note = None
            self.update()
        else:
            self.input([], self.comment, free=True)

    def comment(self, note):
        """
        Adds a new comment
        """
        if note != "":
            da = self.dac.get_current()
            da.note = note
            self.update()

    def button_filter(self, e):
        """
        Button to filter segments by label
        """
        # save because filter tends to make the app bug
        self.dac.save(
            name="{}auto-{}.pic".format(DialogueActCollection.save_dir, datetime.now().strftime("%d-%m-%y_%X")),
            backup=True
        )

        current_da = self.dac.get_current()

        if not self.dac.filter and (self.dac.dimension in current_da.annotations or self.dac.dimension in current_da.legacy):
            if self.dac.dimension in current_da.annotations:
                self.dac.collection = [da for da in self.dac.full_collection if self.dac.dimension in da.annotations and da.annotations[self.dac.dimension].startswith(current_da.annotations[self.dac.dimension].split(" ➔ ")[0])]
                self.dac.filter = "[{}]".format(current_da.annotations[self.dac.dimension].split(" ➔ ")[0])
            elif self.dac.dimension in current_da.legacy:
                self.dac.collection = [da for da in self.dac.full_collection if self.dac.dimension in da.legacy and da.legacy[self.dac.dimension].startswith(current_da.legacy[self.dac.dimension].split(" ➔ ")[0])]
                self.dac.filter = "(({}))".format(current_da.legacy[self.dac.dimension].split(" ➔ ")[0])
        else:
            self.dac.collection = self.dac.full_collection.copy()
            self.dac.filter = False

        for i, da in enumerate(self.dac.collection):
            if da == current_da:
                self.dac.i = i

        self.update()

    def button_undo(self, e):
        """
        Button to undo changes
        """
        # if there is a previous state in history to go to
        if len(self.undo_history) > 1:
            del self.undo_history[-1]  # remove current state from history

            self.dac = self.undo_history[-1]  # change to previous state in history
            self.update(backup=False)  # update without saving state to history

    def annotation_mode(self):
        """
        Resumes the annotation mode
        """
        da = self.dac.get_current()

        if self.dac.dimension in self.dac.values and self.dac.dimension in da.annotations and da.annotations[self.dac.dimension] in self.dac.labels[self.dac.dimension] + self.dac.labels[taxonomy.GENERAL_PURPOSE]:
            self.input(self.dac.values[self.dac.dimension], self.annotate_qualifier, sort=False)
        else:
            self.input(self.dac.labels[self.dac.dimension] + self.dac.labels[taxonomy.GENERAL_PURPOSE], self.annotate_label, sort=False)

    def annotate_label(self, annotation):
        """
        Adds a label to the current segment annotations
        """
        da = self.dac.get_current()
        da.annotations[self.dac.dimension] = annotation

        if self.dac.dimension not in self.dac.values or self.dac.dimension not in da.annotations or da.annotations[self.dac.dimension] not in self.dac.labels[self.dac.dimension] + self.dac.labels[taxonomy.GENERAL_PURPOSE]:
            self.dac.next()

        self.update()

    def annotate_qualifier(self, annotation):
        """
        Adds a qualifier to the current segment annotations
        """
        da = self.dac.get_current()
        da.annotations[self.dac.dimension] = "{} ➔ {}".format(da.annotations[self.dac.dimension], annotation)
        self.dac.next()
        self.update()

    def update(self, t=None, backup=True):
        """
        Updates the application state
        """
        self.clear_screen()

        n_previous = self.dac.i if self.dac.i < 50 else 50

        for j in range(self.dac.i - n_previous, self.dac.i):
            self.output_segment(j)

        # dimension in status
        status = "Dimension: {}".format(self.dac.dimension.title())

        # filter in status
        if self.dac.filter:
            status = "{} - Filter: {}".format(status, self.dac.filter)

        # file in status
        status = "{}\nFile: {}".format(status, self.dac.save_file)

        self.update_status_message(status)

        self.output_segment(self.dac.i, current=True)
        self.annotation_mode()

        if backup:
            if len(self.undo_history) == 100:
                self.undo_history.pop(0)
            self.undo_history.append(deepcopy(self.dac))

        self.dac.save()

    def output_segment(self, i, current=False):
        """
        Outputs a segment to the text field
        """
        da = self.dac.collection[i]

        style = [da.participant]

        if current:
            style.append(styles.STRONG)

        text = "{}\t{}\t{}  \t\t{}".format(i + 1, da.time, da.participant, da.raw)
        self.output(text, style=style)

        offset = len(text) + 1

        colors = {
            taxonomy.TASK: styles.WHITE,
            taxonomy.FEEDBACK: styles.PROCESS,
            taxonomy.SOCIAL_OBLIGATIONS_MANAGEMENT: styles.OK,
            taxonomy.DISCOURSE_STRUCTURE_MANAGEMENT: styles.INFO,
            taxonomy.COMMUNICATION_MANAGEMENT: styles.DEBUG,
            taxonomy.CONTACT_MANAGEMENT: styles.GREEN,
            taxonomy.OPINION: styles.WARNING,
            taxonomy.SENTIMENT: styles.WARNING,
            taxonomy.EMOTION: styles.WARNING,
            taxonomy.KNOWLEDGE: styles.DIALOG,
            taxonomy.PROBLEM_MANAGEMENT: styles.FAIL,
            taxonomy.PARTIALITY: styles.PURPLE,
            taxonomy.CONDITIONALITY: styles.PURPLE,
            taxonomy.CERTAINTY: styles.PURPLE,
            taxonomy.IRONY: styles.PURPLE
        }

        for dimension in reversed(sorted(da.annotations.keys())):
            addendum = " [{}]".format(da.annotations[dimension])
            self.add_to_last_line(addendum, style=colors[dimension], offset=offset)
            offset += len(addendum)

        for dimension in reversed(sorted(da.legacy.keys())):
            if dimension not in da.annotations:
                addendum = " (({}))".format(da.legacy[dimension])
                self.add_to_last_line(addendum, style=colors[dimension], offset=offset)
                offset += len(addendum)

        if da.link is not None:
            if da.link in self.dac.collection:
                addendum = " ⟲ {}".format(self.dac.collection.index(da.link) + 1)
            else:
                addendum = " ⟲"
            self.add_to_last_line(addendum, style=styles.WHITE, offset=offset)
            offset += len(addendum)

        if da.note is not None:
            self.output("\t\t\t\t ⤷ {}".format(da.note), style=styles.ITALIC)
