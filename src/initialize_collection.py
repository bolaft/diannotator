#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from model import DialogueActCollection

dac = DialogueActCollection()
dac.load_raw(DialogueActCollection.data_file)
dac.save()
