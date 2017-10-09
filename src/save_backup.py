#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from model import DialogueActCollection
from datetime import datetime

dac = DialogueActCollection.load()
dac.save(name=datetime.now().strftime("%d-%m-%y_%X"))
