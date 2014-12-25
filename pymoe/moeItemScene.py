#!/usr/bin/env python
###############################################################################
#
# Scene
#
###############################################################################

from config import conf
from helpers import *
from moeGTK import *

import string
import re

from moeItemDoc import DocItem

class SceneItem(DocItem):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    opt_formatting = [
        [ "normal", "Normal" ],
        [ "bold", "Bold" ],
        [ "italic", "Italic" ],
    ]
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self, document, ET = None, root = None,
        content = None,
        name = None,
        synopsis = None
    ):
        super(SceneItem,self).__init__(document)

        self.synonyms = {
            "todo": None,
            "conflict": None,
            "sketch": "comments",
            "description": "synopsis",
        }
        
        self.elements = {
            "name": TextBuf(),
            "content": TextBuf(),
            "synopsis": TextBuf(),
            "comments": TextBuf(),
            "formatting": TextCombo(self.opt_formatting),
        }
        self.attributes = [ "formatting" ]
        
        self.searchfields = [
            "name", "content",
            "synopsis", "sketch"
        ]
        self.officialfields = [ "name", "content" ]
        self.visiblenames = {
            "name": "Name",
            "content": "Content",
            "synopsis": "Synopsis",
            "comments": "Comments",
        }

        self.name = self.elements["name"]
        self.name.connect("changed", self.cbNameModified)
        self.included = True
        self.number = ""
        self.scene = None
        
        if root == None:
            self.new(name, synopsis, content)
        else:
            self.load(ET, root)
                
        for val in self.elements.values():
            document.watchDirty(val)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def getContentEditor(self):
        namebox = createEntry(self.elements["name"])
        descbox = createTextBox(
            self.elements["synopsis"],
            pad_leftright = 40,
            pad_topbottom = 10,
            bgcolor = conf.bg_synopses,
        )
        commentbox = createTextBox(
            self.elements["comments"],
            pad_leftright = 40,
            pad_topbottom = 10,
        )
        contentedit = createScrolledTextBox(
            self.elements["content"],
            pad_leftright = 40,
            pad_topbottom = 10,
        )

        topgrid = gtk.HBox()
        topgrid.pack_start(gtk.Label(self.visiblenames["name"]), False, False)
        topgrid.pack_start(namebox)
        topgrid.pack_start(self.elements["formatting"], False, False)

        topbox = gtk.VBox()

        topbox.synopsis = createFrame(
            "Synopsis",
            descbox,
            expander = True,
            expanded = (conf.get_doc("SceneEdit", "Synopses") == "True")
        )

        topbox.comments = createFrame(
            "Comments",
            commentbox,
            expander = True,
            expanded = (conf.get_doc("SceneEdit", "Comments") == "True")
        )

        topbox.pack_start(topgrid, False, False)
        topbox.pack_start(topbox.synopsis, False, False)
        topbox.pack_start(contentedit)
        topbox.pack_start(topbox.comments, False, False)

        def cbMapped(self):
            self.synopsis.set_expanded((conf.get_doc("SceneEdit", "Synopses") == "True"))
            self.comments.set_expanded((conf.get_doc("SceneEdit", "Comments") == "True"))

        def cbUnmapped(self):
            conf.set_doc("SceneEdit", "Synopses", self.synopsis.get_expanded())
            conf.set_doc("SceneEdit", "Comments", self.comments.get_expanded())
            
        topbox.connect("map", cbMapped)
        topbox.connect("unmap", cbUnmapped)
        
        topbox.grabber = contentedit.grabber
        return topbox
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def calcWordCount(self):
        return len(string.split(self.elements["content"].get_content()))

    def getSeparator(self):
        return ""        

    def getName(self):
        if self.scene:
            return "(%d) %s" % (self.scene, self.name.get_content())
        else:
            return self.name.get_content()
            
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def split(self):

        content = self.elements["content"]
        loc = content.get_iter_at_mark(content.get_insert())
        end = content.get_end_iter()
        
        text1 = content.get_slice(
            content.get_start_iter(),
            loc
        )
        text2 = content.get_slice(
            loc,
            content.get_end_iter()
        )
        if len(text1.strip()) == 0: return
        #if len(text.strip()) == 0: return
        
        splitted = SceneItem(self.document)
        splitted.included = self.included
        splitted["content"].set_content(text2)
        self["content"].set_content(text1)

        #text = [] + text.splitlines()
        #splitted.elements["content"].set_content(string.strip(string.join(text, "\n")))
        #content.delete(loc, content.get_end_iter())
        return splitted

    def merge(self, item):
        
        def insert_bufs(where, what, sep):
            mark = where.create_mark("merge", where.get_end_iter(), True)
            where.insert(
                where.get_end_iter(),
                sep + what.get_content()
            )
            where.place_cursor(where.get_iter_at_mark(mark))
            where.delete_mark(mark)
        
        if isinstance(item, SceneItem):
            insert_bufs(
                self.elements["synopsis"],
                item.elements["synopsis"],
                "\n\n"
            )
            insert_bufs(
                self.elements["comments"],
                item.elements["comments"],
                "\n\n"
            )
            insert_bufs(
                self.elements["content"],
                item.elements["content"],
                "\n\n---\n\n"
            )
            return True
        return False

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def new(self, name, synopsis, content):
        #super(SceneItem,self).new()

        self.name.set_content(name and name or "<Unnamed Scene>")

        if synopsis: self["synopsis"].set_content(synopsis)
        if content:  self["content"].set_content(content)

    def save(self, ET, root):
        return super(SceneItem,self).save(
            ET,
            ET.SubElement(root, "SceneItem")
        )

