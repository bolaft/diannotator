import styles
import taxonomy

from interface import GraphicalUserInterface
from model import DialogueActCollection


class Annotator(GraphicalUserInterface):
    """
    Class managing the annotation process
    """
    def __init__(self):
        """
        Initializes the game
        """
        GraphicalUserInterface.__init__(self)

        self.dac = DialogueActCollection.load()

        for participant in set([da.participant for da in self.dac.collection]):
            self.add_tag(
                participant,
                foreground=self.generate_random_color()
            )

        self.parent.bind("<Down>", self.button_continue)
        self.parent.bind("<Up>", self.button_return)
        self.parent.bind("<Next>", lambda event, arg=10: self.button_continue(event, n=arg))
        self.parent.bind("<Prior>", lambda event, arg=10: self.button_return(event, n=arg))
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

        self.update_special_commands()  # initial update of the command list

        self.command = "annotation"
        self.dac.filter = False
        self.update()

    def annotation_mode(self):
        da = self.dac.get_current()
        if self.dac.dimension in self.dac.values and self.dac.dimension in da.annotations and da.annotations[self.dac.dimension] in self.dac.labels[self.dac.dimension] + self.dac.labels[taxonomy.GENERAL_PURPOSE]:
            self.input(self.dac.values[self.dac.dimension], self.annotate_qualifier, sort=False)
        else:
            self.input(self.dac.labels[self.dac.dimension] + self.dac.labels[taxonomy.GENERAL_PURPOSE], self.annotate_label, sort=False)

    def annotate_label(self, annotation):
        da = self.dac.get_current()
        da.annotations[self.dac.dimension] = annotation

        if self.dac.dimension not in self.dac.values or self.dac.dimension not in da.annotations or da.annotations[self.dac.dimension] not in self.dac.labels[self.dac.dimension] + self.dac.labels[taxonomy.GENERAL_PURPOSE]:
            self.dac.next()

        self.update()

    def annotate_qualifier(self, annotation):
        da = self.dac.get_current()
        da.annotations[self.dac.dimension] = "{} ➔ {}".format(da.annotations[self.dac.dimension], annotation)
        self.dac.next()
        self.update()

    def button_continue(self, e, n=1):
        for i in range(0, n):
            self.dac.next()
        self.update()

    def button_return(self, e, n=1):
        for i in range(0, n):
            self.dac.previous()
        self.update()

    def button_link(self, e):
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
        number = int(number) - 1
        da = self.dac.get_current()
        da.link = self.dac.collection[number]
        self.dac.collection[number].linked.append(da)

        self.update()

    def button_remove(self, e):
        da = self.dac.get_current()

        if self.dac.dimension in da.annotations:
            del da.annotations[self.dac.dimension]

            self.update()

    def button_merge(self, e):
        current = self.dac.get_current()
        previous = self.dac.collection[self.dac.i - 1]

        if current.participant == previous.participant:  # can only merge DA from the same participant
            current.merge(previous)

            del self.dac.collection[self.dac.i - 1]

            self.dac.previous()
            self.update()

    def button_split(self, e):
        da = self.dac.get_current()
        self.input(da.tokens[:-1], self.split, sort=False)

    def split(self, token):
        da = self.dac.get_current()
        splits = da.split(token)

        del self.dac.collection[self.dac.i]

        for split in reversed(splits):
            self.dac.collection.insert(self.dac.i, split)

        self.update()

    def button_dimension(self, e):
        self.input([dim for dim in self.dac.labels.keys() if dim != taxonomy.GENERAL_PURPOSE], self.change_dimension)

    def change_dimension(self, dimension):
        self.dac.dimension = dimension
        self.update()

    def button_jump(self, e):
        self.input(range(1, len(self.dac.collection)), self.jump)

    def jump(self, number):
        self.dac.i = int(number) - 1
        self.update()

    def button_update(self, e):
        da = self.dac.get_current()

        if self.dac.dimension in da.annotations:
            self.input([], self.update_label, free=True)

    def update_label(self, label):
        da = self.dac.get_current()

        self.dac.change_label(
            self.dac.dimension,
            da.annotations[self.dac.dimension],
            label
        )

        self.update()

    def button_add(self, e):
        self.input([], self.add_label, free=True)

    def add_label(self, label):
        self.dac.add_label(self.dac.dimension, label)

    def button_comment(self, e):
        da = self.dac.get_current()

        if da.note is not None:
            da.note = None
            self.update()
        else:
            self.input([], self.comment, free=True)

    def comment(self, note):
        da = self.dac.get_current()
        da.note = note
        self.update()

    def button_filter(self, e):
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

    def update(self, t=None):
        self.clear_screen()

        n_previous = self.dac.i if self.dac.i < 50 else 50

        for j in range(self.dac.i - n_previous, self.dac.i):
            self.output_da(j)

        status = "Dimension: {}".format(self.dac.dimension.title()) if not self.dac.filter else "Dimension: {} - Filter: {}".format(self.dac.dimension.title(), self.dac.filter)
        self.update_status_message(status)

        self.output_da(self.dac.i, current=True)
        self.dac.save()
        self.annotation_mode()

    def output_da(self, i, current=False):
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
            addendum = " ⟲ {}".format(self.dac.collection.index(da.link) + 1)
            self.add_to_last_line(addendum, style=styles.WHITE, offset=offset)
            offset += len(addendum)

        if da.note is not None:
            addendum = " {} {} {}".format(u"\u00AB", da.note, u"\u00BB")
            self.add_to_last_line(addendum, style=styles.ITALIC, offset=offset)
            offset += len(addendum)
