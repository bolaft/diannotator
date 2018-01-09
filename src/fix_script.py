#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# DiAnnotator
#
# Author: Soufian Salim <soufi@nsal.im>
#
# URL: <http://github.com/bolaft/diannotator>

"""
Fix script
"""

from model import SegmentCollection

path_pic = "../sav/final.pic"
path_out = "../sav/out_final.pic"
path_csv = "../csv/ubuntu-irc-fr.csv"
path_tax = "../tax/Ubuntu_CMC.json"

if __name__ == "__main__":
    csv_sc = SegmentCollection()
    csv_sc.full_collection = csv_sc.import_collection_from_csv(path_csv)
    csv_sc.import_taxonomy(path_tax)
    pic_sc = SegmentCollection.load(path_pic)

    original_raw = "<<<NONE>>>"

    for pic_segment in pic_sc.full_collection:
        if original_raw == pic_segment.original_raw:
            pic_segment.original_raw = ""

        if pic_segment.original_raw:
            original_raw = pic_segment.original_raw

    pic_sc.save(path=path_out)
