#!/usr/bin/env python
###############################################################################
#
# General group
#
###############################################################################

import string
import re

from config import conf
from helpers import *
from moeGTK import *

from moeItemDoc import DocItem

class GroupItem(DocItem):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(
        self, document, ET = None, root = None,
        name = None,
        level = -1,
        included = True,
        alterable = True
    ):
        super(GroupItem,self).__init__(document)

        self.synonyms = {
            "todo": None,
            "description": "synopsis",
            "sketch": "comments",
        }
        
        self.elements = {
            "name": TextBuf(),
            "synopsis": TextBuf(),
            "comments": TextBuf(),
        }
        self.attributes = []
        
        self.searchfields   = [ "name", "synopsis", "sketch" ]
        self.officialfields = [ "name" ]
        self.visiblenames = {
            "name": "Name",
            "synopsis": "Synopsis",
            "comments": "Comments",
        }
            
        self.name = self.elements["name"]
        self.name.connect("changed", self.cbNameModified)
        self.number = "1"
        
        self.included = included
        self.alterable = alterable
        self.level = level
        
        if root == None:
            self.new(name)
        else:
            self.load(ET, root)
                
        for val in self.elements.values():
            document.watchDirty(val)
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def getContentEditor(self):
        namebox   = createTextBox(self.elements["name"], 1, 2, 2)
        descbox   = createTextBox(self.elements["synopsis"], 1, 2, 2)
        sketchbox = createTextBox(self.elements["comments"], 1, 2, 2)
        
        grid = createEditGrid(
            None,
            [
                [self.visiblenames["name"], namebox],
                [self.visiblenames["synopsis"], descbox],
                [self.visiblenames["comments"], sketchbox],
            ],
        )

        vbox = gtk.VBox()
        vbox.pack_start(grid, False, False)
        vbox.pack_start(gtk.Label())
        vbox.grabber = descbox.grabber
        return vbox
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def getName(self): return self.name.get_content()

    def getSeparator(self):
        return ""
        #if self.level == 1:
        #    return "%d. luku" % self.number
        #elif self.level == 2:
        #    return "Osa %s" % int2roman(self.number)
        #else:
        #    return ""
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def new(self, name = "<Unnamed Group>"):
        #super(ChapterItem,self).new()
        self.name.set_content(name)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def save(self, ET, root):
        elem = ET.SubElement(root, "GroupItem")
        elem.set("level", str(self.level))
        elem.set("alterable", str(self.alterable))
        return super(GroupItem,self).save(ET, elem)

    
