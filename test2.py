#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys

cwd = os.getcwd()
sys.path.append(os.path.join("{}/".format(cwd)))

from test import *

pathcheck()
