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
        da.note = self.note
        da.tokenize()

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
        da2.link = None

        # preserves links
        for link in self.linked:
            link.link = da2

        return [da1, da2]

    def merge(self, da):
        """
        Merges the DA with another
        """
        join = "" if len(self.raw) == 0 or self.raw[0] in [",", "."] else " "
        self.raw = da.raw + join + self.raw
        self.tokenize()
        self.annotations.update(da.annotations)
        self.legacy.update(da.legacy)
        self.data += da.data

        if self.note is None:
            if da.note is not None:
                self.note = da.note
        elif da.note is not None:
            self.note = "{} / {}".format(da.note, self.note)

        if da == self.link:
            da.linked.remove(self)
            self.link = da.link

        for linked_da in da.linked:
            linked_da.link = self

        self.linked = list(set(self.linked + da.linked))


class DialogueActCollection:
    # file for serialization
    data_folder = "../csv/"
    data_file = data_folder + "data.csv"

    save_folder = "../sav/"
    save_file = save_folder + "dialogue_act_collection.pic"

    def __init__(self):
        self.full_collection = []  # full collection of DA
        self.collection = []  # current collection used
        self.annotations = {}  # list of possible annotations

        self.labels = taxonomy.labels  # label tagsets
        self.values = taxonomy.values  # label qualifier tagsets

        self.i = 0
        self.dimension = taxonomy.TASK
        self.filter = False

    def get_current(self):
        return self.collection[self.i]

    def next(self):
        self.i = self.i if self.i + 1 == len(self.collection) else self.i + 1

    def previous(self):
        self.i = 0 if self.i - 1 < 0 else self.i - 1

    def change_label(self, dimension, label, new_label):
        """
        Renames a label
        """
        tagset = taxonomy.GENERAL_PURPOSE if label not in self.labels[dimension] else dimension
        index = self.labels[tagset].index(label)
        self.labels[tagset].remove(label)

        if new_label != "" and new_label not in self.labels[tagset] and new_label not in self.labels[taxonomy.GENERAL_PURPOSE]:
            self.labels[tagset].insert(index, new_label)

        for da in self.collection:
            if dimension in da.annotations and da.annotations[dimension] == label:
                if new_label != "":
                    da.annotations[dimension] = new_label
                else:
                    del da.annotations[dimension]

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
            0: taxonomy.CONTACT_MANAGEMENT,
            2: taxonomy.COMMUNICATION_MANAGEMENT,
            6: taxonomy.SOCIAL_OBLIGATIONS_MANAGEMENT,
            8: taxonomy.TASK,
            (12, 11): taxonomy.FEEDBACK,
            (14, 16): taxonomy.SENTIMENT,
            (17, 19): taxonomy.OPINION,
            (20, 22): taxonomy.EMOTION,
            23: taxonomy.KNOWLEDGE,
            25: taxonomy.DISCOURSE_STRUCTURE_MANAGEMENT,
            31: taxonomy.PARTIALITY,
            32: taxonomy.CONDITIONALITY,
            33: taxonomy.CERTAINTY,
            34: taxonomy.IRONY
        }

        legacy = {}

        for col in keys.keys():
            if not isinstance(col, int) and cols[col[0]] != "" and cols[col[1]] != "":
                legacy[keys[col]] = " ➔ ".join([cols[col[0]], cols[col[1]]])
            elif (isinstance(col, int) and cols[col] != "") or (isinstance(col, tuple) and cols[col[0]] != ""):
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
            dac.load_raw(DialogueActCollection.data_file)
            return dac

    def save(self, name=None):
        """
        Serializes the DialogueActCollection
        """
        path = DialogueActCollection.save_file if name is None else DialogueActCollection.data_folder + name + ".pic"
        with open(path, "wb") as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
