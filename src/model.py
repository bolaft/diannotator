# DiAnnotator
#
# Author: Soufian Salim <soufi@nsal.im>
#
# URL: <http://github.com/bolaft/diannotator>

"""
Segment modelisation classes
"""

import codecs
import csv
import json
import os
import pickle
import tempfile

from collections import OrderedDict
from nltk.tokenize import WhitespaceTokenizer

# check if the current file is in a folder name "src"
EXEC_FROM_SOURCE = os.path.dirname(os.path.abspath(__file__)).split("/")[-1] == "src"


class Segment:
    def __init__(self, raw, participant, time, date):
        """
        Segment constructor
        """
        self.id = id(self)  # random unique ID
        self.raw = raw  # raw utterance
        self.original_raw = raw  # full original raw utterance
        self.participant = participant  # speaker name
        self.annotations = {}  # annotations
        self.legacy = {}  # legacy annotations
        self.date = date  # date as string
        self.time = time  # time as string
        self.links = []  # segment linked to this one
        self.linked = []  # segments that answer an elicitation in this one
        self.note = None  # note about the segment

        self.tokenize()  # tokenization

    ##################
    # EXPORT METHODS #
    ##################

    def to_json_dict(self):
        """
        Returns a dict representation of the object for JSON export
        """
        links = {}

        for segment, lt in self.links:
            links[lt] = [segment.id] if lt not in links else links[lt] + [segment.id]

        return {
            "id": self.id,
            "raw": self.raw,
            "original_raw": self.original_raw,
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
        data.update({"original_raw": self.original_raw if isinstance(self.original_raw, str) else "<<MERGED<<".join(self.original_raw)})
        data.update({"participant": self.participant})
        data.update({"date": self.date})
        data.update({"time": self.time})
        data.update({"note": self.note})
        data.update({"links": ",".join(["{}-{}".format(segment.id, lt) for segment, lt in self.links])})

        for dimension in labels.keys():
            data.update(
                {dimension: None if not dimension in self.annotations else self.annotations[dimension]}
            )

        return data

    ###############
    # NLP METHODS #
    ###############

    def tokenize(self):
        """
        Tokenizes the segment
        """
        tokenizer = WhitespaceTokenizer()
        self.tokens = tokenizer.tokenize(self.raw)

    ###########################
    # LINK MANAGEMENT METHODS #
    ###########################

    def check_for_link(self, target):
        """
        Checks if two segments are linked
        """
        for ls, lt in self.links:
            if ls == target:
                return True

    def remove_links(self, target):
        """
        Removes a link between two segments
        """
        for ls, lt in self.links:
            if ls == target:
                self.links.remove((target, lt))

        for lls, llt in target.linked:
            if lls == self:
                target.linked.remove((self, llt))

    def replace_links(self, target, new_target):
        """
        Removes a link between two segments
        """
        for ls, lt in self.links:
            if ls == target:
                self.links.remove((target, lt))
                self.links.append((new_target, lt))

        for ls, lt in target.linked:
            if ls == self:
                target.linked.remove((self, lt))
                new_target.linked.append((self, lt))

    ################################
    # SEGMENT MODIFICATION METHODS #
    ################################

    def split(self, token):
        """
        Returns two halves of the segments
        """
        # index of the split
        split_index = self.tokens.index(token) + 1

        # copying attributes
        s1 = self.copy(" ".join(self.tokens[0:split_index]))
        s2 = self.copy(" ".join(self.tokens[split_index:]))

        # outgoing links are removed for s2
        s2.links = []

        # preserves links
        for ls, lt in self.linked:
            ls.replace_links(self, s2)

        return [s1, s2]

    def merge(self, segment):
        """
        Merges the segment with another
        """
        join = "" if len(self.raw) == 0 or self.raw[0] in [",", "."] else " "
        self.raw = segment.raw + join + self.raw
        self.original_raw = [segment.original_raw, self.original_raw]
        self.tokenize()
        self.annotations.update(segment.annotations)
        self.legacy.update(segment.legacy)

        if self.note is None:
            if segment.note is not None:
                self.note = segment.note
        elif segment.note is not None:
            self.note = "{} / {}".format(segment.note, self.note)

        # removing links towards the merged segment
        self.remove_links(segment)

        # merging links
        self.links = list(set(self.links + segment.links))

        # updating incoming links
        for ls, lt in segment.linked:
            ls.replace_links(segment, self)

    #################
    # OTHER METHODS #
    #################

    def copy(self, raw):
        """
        Creates and returns a segment with similar attributes but different raw
        """
        segment = Segment(raw, self.participant, self.time, self.date)
        segment.original_raw = self.original_raw
        segment.annotations = self.annotations.copy()
        segment.legacy = self.legacy.copy()
        segment.links = self.links.copy()
        segment.time = self.time
        segment.date = self.date
        segment.linked = self.linked.copy()
        segment.note = self.note
        segment.tokenize()

        return segment


class SegmentCollection:
    # paths
    save_dir = "../sav/" if EXEC_FROM_SOURCE else "sav/"
    taxo_dir = "../tax/" if EXEC_FROM_SOURCE else "tax/"
    data_dir = "../out/" if EXEC_FROM_SOURCE else "out/"
    temp_dir = "{}/diannotator/".format(tempfile.gettempdir())

    def __init__(self):
        """
        Initialization of the segment collection
        """
        self.save_file = os.path.abspath("{}tmp.pic".format(SegmentCollection.save_dir))

        self.full_collection = []  # full collection of segments
        self.collection = []  # current collection used
        self.annotations = {}  # list of possible annotations

        self.taxonomy = None  # taxonomy name

        self.labels = {}  # label tagsets
        self.values = {}  # label qualifier tagsets
        self.colors = {}  # dimension colors
        self.links = []  # link types

        self.i = 0  # collection index
        self.dimension = None  # active dimension
        self.filter = False  # active filter

    ######################
    # NAVIGATION METHODS #
    ######################

    def next(self):
        self.i = self.i if self.i + 1 == len(self.collection) else self.i + 1

    def previous(self):
        self.i = 0 if self.i - 1 < 0 else self.i - 1

    ##################
    # ACCESS METHODS #
    ##################

    def get_active(self):
        return self.collection[self.i]

    ########################
    # MODIFICATION METHODS #
    ########################

    def remove(self, segment):
        self.collection.remove(segment)
        self.full_collection.remove(segment)

    def insert_after_active(self, insert):
        # insert into full collection
        self.full_collection.insert(self.full_collection.index(self.get_active()) + 1, insert)

        # insert into active collection
        self.collection.insert(self.i + 1, insert)

    #################################
    # TAXONOMY MODIFICATION METHODS #
    #################################

    def change_label(self, dimension, label, new_label):
        """
        Renames a label
        """
        index = self.labels[dimension].index(label)
        self.labels[dimension].remove(label)

        if new_label not in self.labels[dimension]:
            self.labels[dimension].insert(index, new_label)

        for segment in list(set(self.collection + self.full_collection)):
            if dimension in segment.annotations and segment.annotations[dimension] == label:
                segment.annotations[dimension] = new_label

    def delete_label(self, dimension, label):
        """
        Deletes a label
        """
        self.labels[dimension].remove(label)

        for segment in list(set(self.collection + self.full_collection)):
            if dimension in segment.annotations and segment.annotations[dimension] == label:
                del segment.annotations[dimension]

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

    ##################################
    # TAXONOMY IMPORT/EXPORT METHODS #
    ##################################

    def import_taxonomy(self, path):
        """
        Imports the collection's taxonomy from a JSON file
        """
        taxonomy = json.loads(codecs.open(path, encoding="utf-8").read())

        self.taxonomy = taxonomy["name"]
        self.dimension = taxonomy["default"]

        self.labels = taxonomy["labels"]  # label tagsets
        self.values = taxonomy["values"]  # label qualifier tagsets
        self.colors = taxonomy["colors"]  # dimension colors
        self.links = taxonomy["links"]  # link types

    def export_taxonomy(self, path):
        """
        Exports the collection's taxonomy to a JSON file
        """
        taxonomy = {
            "name": self.taxonomy,
            "default": self.dimension,
            "colors": self.colors,
            "labels": self.labels,
            "values": self.values
        }

        with open(path, "w") as f:
            json.dump(taxonomy, f, indent=4, ensure_ascii=False)

    ####################################
    # COLLECTION IMPORT/EXPORT METHODS #
    ####################################

    def import_collection(self, path):
        """
        Imports a new collection from a CSV file
        """
        with open(path) as f:
            rows = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True, delimiter="\t")]

        previous_segment = None
        segment = None

        for row in rows:
            time = previous_segment.time if row["time"] is None or row["time"].strip() == "" else row["time"].strip()
            date = previous_segment.date if row["date"] is None or row["date"].strip() == "" else row["date"].strip()
            span = row["segment"].strip()

            if row["raw"] is None or row["raw"].strip() == "":
                segment = Segment(
                    previous_segment.raw,
                    previous_segment.participant,
                    previous_segment.time,
                    previous_segment.date
                )
                segment.original_raw = previous_segment.original_raw

                # loading legacy annotations
                for key in row.keys():
                    if key not in ["segment", "raw", "time", "date", "participant"] and row[key] is not None and row[key].strip() != "":
                        if key.endswith("-value") and row[key]:
                            dimension = key[:len(key) - len("-value")]

                            # if the function is already set
                            if key in segment.legacy:
                                segment.legacy[dimension] = "{} ➔ {}".format(segment.legacy[dimension], row[key])
                            else:
                                segment.legacy[dimension] = row[key]
                        else:
                            # if the qualifier is already set
                            if key in segment.legacy:
                                segment.legacy[key] = "{} ➔ {}".format(row[key], segment.legacy[key])
                            else:
                                segment.legacy[key] = row[key]

                tokenizer = WhitespaceTokenizer()

                # last token of the previous segment's segment
                end_of_previous_span = tokenizer.tokenize(previous_segment.span)[-1]

                # position of the last token of the previous segment's segment in the full raw
                index = previous_segment.raw.index(end_of_previous_span) + len(end_of_previous_span)

                # ajust the raw of the current segment
                segment.raw = previous_segment.raw[index:].strip()

                # adjust the raw of the previous segment
                previous_segment.raw = previous_segment.raw[:index].strip()

                # update tokens of the previous segment
                previous_segment.tokenize()
            else:
                raw = row["raw"].strip()
                participant = row["participant"].strip() if row["participant"].strip() != "\\" else segment.participant

                segment = Segment(
                    raw,
                    participant,
                    time,
                    date
                )

            # update the current segment's segment
            segment.span = span

            # update the current segment's tokens
            segment.tokenize()

            # set the current segment as the previous segment (for the next iteration)
            previous_segment = segment

            # makes legacy annotations for the segment
            segment.legacy = self.make_legacy_annotations(row)

            # set note
            segment.note = row["note"].strip() if "note" in row else None

            # adds the segment to the full collection
            self.full_collection.append(segment)

        # syncs the current collection to the full collection
        self.collection = self.full_collection.copy()

    def export_collection(self, path):
        """
        Exports the collection to the filesystem
        """
        if path.endswith(".json"):
            self.export_collection_as_json(path)
        elif path.endswith(".csv"):
            self.export_collection_as_csv(path)

    def export_collection_as_json(self, path):
        """
        Exports the collection in JSON format
        """
        data = [segment.to_json_dict() for segment in self.full_collection]

        with open(path, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def export_collection_as_csv(self, path):
        """
        Exports the collection in CSV format
        """
        with open(path, "w") as f:
            w = csv.DictWriter(f, self.full_collection[0].to_csv_dict(self.labels).keys(), delimiter="\t")
            w.writeheader()

            for segment in self.full_collection:
                w.writerow(segment.to_csv_dict(self.labels))

    ###########################
    # SAVE MANAGEMENT METHODS #
    ###########################

    def save(self, name=None, backup=False):
        """
        Serializes the SegmentCollection and writes it to the filesystem
        """
        if name and not backup:
            self.save_file = os.path.abspath(name)
            self.write_save_path_to_tmp()

        with open(name if name is not None else self.save_file, "wb") as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

    def write_save_path_to_tmp(self):
        """
        Writes the path to the current save file to /tmp
        """
        if not os.path.exists(SegmentCollection.temp_dir):
            os.makedirs(SegmentCollection.temp_dir)

        with open("{}last_save.tmp".format(SegmentCollection.temp_dir), "w") as tmp:
            tmp.write(self.save_file)

    @staticmethod
    def read_save_path_from_tmp():
        """
        Reads the path to the previous save file from /tmp
        """
        if not os.path.exists(SegmentCollection.temp_dir):
            os.makedirs(SegmentCollection.temp_dir)

        path = "{}last_save.tmp".format(SegmentCollection.temp_dir)

        # create file if doesn't exist
        if not os.path.exists(path):
            open(path, "a").close()

        with open(path, "r") as tmp:
            tmp.seek(0)
            return tmp.read().strip()

    @staticmethod
    def load(path):
        """
        Loads a serialized SegmentCollection
        """
        if path.endswith(".pic"):
            with open(path, "rb") as f:
                sc = pickle.load(f)
                sc.write_save_path_to_tmp()

                return sc
        elif path.endswith(".csv"):
            sc = SegmentCollection()
            sc.import_collection(path)
            sc.write_save_path_to_tmp()

            return sc

        return False
