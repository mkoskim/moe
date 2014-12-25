#!/usr/bin/env python
###############################################################################
#
# Contiguous view mode for creating text as one big buffer.
#
# This mode is built on "flattening" and "deflattening" abilities of a
# document (see: moeDocument). Included content is appended to a buffer
# as contiguous text, which is then edited by simple edit box. When
# deflattening, modifications are put back to tree.
#
# Because of this, it is not possible to restructure text in contiguous
# mode (may be changed in future). Also, many tools don't work for
# flattened text, meaning that before using them, text must be deflattened.
#
# Flattened buffer contains tags to separate scenes.
#
###############################################################################

from config import conf
from helpers import *
from moeGTK import *

###############################################################################
#
# ToC listbox for cont'd view
#
###############################################################################

class TocBox(gtk.TreeView):

    def __init__(self, blocks):
        super(TocBox,self).__init__()

        model = gtk.ListStore(str, object)

        for item in blocks:
            if item.index: model.append((item.index, item.start))

        cr = gtk.CellRendererText()
        tc = gtk.TreeViewColumn("Content")
        tc.pack_start(cr, True)
        tc.add_attribute(cr, "text", 0)
        self.append_column(tc)

        self.set_model(model)

###############################################################################
#
# Contiguous editing view
#
###############################################################################

class EditorViewFlatten(gtk.HPaned):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def switchIn(self):
        self.set_position(int(conf.get_gui("DraftView", "index_width")))
        
    def switchOut(self):
        #print "Contiguous view: Switching out"
        conf.set_gui("DraftView", "index_width", self.get_position())
        self.document.deflatten()
        self.document.flat.disconnect(self.dirty_handler)
        self.document.flat = None
        
    #--------------------------------------------------------------------------
    # When clicking toc box, place cursor
    #--------------------------------------------------------------------------

    def cbTocClick(self, treeview, event = None):
        model = treeview.get_model()
        path, col = treeview.get_cursor()
        mark = model[path][1]
 
        flatbuf = self.document.flat
        
        flatbuf.place_cursor(flatbuf.get_iter_at_mark(mark))
        self.contentedit.grabber.scroll_to_mark(mark, 0.2)
        self.contentedit.grabber.grab_focus()
       
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbToggleSynopses(self, widget):
        tagtbl = self.document.flat.get_tag_table()
        tag = tagtbl.lookup("synopsis")
        tag.set_property("invisible", not widget.get_active())
        conf.set_doc("DraftEdit", "Synopses", widget.get_active())

    #--------------------------------------------------------------------------
    # 
    #--------------------------------------------------------------------------

    def __init__(self, document, mode = None):
        super(EditorViewFlatten,self).__init__()

        if document == None: return        
        self.document = document

        self.dirty_handler = self.document.flat.connect(
            "changed",
            self.document.cbModified
        )
        
        #----------------------------------------------------------------------
        # Editing components
        #----------------------------------------------------------------------

        vbox = gtk.VBox()
        
        toolbar = ToolBar(
            ToolBar.CheckButton(
                "Synopses",
                (conf.get_doc("DraftEdit", "Synopses") == "True"),
                self.cbToggleSynopses,
                "Toggle synopses on/off"
            ),
        )
        
        authoredit = createEntry(
            self.document.title.elements["author"],
            justify = gtk.JUSTIFY_CENTER,
        )
        titleedit = createEntry(
            self.document.title.elements["title"],
            font="14",
            justify = gtk.JUSTIFY_CENTER,
        )
        self.contentedit = createScrolledTextBox(
            self.document.flat,
            pad_leftright = 40,
            pad_topbottom = 20,
        )
        
        vbox.pack_start(toolbar,  False, False, 0)
        vbox.pack_start(self.contentedit, True, True, 0)
        
        self.pack2(vbox)

        #----------------------------------------------------------------------
        # Synopsis + ToC
        #----------------------------------------------------------------------
    
        self.tocbox = TocBox(self.document.flat.blocks)
        self.tocbox.connect("button-release-event", self.cbTocClick)
        
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.tocbox)
        sw.grabber = self.tocbox

        self.pack1(sw)
        
        """synopsisbox = createFrame(
            "Synopsis",
            createTextBox(
                self.document.flat.synopsis,
                pad_leftright = 10,
                pad_topbottom = 5,
                bgcolor = conf.bg_synopses
            )
        )
                    
        vbox = gtk.VBox()
        vbox.pack_start(synopsisbox, False, False)
        vbox.pack_start(sw, True, True)

        self.pack1(vbox)"""

        #----------------------------------------------------------------------
        #----------------------------------------------------------------------

        self.grabber = self.contentedit.grabber

###############################################################################
#
# New editing view
#
###############################################################################

class EditorViewNew(gtk.HBox):

    def __init__(self, document, scene, mode = None):
        super(EditorViewNew,self).__init__()

        if document == None: return        
        self.document = document

        authoredit = createEntry(
            self.document.title["author"],
            justify = gtk.JUSTIFY_CENTER,
        )
        titleedit = createEntry(
            self.document.title["title"],
            font="14",
            justify = gtk.JUSTIFY_CENTER,
        )
        contentedit = createScrolledTextBox(
            scene["content"],
            pad_leftright = 40,
            pad_topbottom = 20,
        )
        
        vbox = gtk.VBox()
        vbox.pack_start(authoredit,   False, False, 0)
        vbox.pack_start(titleedit,    False, False, 0)
        vbox.pack_start(contentedit,  True, True, 0)
        
        width = int(conf.get_gui("DraftView", "index_width"))

        leftpad = gtk.Label()
        leftpad.set_size_request(width / 2, -1)
        rightpad = gtk.Label()
        rightpad.set_size_request(width / 2, -1)
        
        self.pack_start(leftpad, False, False)
        self.pack_start(vbox, True, True)
        self.pack_start(rightpad, False, False)
        
        self.grabber = contentedit.grabber
        
