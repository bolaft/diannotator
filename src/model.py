import codecs
import pickle
import os
import csv
import json
import tempfile

from nltk.tokenize import WhitespaceTokenizer
from collections import OrderedDict


# check if the current file is in a folder name "src"
EXEC_FROM_SOURCE = os.path.dirname(os.path.abspath(__file__)).split("/")[-1] == "src"


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
        self.links = []  # DA linked to this one
        self.linked = []  # DAs that answer an elicitation in this one
        self.note = None  # note about the DA

        self.tokenize()  # tokenization

    def to_json_dict(self):
        """
        Returns a dict representation of the object for JSON export
        """
        links = {}

        for da, lt in self.links:
            links[lt] = [da.id] if lt not in links else links[lt] + [da.id]

        return {
            "id": self.id,
            "raw": self.raw,
            "participant": self.participant,
            "date": self.date,
            "time": self.time,
            "note": self.note,
            "links": links,
            "annotations": self.annotations
        }

    def to_csv_dict(self, labels):
        """
        Returns a dict representation of the object for CSV export
        """
        data = OrderedDict()

        data.update({"id": self.id})
        data.update({"raw": self.raw})
        data.update({"participant": self.participant})
        data.update({"date": self.date})
        data.update({"time": self.time})
        data.update({"note": self.note})
        data.update({"links": ",".join(["{}-{}".format(da.id, lt) for da, lt in self.links])})

        for dimension in labels:
            data.update(
                {dimension: None if not dimension in self.annotations else self.annotations[dimension]}
            )

        return data

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
        da.links = self.links.copy()
        da.time = self.time
        da.date = self.date
        da.linked = self.linked.copy()
        da.note = self.note
        da.tokenize()

        return da

    @staticmethod
    def check_for_link(source, target):
        """
        Checks if two DAs are linked
        """
        for da, lt in source.links:
            if da == target:
                return True

    @staticmethod
    def remove_links(source, target):
        """
        Removes a link between two DA
        """
        for da, lt in source.links:
            if da == target:
                source.links.remove((target, lt))

        for lda, llt in target.linked:
            if lda == source:
                target.linked.remove((source, llt))

    @staticmethod
    def replace_links(source, target, new_target):
        """
        Removes a link between two DA
        """
        for lda, lt in source.links:
            if lda == target:
                source.links.remove((target, lt))
                source.links.append((new_target, lt))

        for lda, lt in target.linked:
            if lda == source:
                target.linked.remove((source, lt))
                new_target.linked.append((source, lt))

    def split(self, token):
        """
        Returns two halves of the DA
        """
        # index of the split
        split_index = self.tokens.index(token) + 1

        # copying attributes
        da1 = self.copy(" ".join(self.tokens[0:split_index]))
        da2 = self.copy(" ".join(self.tokens[split_index:]))

        # outgoing links are removed for da2
        da2.links = []

        # preserves links
        for lda, lt in self.linked:
            DialogueAct.replace_links(lt, self, da2)

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

        if self.note is None:
            if da.note is not None:
                self.note = da.note
        elif da.note is not None:
            self.note = "{} / {}".format(da.note, self.note)

        if DialogueAct.check_for_link(self, da):
            DialogueAct.remove_links(self, da)
            self.links = da.links

        for lda, lt in da.linked:
            DialogueAct.replace_links(lda, da, self)

        self.linked = list(set(self.linked + da.linked))


class DialogueActCollection:
    # file for serialization
    save_dir = "../sav/" if EXEC_FROM_SOURCE else "sav/"
    taxo_dir = "../tax/" if EXEC_FROM_SOURCE else "tax/"
    data_dir = "../out/" if EXEC_FROM_SOURCE else "out/"
    temp_dir = "{}/diannotator/".format(tempfile.gettempdir())

    def __init__(self):
        self.save_file = os.path.abspath("{}tmp.pic".format(DialogueActCollection.save_dir))

        self.full_collection = []  # full collection of DA
        self.collection = []  # current collection used
        self.annotations = {}  # list of possible annotations

        self.taxonomy = None

        self.labels = {}  # label tagsets
        self.values = {}  # label qualifier tagsets
        self.colors = {}  # dimension colors
        self.links = []  # link types

        self.i = 0
        self.dimension = None
        self.filter = False

    def set_taxonomy(self, path):
        taxonomy = json.loads(codecs.open(path, encoding="utf-8").read())

        self.taxonomy = taxonomy["name"]
        self.dimension = taxonomy["default"]

        self.labels = taxonomy["labels"]  # label tagsets
        self.values = taxonomy["values"]  # label qualifier tagsets
        self.colors = taxonomy["colors"]  # dimension colors
        self.links = taxonomy["links"]  # link types

    def get_current(self):
        return self.collection[self.i]

    def remove(self, da):
        self.collection.remove(da)
        self.full_collection.remove(da)

    def insert_after_current(self, insert):
        # insert into full collection
        self.full_collection.insert(self.full_collection.index(self.get_current()) + 1, insert)

        # insert into current collection
        self.collection.insert(self.i + 1, insert)

    def next(self):
        self.i = self.i if self.i + 1 == len(self.collection) else self.i + 1

    def previous(self):
        self.i = 0 if self.i - 1 < 0 else self.i - 1

    def change_label(self, dimension, label, new_label):
        """
        Renames a label
        """
        index = self.labels[dimension].index(label)
        self.labels[dimension].remove(label)

        if new_label not in self.labels[dimension]:
            self.labels[dimension].insert(index, new_label)

        for da in list(set(self.collection + self.full_collection)):
            if dimension in da.annotations and da.annotations[dimension] == label:
                da.annotations[dimension] = new_label

    def delete_label(self, dimension, label):
        """
        Deletes a label
        """
        self.labels[dimension].remove(label)

        for da in list(set(self.collection + self.full_collection)):
            if dimension in da.annotations and da.annotations[dimension] == label:
                del da.annotations[dimension]

    def add_label(self, dimension, label):
        """
        Adds a new label to the tagset
        """
        self.labels[dimension].append(label)

    def add_qualifier(self, dimension, quaifier):
        """
        Adds a new qualifier to the tagset
        """
        self.values[dimension].append(quaifier)

    def load_csv(self, path):
        """
        Loads a new collection from a CSV file
        """
        with open(path) as f:
            rows = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True, delimiter="\t")]

        previous_da = None
        da = None

        for row in rows:
            time = row["time"].strip()
            date = row["date"].strip()
            segment = row["segment"].strip()
            note = row["note"].strip() if "note" in row else None

            if row["raw"] is None or row["raw"].strip() == "":
                da = DialogueAct(
                    previous_da.raw,
                    previous_da.participant,
                    previous_da.time,
                    previous_da.date
                )
                da.note = previous_da.note

                da.legacy = {}

                tokenizer = WhitespaceTokenizer()

                # last token of the previous DA's segment
                end_of_previous_da = tokenizer.tokenize(previous_da.segment)[-1]

                # position of the last token of the previous DA's segment in the full raw
                index = previous_da.raw.index(end_of_previous_da) + len(end_of_previous_da)

                # ajust the raw of the current DA
                da.raw = previous_da.raw[index:].strip()

                # adjust the raw of the previous DA
                previous_da.raw = previous_da.raw[:index].strip()

                # update tokens of the previous DA
                previous_da.tokenize()
            else:
                raw = row["raw"].strip()
                participant = row["participant"].strip() if row["participant"].strip() != "\\" else da.participant

                da = DialogueAct(
                    raw,
                    participant,
                    time,
                    date
                )
                da.note = note

            # update the current DA's segment
            da.segment = segment

            # update the current DA's tokens
            da.tokenize()

            # set the current DA as the previous DA (for the next iteration)
            previous_da = da

            # makes legacy annotations for the DA
            da.legacy = self.make_legacy_annotations(row)

            # adds the DA to the full collection
            self.full_collection.append(da)

        # syncs the current collection to the full collection
        self.collection = self.full_collection.copy()

    def make_legacy_annotations(self, row):
        legacy = {}

        for key in row.keys():
            if key not in ["segment", "raw", "time", "date", "participant"] and row[key] is not None and row[key].strip() != "":
                if key.endswith("-value") and row[key]:
                    dimension = key[:len(key) - len("-value")]

                    # if the function is alreay set
                    if key in legacy:
                        legacy[dimension] = "{} ➔ {}".format(legacy[dimension], row[key])
                    else:
                        legacy[dimension] = row[key]
                else:
                    # if the qualifier is already set
                    if key in legacy:
                        legacy[key] = "{} ➔ {}".format(row[key], legacy[key])
                    else:
                        legacy[key] = row[key]

        return legacy

    def save(self, name=None, backup=False):
        """
        Serializes the DialogueActCollection
        """
        if name and not backup:
            self.save_file = os.path.abspath(name)
            self.update_last_save()

        with open(name if name is not None else self.save_file, "wb") as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

    def export(self, path):
        if path.endswith(".json"):
            self.export_json(path)
        elif path.endswith(".csv"):
            self.export_csv(path)

    def export_json(self, path):
        data = [da.to_json_dict() for da in self.full_collection]

        with open(path, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def export_csv(self, path):
        with open(path, "w") as f:
            w = csv.DictWriter(f, self.full_collection[0].to_csv_dict(self.labels).keys(), delimiter="\t")
            w.writeheader()

            for da in self.full_collection:
                w.writerow(da.to_csv_dict())

    def export_taxonomy(self, path):
        taxonomy = {
            "name": self.taxonomy,
            "default": self.dimension,
            "colors": self.colors,
            "labels": self.labels,
            "values": self.values
        }

        with open(path, "w") as f:
            json.dump(taxonomy, f, indent=4, ensure_ascii=False)

    def update_last_save(self):
        if not os.path.exists(DialogueActCollection.temp_dir):
            os.makedirs(DialogueActCollection.temp_dir)

        with open("{}last_save.tmp".format(DialogueActCollection.temp_dir), "w") as tmp:
            tmp.write(self.save_file)

    @staticmethod
    def get_last_save():
        if not os.path.exists(DialogueActCollection.temp_dir):
            os.makedirs(DialogueActCollection.temp_dir)

        path = "{}last_save.tmp".format(DialogueActCollection.temp_dir)

        # create file if doesn't exist
        if not os.path.exists(path):
            open(path, "a").close()

        with open(path, "r") as tmp:
            tmp.seek(0)
            return tmp.read().strip()

    @staticmethod
    def load(path):
        """
        Loads a serialized DialogueActCollection
        """
        if path.endswith(".pic"):
            with open(path, "rb") as f:
                dac = pickle.load(f)
                dac.update_last_save()

                return dac
        elif path.endswith(".csv"):
            dac = DialogueActCollection()
            dac.load_csv(path)
            dac.update_last_save()

            return dac

        return False
