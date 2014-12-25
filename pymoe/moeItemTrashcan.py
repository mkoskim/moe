#!/usr/bin/env python
###############################################################################
#
# Scene
#
###############################################################################

from config import conf
from helpers import *
from moeGTK import *

from moeItemDoc import DocItem

class TrashcanItem(DocItem):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self, document):
        super(TrashcanItem,self).__init__(document)

        self.keep_last  = True
        self.sticky     = True
        self.removable  = False
        
        self.included   = False
        self.alterable  = False
        
        self.level = 3
        self.name = None
        
    def getName(self): return "<Trashcan>"
    
    def getSeparator(self): return ""
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def load(self, ET, root): return            
    def save(self, ET, root): return None

