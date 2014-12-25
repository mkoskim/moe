#!/usr/bin/env python
###############################################################################
#
# Multi-part Text Editor Item superclass
#
###############################################################################

import os

from config import conf
from helpers import *
from moeGTK import *

#------------------------------------------------------------------------------
#
# These items can be added to index
#
#------------------------------------------------------------------------------

class DocItem(object):

    def __init__(self, document):
        self.document = document
        self.included = True
        self.namelabel = gtk.Label()

        self.words = None           # Buffered word count

        self.level = 0              # Group level, 0 = lowest

        self.removable = True       # Can be removed
        self.alterable = True       # Inclusion can be changed
        
        self.sticky = False         # Reordeable?
        self.keep_first = False     # Allow/disallow items before
        self.keep_last = False      # Allow/disallow items after
        
        self.searchfields   = None  # Fields for search
        self.officialfields = None  # "Official" search fields
        self.visiblenames   = None  # Visible names for fields
        
        #self.attributes = [ ]
        #self.attributes = [ "included", "words" ]
        
    # -------------------------------------------------------------------------
    # Connecting signals
    # -------------------------------------------------------------------------

    def connect_childs(self, signal, callback, *childs):
        for child in childs:
            child.connect(signal, callback)

    # -------------------------------------------------------------------------
    # Indexing
    # -------------------------------------------------------------------------

    def __getitem__(self, k):    return self.elements[k]
    def __setitem__(self, k, v): self.elements[k] = v

    # -------------------------------------------------------------------------
    # For saving
    # -------------------------------------------------------------------------

    def split(self): return None
    def merge(self, item): return False
    
    # -------------------------------------------------------------------------
    # Interface to gtk.TreeView
    # -------------------------------------------------------------------------
    
    def getWordCount(self): return self.words
    def setWordCount(self, words): self.words = words
    def calcWordCount(self): return 0
    
    def getName(self): return None
    def getSeparator(self): return None
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbNameModified(self, widget, event = None):
        self.namelabel.set_text(self.getName())
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def getNameLabel(self): return self.namelabel
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def load(self, ET, root):

        self.included = root.get("included") == "True"

        try:
            self.words = int(root.get("words"))
        except ValueError:
            self.words = None
        
        for tag in self.attributes:
            try:
                self.elements[tag].set_content(root.get(tag))
            except ValueError:
                pass
            
        for elem in root:
            if elem.tag == "childs": continue
            if hasattr(self,"synonyms") and elem.tag in self.synonyms:
                elem.tag = self.synonyms[elem.tag]
                if elem.tag == None: continue
            self.elements[elem.tag].set_content(elem.text)
            if hasattr(self.elements[elem.tag], "set_modified"):
                self.elements[elem.tag].set_modified(False)
            
    def file_content(self): return None
        
    def save(self, ET, root):
        root.set("words", str(self.words))
        root.set("included", str(self.included))
        for key in self.elements.keys():
            if key in self.attributes:
                root.set(key, self.elements[key].get_content())
            else:
                elem = ET.SubElement(root, key)
                elem.text = self.elements[key].get_content()
        return root
