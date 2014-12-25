#!/usr/bin/env python
###############################################################################
#
# Convert moe files to newest versions
#
###############################################################################

import sys

from moeDocument import Document

if len(sys.argv) < 2:
    print>>sys.stderr, "Usage: moeconvert.py <filename> ..."
    sys.exit(-1)

for filename in sys.argv[1:]:
    doc = Document(None, filename)
    doc.save()
