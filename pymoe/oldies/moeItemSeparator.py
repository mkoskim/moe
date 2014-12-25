#!/usr/bin/env python
###############################################################################
#
# MTE Separator Items
#
###############################################################################

import string

from config import conf
from helpers import *
from moeGTK import *

from moeItemDoc import DocItem

#------------------------------------------------------------------------------
#
# Separator items
#
#------------------------------------------------------------------------------

class SeparatorItem(DocItem):

    def __init__(self, parent, label):
        super(SeparatorItem,self).__init__(parent)

        self.label = label
        self.view = parent.emptypage

    def getWordCount(self): return ""

    def getName(self): return ""
    
    def getSeparator(self): return self.label

#------------------------------------------------------------------------------
#
# Separator items
#
#------------------------------------------------------------------------------

class FrontmatterItem(SeparatorItem):

    def __init__(self, parent):
        super(FrontmatterItem,self).__init__(parent, "Frontmatter")

class MainmatterItem(SeparatorItem):

    def __init__(self, parent):
        super(MainmatterItem,self).__init__(parent, "Mainmatter")

class BackmatterItem(SeparatorItem):

    def __init__(self, parent):
        super(BackmatterItem,self).__init__(parent, "Backmatter")
    
