import codecs
import pickle
import taxonomy

from nltk.tokenize import WhitespaceTokenizer


class DialogueAct:
    def __init__(self, raw, participant, time, date):
        """
        Dialogue Act constructor
        """
        self.id = id(self)  # random unique ID
        self.raw = raw  # raw utterance
        self.participant = participant  # speaker name
        self.annotations = {}  # annotations
        self.legacy = {}  # legacy annotations
        self.date = date  # date as string
        self.time = time  # time as string
        self.link = None  # DA that elicited this one
        self.linked = []  # DAs that answer an elicitation in this one
        self.data = {}  # raw data
        self.note = None  # note about the DA

        self.tokenize()  # tokenization

    def tokenize(self):
        """
        White space tokenization
        """
        tokenizer = WhitespaceTokenizer()
        self.tokens = tokenizer.tokenize(self.raw)

    def copy(self, raw):
        """
        Creates and returns a DA with similar attributes but different raw
        """
        da = DialogueAct(raw, self.participant, self.time, self.date)
        da.annotations = self.annotations.copy()
        da.legacy = self.legacy.copy()
        da.data = self.data.copy()
        da.link = self.link
        da.linked = self.linked

        return da

    def split(self, token):
        """
        Returns two halves of the DA
        """
        # index of the split
        split_index = self.tokens.index(token) + 1

        # copying attributes
        da1 = self.copy(" ".join(self.tokens[0:split_index]))
        da2 = self.copy(" ".join(self.tokens[split_index:]))

        # preserves links
        for link in self.linked:
            link.link = da2

        return [da1, da2]

    def merge(self, da):
        """
        Merges the DA with another
        """
        self.tokens = da.tokens + self.tokens

        join = "" if len(self.raw) == 0 or self.raw[0] in [",", "."] else " "
        self.raw = da.raw + join + self.raw
        self.annotations.update(da.annotations)
        self.legacy.update(da.legacy)
        self.data += da.data

        for linked_da in da.linked:
            linked_da.link = self

        self.linked = list(set(self.linked + da.linked))


class DialogueActCollection:
    # file for serialization
    data_folder = "data/"
    save_file = data_folder + "dialogue_act_collection.pic"
    default_raw_path = data_folder + "data.csv"

    def __init__(self):
        self.full_collection = []  # full collection of DA
        self.collection = []  # current collection used
        self.annotations = {}  # list of possible annotations

        self.labels = taxonomy.labels  # label tagsets
        self.values = taxonomy.values  # label qualifier tagsets

        self.i = 0
        self.dimension = "task"

    def get_current(self):
        return self.collection[self.i]

    def next(self):
        self.i = 0 if self.i + 1 == len(self.collection) else self.i + 1

    def previous(self):
        self.i = len(self.collection) - 1 if self.i - 1 < 0 else self.i - 1

    def change_label(self, dimension, label, new_label):
        """
        Renames a label
        """
        tagset = "general_purpose" if label not in self.labels[dimension] else dimension
        index = self.labels[tagset].index(label)
        self.labels[tagset].remove(label)
        self.labels[tagset].insert(index, new_label)

        for da in self.collection:
            if dimension in da.annotations and da.annotations[dimension] == label:
                da.annotations[dimension] = new_label

    def add_label(self, dimension, label):
        """
        Adds a new label to the tagset
        """
        self.labels[dimension].append(label)

    def load_raw(self, path):
        """
        Loads a new collection from a CSV file
        """
        previous_da = None
        da = None

        with codecs.open(path, "r", encoding="utf-8") as f:
            for l in f:
                cols = l.split("\t")
                time = cols[49].strip()
                date = cols[48].strip()
                segment = cols[52].strip()

                if cols[53] == "":
                    da = DialogueAct(previous_da.raw, previous_da.participant, previous_da.time, previous_da.date)
                    da.legacy = {}

                    tokenizer = WhitespaceTokenizer()
                    end_of_previous_da = tokenizer.tokenize(previous_da.segment)[-1]
                    index = previous_da.raw.index(end_of_previous_da) + len(end_of_previous_da)
                    da.raw = previous_da.raw[index:].strip()
                    previous_da.raw = previous_da.raw[:index].strip()
                    previous_da.tokenize()
                    da.segment = segment
                    da.tokenize()
                    previous_da = da
                else:
                    raw = cols[53].strip()
                    participant = cols[50].strip() if cols[50] != "\\" else da.participant

                    da = DialogueAct(raw, participant, time, date)
                    da.segment = segment
                    previous_da = da

                da.legacy = self.make_legacy_annotations(cols)
                da.data = cols

                self.full_collection.append(da)

        self.collection = self.full_collection.copy()

    def make_legacy_annotations(self, cols):
        keys = {
            0: "contact",
            2: "communication",
            6: "social",
            8: "task",
            12: "feedback",
            14: "sentiment",
            17: "opinion",
            20: "emotion",
            23: "knowledge",
            25: "discourse"
        }

        legacy = {}

        for col in keys.keys():
            if cols[col] != "":
                legacy[keys[col]] = cols[col]

        return legacy

    @staticmethod
    def load():
        """
        Loads a serialized DialogueActCollection
        """
        try:
            with open(DialogueActCollection.save_file, "rb") as f:
                return pickle.load(f)
        except Exception:
            dac = DialogueActCollection()
            dac.load_raw(DialogueActCollection.default_raw_path)
            return dac

    def save(self, name=None):
        """
        Serializes the DialogueActCollection
        """
        path = DialogueActCollection.save_file if name is None else DialogueActCollection.data_folder + name + ".pic"
        with open(path, "wb") as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
