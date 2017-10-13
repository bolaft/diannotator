# DiAnnotator
#
# Author: Soufian Salim <soufi@nsal.im>
#
# URL: <http://github.com/bolaft/diannotator>

"""
Segment modelisation classes
"""

import codecs
import collections
import csv
import json
import logging
import os
import pickle
import tempfile

from collections import OrderedDict
from datetime import datetime
from nltk.tokenize import WhitespaceTokenizer

# check if the current file is in a folder name "src"
EXEC_FROM_SOURCE = os.path.dirname(os.path.abspath(__file__)).split("/")[-1] == "src"

# symbol for merged original raws
MERGE_SYMBOL = "<<MERGED<<"


class Segment:
    def __init__(self, raw, participant, time, date):
        """
        Segment constructor
        """
        self.id = id(self)  # random unique ID
        self.raw = raw  # raw text
        self.original_raw = raw  # full original raw text
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
            "segment": self.raw,
            "raw": self.original_raw,
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
        data.update({"segment": self.raw})
        data.update({"raw": self.original_raw if isinstance(self.original_raw, str) else MERGE_SYMBOL.join(self.original_raw)})
        data.update({"participant": self.participant})
        data.update({"date": self.date})
        data.update({"time": self.time})
        data.update({"note": self.note if self.note is not None else ""})
        data.update({"links": ",".join(["{}-{}".format(segment.id, lt) for segment, lt in self.links])})

        for layer in labels.keys():
            if layer in self.annotations:
                # label
                data.update({layer: self.annotations[layer]["label"]})

                if "qualifier" in self.annotations[layer]:
                    # qualifier
                    data.update({layer: self.annotations[layer]["label"]})
                else:
                    # empty qualifier
                    data.update({layer + "-value": ""})
            else:
                # empty label
                data.update({layer: ""})
                # empty qualifier
                data.update({layer + "-value": ""})

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

    def create_link(self, target, link_type):
        """
        Creates a link towards another segment
        """
        self.links.append((target, link_type))
        target.linked.append((self, link_type))

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

        # preserving original raws, as a list
        original_raw = []

        if isinstance(segment.original_raw, str):
            original_raw.append(segment.original_raw)
        else:
            original_raw = segment.original_raw

        if isinstance(self.original_raw, str):
            original_raw.append(self.original_raw)
        else:
            original_raw = original_raw + self.original_raw

        self.original_raw = original_raw

        self.tokenize()

        self.annotations = self.update(self.annotations, segment.annotations)
        self.legacy = self.update(self.legacy, segment.legacy)

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

    def update(self, data1, data2):
        """
        Updates a dictionary with nested values
        """
        for k, v in data2.items():
            if isinstance(v, collections.Mapping):
                r = self.update(data1.get(k, {}), v)
                data1[k] = r
            else:
                data1[k] = data2[k]
        return data1

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
    """
    Class managing a collection of segments
    """
    # paths
    save_dir = "../sav/" if EXEC_FROM_SOURCE else "sav/"
    taxo_dir = "../tax/" if EXEC_FROM_SOURCE else "tax/"
    csv_dir = "../csv/" if EXEC_FROM_SOURCE else "csv/"
    custom_taxo_dir = "../tax/custom" if EXEC_FROM_SOURCE else "tax/"
    out_dir = "../out/" if EXEC_FROM_SOURCE else "out/"
    temp_dir = "{}/diannotator/".format(tempfile.gettempdir())

    def __init__(self):
        """
        Initialization of the segment collection
        """
        self.save_file = os.path.abspath("{}tmp.pic".format(SegmentCollection.save_dir))

        self.full_collection = []  # full collection of segments
        self.collection = self.full_collection.copy()  # current collection used
        self.annotations = {}  # list of annotations

        self.taxonomy = None  # taxonomy name

        self.labels = {}  # label tagsets
        self.qualifiers = {}  # label qualifier tagsets
        self.colors = {}  # layer colors
        self.links = {}  # link types

        self.i = 0  # collection index
        self.layer = None  # active layer
        self.default_layer = None  # default layer
        self.filter = False  # active filter

    ######################
    # NAVIGATION METHODS #
    ######################

    def next(self, n=1):
        """
        Sets the index to the next segment
        """
        self.i = self.i + n if self.i + n < len(self.collection) else self.i

    def previous(self, n=1):
        """
        Sets the index to the previous segment
        """
        self.i = self.i - n if self.i - n >= 0 and self.collection else self.i  # must check if collection not empty

    ##################
    # ACCESS METHODS #
    ##################

    def get_active(self):
        """
        Returns the active segment
        """
        return self.collection[self.i]

    def get_active_label(self):
        """
        Returns the active segment's label
        """
        segment = self.get_active()

        if self.layer in segment.annotations and "label" in segment.annotations[self.layer]:
            return segment.annotations[self.layer]["label"]
        else:
            return False

    def get_active_qualifier(self):
        """
        Returns the active segment's qualifier
        """
        segment = self.get_active()

        if self.layer in segment.annotations and "qualifier" in segment.annotations[self.layer]:
            return segment.annotations[self.layer]["qualifier"]
        else:
            return False

    def get_segment_indexes(self, segment):
        """
        Return a tuple of segment indexes
        """
        return (self.collection.index(segment), self.full_collection.index(segment))

    ########################
    # MODIFICATION METHODS #
    ########################

    def remove(self, segment):
        """
        Removes a segment
        """
        ci = self.collection.index(segment)
        self.collection.remove(segment)
        fi = self.full_collection.index(segment)
        self.full_collection.remove(segment)

    def insert(self, i, fi, insert):
        """
        Inserts a segment at a specific index
        """
        # insert into full collection
        self.full_collection.insert(i, insert)

        # insert into active collection
        self.collection.insert(fi, insert)

    def insert_after_active(self, insert):
        """
        Inserts a segment after the active one
        """
        # insert into full collection
        self.full_collection.insert(self.full_collection.index(self.get_active()) + 1, insert)

        # insert into active collection
        self.collection.insert(self.i + 1, insert)

    #################################
    # TAXONOMY MODIFICATION METHODS #
    #################################

    def change_label(self, layer, label, new_label):
        """
        Renames a label
        """
        index = self.labels[layer].index(label)
        self.labels[layer].remove(label)

        if new_label not in self.labels[layer]:
            self.labels[layer].insert(index, new_label)

        for segment in list(set(self.collection + self.full_collection)):
            if layer in segment.annotations:
                # replace label
                segment.annotations[layer]["label"] = new_label

    def change_qualifier(self, layer, qualifier, new_qualifier):
        """
        Renames a qualifier
        """
        index = self.qualifiers[layer].index(qualifier)
        self.qualifiers[layer].remove(qualifier)

        if new_qualifier not in self.qualifiers[layer]:
            self.qualifiers[layer].insert(index, new_qualifier)

        for segment in list(set(self.collection + self.full_collection)):
            if layer in segment.annotations:
                # replace qualifier
                segment.annotations[layer]["qualifier"] = new_qualifier

    def delete_label(self, layer, label):
        """
        Deletes a label
        """
        self.labels[layer].remove(label)

        for segment in list(set(self.collection + self.full_collection)):
            if layer in segment.annotations and "label" in segment.annotations[layer] and segment.annotations[layer]["label"] == label:
                del segment.annotations[layer]

    def delete_qualifier(self, layer, qualifier):
        """
        Deletes a qualifier
        """
        self.qualifiers[layer].remove(qualifier)

        for segment in list(set(self.collection + self.full_collection)):
            if layer in segment.annotations and "qualifier" in segment.annotations[layer] and segment.annotations[layer]["qualifier"] == qualifier:
                del segment.annotations[layer]["qualifier"]

    def add_layer(self, layer):
        """
        Adds a new layer to the tagset
        """
        self.labels[layer] = []

    def add_label(self, layer, label):
        """
        Adds a new label to the tagset
        """
        if label not in self.labels[layer]:
            self.labels[layer].append(label)

    def add_qualifier(self, layer, qualifier):
        """
        Adds a new qualifier to the tagset
        """
        if qualifier not in self.qualifiers[layer]:
            self.qualifiers[layer].append(qualifier)

    def delete_layer(self, layer):
        """
        Deletes a layer
        """
        # remove the layer from the taxonomy
        del self.labels[layer]

        # remove the layer from all annotations
        for segment in list(set(self.collection + self.full_collection)):
            if layer in segment.annotations:
                del segment.annotations[layer]

        # changes the default layer if needed
        if layer == self.default_layer:
            self.default_layer = list(self.labels.keys())[0]

        # changes the active layer
        self.layer = self.default_layer

    ##################################
    # TAXONOMY IMPORT/EXPORT METHODS #
    ##################################

    def import_taxonomy(self, path):
        """
        Imports the collection's taxonomy from a JSON file
        """
        try:
            taxonomy = json.loads(codecs.open(path, encoding="utf-8").read())

            self.taxonomy = taxonomy["name"]
            self.layer = self.default_layer = taxonomy["default"]

            self.labels = taxonomy["labels"]  # label tagsets
            self.qualifiers = taxonomy["qualifiers"]  # label qualifier tagsets
            self.colors = taxonomy["colors"]  # layer colors
            self.links = taxonomy["links"]  # link types
        except Exception as e:
            logging.exception("DialogueActCollection.import_taxonomy()")
            return False

        return True

    def export_taxonomy(self, path):
        """
        Exports the collection's taxonomy to a JSON file
        """
        taxonomy = {
            "name": self.taxonomy,
            "default": self.default_layer,
            "colors": self.colors,
            "labels": self.labels,
            "qualifiers": self.qualifiers,
            "links": self.links
        }

        try:
            with open(path, "w") as f:
                json.dump(taxonomy, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.exception("DialogueActCollection.export_taxonomy()")
            return False

        return True

    ####################################
    # COLLECTION IMPORT/EXPORT METHODS #
    ####################################

    def import_collection(self, path):
        """
        Imports a new collection from a CSV file
        """
        # backup of the full collection
        collection = self.collection
        full_collection = self.full_collection

        try:
            self.full_collection = []

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

                # loading legacy annotations
                for key in row.keys():
                    if key not in ["segment", "raw", "time", "date", "participant", "links", "note", "id"] and row[key] is not None and row[key].strip() != "":
                        if key.endswith("-value") and row[key]:
                            # getting layer name from column
                            layer = key[:len(key) - len("-value")]

                            # create layer if does not exist
                            if layer not in segment.legacy:
                                segment.legacy[layer] = {}

                            # adding qualifier
                            segment.legacy[layer]["qualifier"] = row[key]
                        else:
                            # create layer if does not exist
                            if key not in segment.legacy:
                                segment.legacy[key] = {}

                            # adding label
                            segment.legacy[key]["label"] = row[key]

                # set note
                segment.note = row["note"].strip() if "note" in row and row["note"].strip() else None

                # adds the segment to the full collection
                self.full_collection.append(segment)

            # syncs the current collection to the full collection
            self.collection = self.full_collection.copy()

            # resets the index
            self.i = 0

            # writes save path to /tmp
            self.write_save_path_to_tmp()
        except Exception as e:
            self.collection = collection
            self.full_collection = full_collection

            logging.exception("DialogueActCollection.import_collection()")

            return False

        return True

    def export_collection(self, path):
        """
        Exports the collection to the filesystem
        """
        try:
            if path.endswith(".json"):
                self.export_collection_as_json(path)
            elif path.endswith(".csv"):
                self.export_collection_as_csv(path)
        except Exception as e:
            logging.exception("DialogueActCollection.export_collection()")
            return False

        return True

    def export_collection_as_json(self, path):
        """
        Exports the collection in JSON format
        """
        data = [segment.to_json_dict() for segment in self.full_collection]

        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.exception("")
            return False

        return True

    def export_collection_as_csv(self, path):
        """
        Exports the collection in CSV format
        """
        with open(path, "w") as f:
            w = csv.DictWriter(f, self.full_collection[0].to_csv_dict(self.labels).keys(), delimiter="\t")
            w.writeheader()

            previous_raw = None
            for segment in self.full_collection:
                row = segment.to_csv_dict(self.labels)

                if row["raw"] == previous_raw:
                    row["raw"] = ""  # no consecutives raws, should be left empty

                w.writerow(row)

                previous_raw = row["raw"]

    ###########################
    # SAVE MANAGEMENT METHODS #
    ###########################

    def save(self, path=None, backup=False):
        """
        Serializes the SegmentCollection and writes it to the filesystem
        """
        if self.layer is None:
            return False

        try:
            with open(path if path is not None else self.save_file, "wb") as f:
                pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

            if path and not backup:
                self.save_file = os.path.abspath(path)
                self.write_save_path_to_tmp()
        except Exception:
            logging.exception("DialogueActCollection.save()")
            return False

        return True

    def write_save_path_to_tmp(self):
        """
        Writes the path to the current save file to /tmp
        """
        try:
            if not os.path.exists(SegmentCollection.temp_dir):
                os.makedirs(SegmentCollection.temp_dir)

            with open("{}last_save.tmp".format(SegmentCollection.temp_dir), "w") as tmp:
                tmp.write(self.save_file)
        except Exception as e:
            logging.exception("DialogueActCollection.write_save_path_to_tmp()")
            return False

        return True

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
    def delete_save_path_on_tmp():
        """
        Deletes the previous save file from /tmp
        """
        if not os.path.exists(SegmentCollection.temp_dir):
            return

        path = "{}last_save.tmp".format(SegmentCollection.temp_dir)

        if not os.path.exists(path):
            return

        os.remove(path)

    @staticmethod
    def load(path):
        """
        Loads a serialized SegmentCollection
        """
        try:
            with open(path, "rb") as f:
                sc = pickle.load(f)
                sc.write_save_path_to_tmp()

                return sc
        except Exception as e:
            logging.exception("DialogueActCollection.load()")
            return False

        return False
