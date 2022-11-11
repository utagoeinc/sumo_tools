#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2009-2022 German Aerospace Center (DLR) and others.
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0/
# This Source Code may also be made available under the following Secondary
# Licenses when the conditions for such availability set forth in the Eclipse
# Public License 2.0 are satisfied: GNU General Public License, version 2
# or later which is available at
# https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html
# SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later

# @file    rebuildConstants.py
# @author  Daniel Krajzewicz
# @author  Michael Behrisch
# @date    2009-07-24

"""
This script extracts definitions from <SUMO>/src/libsumo/TraCIConstants.h
 and builds the according constants definition python and java files
 "constants.py" and Constants.java.
 When called without options the script generates both files in the default
 locations. To generate just python give an output file name, for Java do:
 tools/traci/rebuildConstants.py -j de.tudresden.sumo.config.Constants
  -o tools/contributed/traas/src/main/java/de/tudresden/sumo/config/Constants.java
"""

from __future__ import print_function
from __future__ import absolute_import
import os
import datetime
import argparse
import re


def translateFile(filePath, fdo, java, start, item, end, item_parser):
    comment_marker = "//" if java else "#"
    with open(filePath) as fdi:
        started = False
        for line in fdi:
            if started:
                line = line.strip()
                if line.find(end) >= 0:
                    started = False
                    continue
                if java:
                    line = line.replace("//", "    //")
                else:
                    line = line.replace("///", "#").lstrip(" ")
                    line = line.replace("//", "# ").lstrip(" ")
                if line.find(item) >= 0 and comment_marker not in line:
                    (ctype, cname, cvalue) = item_parser(line)
                    if java:
                        line = "    public static final {} {} = {};".format(ctype, cname, cvalue)
                    else:
                        line = "{} = {}".format(cname, cvalue)
                print(line, file=fdo)
            if line.find(start) >= 0:
                started = True


def parseTraciConstant(line):
    match = re.search(r'(\S+) ([A-Z0-9_]+) = (\S+);', line)
    if match:
        return match.group(1, 2, 3)
    else:
        return None


def parseLaneChangeAction(line):
    line = line.rstrip(',')
    match = re.search('([A-Z0-9_]+) = (.+)', line)
    if match:
        return ('int', match.group(1), match.group(2))
    else:
        return None


dirname = os.path.dirname(__file__)
argParser = argparse.ArgumentParser()
argParser.add_argument("-j", "--java",
                       help="generate Java output as static members of the given class", metavar="CLASS")
argParser.add_argument("-o", "--output",
                       help="File to save constants into", metavar="FILE")
options = argParser.parse_args()
header = """# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2009-2022 German Aerospace Center (DLR) and others.
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0/
# This Source Code may also be made available under the following Secondary
# Licenses when the conditions for such availability set forth in the Eclipse
# Public License 2.0 are satisfied: GNU General Public License, version 2
# or later which is available at
# https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html
# SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later

# @file    <file>
# @author  generated by "%s"
# @date    %s

\"\"\"
This script contains TraCI constant definitions from <SUMO_HOME>/src/libsumo/TraCIConstants.h.\
""" % (os.path.basename(__file__), datetime.datetime.now())


outputs = [(options.output if options.output else os.path.join(dirname, "constants.py"), None)]
if options.output is None:
    outputs.append((dirname + "/../contributed/traas/src/main/java/de/tudresden/sumo/config/Constants.java",
                    options.java if options.java else "de.tudresden.sumo.config.Constants"))
for out, className in outputs:
    fdo = open(out, "w")
    h = header.replace("<file>", os.path.basename(out))
    if className:
        sep = "/%s/" % (76 * "*")
        print(sep, file=fdo)
        h = h.replace("\n# @file", sep + "\n/// @file").replace("# @", "/// @")
        print(h.replace("#", "//").replace('\n"""\n', "///\n// "), file=fdo)
        print(sep, file=fdo)
        if "." in className:
            package, className = className.rsplit(".", 1)
            fdo.write("package %s;\n" % package)
        fdo.write("public class %s {" % className)
    else:
        print(h, file=fdo)
        print('"""\n', file=fdo)

    srcDir = os.path.join(dirname, "..", "..", "src")
    translateFile(os.path.join(srcDir, "libsumo", "TraCIConstants.h"),
                  fdo, className is not None,
                  "namespace libsumo {", "TRACI_CONST ", "} // namespace libsumo", parseTraciConstant)

    translateFile(os.path.join(srcDir, "utils", "xml", "SUMOXMLDefinitions.h"),
                  fdo, className is not None,
                  "enum LaneChangeAction {", "LCA_", "};", parseLaneChangeAction)
    if className:
        fdo.write("}\n")
    fdo.close()
