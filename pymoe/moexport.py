#!/usr/bin/env python
###############################################################################
#
# Document exporting to stdout, used when scripting
#
###############################################################################

import sys

from config import conf
from helpers import *    
from moeXML import *

from moeExport import exportTree

###############################################################################
###############################################################################

if __name__ == "__main__":
    if len(sys.argv) == 3:
        filename, fmt = sys.argv[1], sys.argv[2]
        content = readfile(filename)
        conf.load(filename)
        content = content.encode("utf-8")
        tree = ET.ElementTree(ET.fromstring(content))
        content = exportTree(tree.getroot(), fmt)
        print>>sys.stdout, content
    else:
        print>>sys.stderr, "Usage: %s <source> <fmt>" % os.path.basename(sys.argv[0])
