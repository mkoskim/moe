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

class TitleItem(DocItem):

    doctypes = [
        [ "shortstory", "Short Story" ],
        [ "longstory",  "Long Story" ],
    ]

    opt_toplevel = [
        [ "chapters", "Chapters" ],
        [ "parts", "Parts" ],
        [ "hiddenparts", "Hidden Parts" ],
    ]
    
    opt_chapters = [
        [ "separated", "Separated (* * *)" ],
        [ "numbered",  "Numbered" ],
        [ "named",     "Named" ],
        [ "both",      "Numbered & Named" ],
    ]
    
    opt_prologue = [
        [ "None",    "No" ],
        [ "unnamed", "Yes, unnamed" ],
        [ "named",   "Yes, named" ],
    ]
    
    opt_epilogue = [
        [ "None",  "No" ],
        [ "named", "Yes, named" ],
    ]

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self, document, ET = None, root = None):
        super(TitleItem,self).__init__(document)

        self.keep_first = True
        self.sticky     = True
        self.removable  = False
        
        self.included   = True
        self.alterable  = False
        
        self.synonyms = {
            "toplevel": "opt_toplevel",
            "chapters": "opt_chapters",
            "prologue": "opt_prologue",
            "epilogue": "opt_epilogue",
            "opt_synopsis": None,
        }
        
        self.elements = {
            "title": TextBuf(),
            "subtitle": TextBuf(),
            "author": TextBuf(),
            "website": TextBuf(),
            "version": TextBuf(),
            "translated": TextBuf(),
            "status": TextBuf(),
            "deadline": TextBuf(),
            "coverpage": TextBuf(),

            "published": TextBuf(),
            "publisher": TextBuf(),
            "year": TextBuf(),

            "type":     TextCombo(self.doctypes),
            "opt_toplevel": TextCombo(self.opt_toplevel),
            "opt_chapters": TextCombo(self.opt_chapters),
            "opt_prologue": TextCombo(self.opt_prologue),
            "opt_epilogue": TextCombo(self.opt_epilogue),

            "synopsis": TextBuf(),
        }
        
        self.attributes = [
            "type",
            "opt_toplevel",
            "opt_chapters",
            "opt_prologue",
            "opt_epilogue"
        ]
        
        self.searchfields = [
            "title", "subtitle", "author", "website",
            "version", "status", "deadline",
            "published", "publisher", "year",
            "synopsis"]
        self.officialfields = [
            "title", "subtitle", "author", "coverpage"
        ]
        self.visiblenames = {
            "title": "Title",
            "subtitle": "Subtitle",
            "author": "Author",
            "website": "Website",
            "translated": "Translated",
            "version": "Version",
            "status": "Status",
            "deadline": "Deadline",
            "coverpage": "Coverpage",

            "synopsis": "Synopsis",

            "type":         "Type",
            "opt_toplevel": "Contains",
            "opt_chapters": "Chapters",
            "opt_prologue": "Prologue",
            "opt_epilogue": "Epilogue",

            "published": "Published",
            "publisher": "Publisher",
            "year": "Year",
        }
        
        if root == None:
            self.new()
        else:
            self.load(ET, root)
        
        self.document.watchRenum(
            self.elements["opt_toplevel"],
            self.elements["opt_prologue"],
            self.elements["opt_epilogue"],
        )
        
        self.title = self.elements["title"]
        self.name  = self.title
        self.title.connect("changed", self.cbNameModified)

        for val in self.elements.values():
            document.watchDirty(val)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def getTopLevel(self):
        return {
            "chapters": 1,
            "parts": 2,
            "hiddenparts": 2,
        }[self.elements["opt_toplevel"].get_content()]

    def hasPrologue(self):
        return self.elements["opt_prologue"].get_content() != "None"
        
    def hasEpilogue(self):
        return self.elements["opt_epilogue"].get_content() != "None"
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def getContentEditor(self):
        #filebox = gtk.HBox()
        #filebox.pack_start(self.filelabel, False, False)

        titleedit = createTextBox(self.elements["title"], 1, 2, 2)

        def gridEntry(elem):
            return [ self.visiblenames[elem], createEntry(self.elements[elem]) ]
            
        def gridAsIs(elem):
            return [ self.visiblenames[elem], self.elements[elem] ]

        basicbox = createEditGrid(
            None,
            [
                [ self.visiblenames["title"], titleedit ],
                gridEntry("subtitle"),
                [ gtk.HSeparator() ],
                gridEntry("author"),
                gridEntry("website"),
                [ gtk.HSeparator() ],
                gridEntry("translated"),
                [ gtk.HSeparator() ],
                gridEntry("status"),
                gridEntry("version"),
                gridEntry("deadline"),
                [ gtk.HSeparator() ],
                gridEntry("coverpage"),
            ],
            False, False
        )
        
        synopsisbox = createScrolledTextBox(self["synopsis"])
        
        publishbox = createEditGrid(
            None,
            [
                gridEntry("published"),
                gridEntry("publisher"),
                gridEntry("year"),
            ],
            False, False
        )
        
        outlookbox = createEditGrid(
            None,
            [
                gridAsIs("type"),
                gridAsIs("opt_toplevel"),
                gridAsIs("opt_chapters"),
                gridAsIs("opt_prologue"),
                gridAsIs("opt_epilogue"),
            ],
            False, False
        )
        
        def gridViaVBox(grid, p1 = False, p2 = False):
            vbox = gtk.VBox()
            vbox.pack_start(grid, p1, p2, 0)
            return vbox
        
        notebook = gtk.Notebook()
        notebook.append_page(gridViaVBox(basicbox), gtk.Label("Headings"))
        notebook.append_page(synopsisbox, gtk.Label("Synopsis"))
        notebook.append_page(gridViaVBox(outlookbox), gtk.Label("Outlook"))
        notebook.append_page(gridViaVBox(publishbox), gtk.Label("Publishing"))
        
        viewbox = gtk.VBox()
        viewbox.pack_start(notebook, False, False)
        #viewbox.pack_start(
        #    createFrame
        #    (
        #        "Synopsis",
        #        createTextBox(
        #            self.elements["synopsis"],
        #            border_width = 5
        #        )
        #    ), True, True
        #)
        viewbox.grabber = titleedit.grabber

        return viewbox

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def getName(self): return self.title.get_content()
    
    def getSeparator(self): return ""
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------
    
    def new(self):
        #super(TitleItem,self).new()
        self.elements["title"].set_content("<Unnamed Story>")
        self.elements["author"].set_content(conf.get_default("author"))
        self.elements["website"].set_content(conf.get_default("website"))
        self.elements["status"].set_content(conf.get_default("status"))
        
        self.elements["author"].set_modified(False)
        self.elements["website"].set_modified(False)
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------
    
    def save(self, ET, root):
        if self["author"].get_modified() and conf.get_default_level("author") == "sys":
            conf.set_default("author", None, self["author"].get_content())

        if self["website"].get_modified() and conf.get_default_level("website") == "sys":
            conf.set_default("website", None, self["website"].get_content())
            
        return super(TitleItem,self).save(
            ET,
            ET.SubElement(root, "TitleItem")
        )

