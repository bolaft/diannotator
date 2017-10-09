#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from model import DialogueActCollection

collection = DialogueActCollection.load().full_collection
print(collection[0])
