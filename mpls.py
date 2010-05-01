#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Count election using Droop's Minneapolis rule

Copyright 2010 by Jonathan Lundell

This file is part of Droop.

    Droop is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Droop is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Droop.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys, os
import Droop
import droop

def usage():
    "mpls usage string"
    return "usage: %s ballot_file" % os.path.basename(sys.argv[0])

if len(sys.argv) != 2:
    print >>sys.stderr, usage()
    sys.exit(1)
try:
    print Droop.main(dict(rule='mpls', path=sys.argv[1]))
except (droop.common.UsageError, droop.common.ElectionError, droop.profile.ElectionProfileError) as err:
    print >>sys.stderr, "** mpls: %s" % err
    print >>sys.stderr, usage()
    sys.exit(1)
sys.exit(0)
