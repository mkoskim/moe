#!/usr/bin/env python
###############################################################################
#
# MTE Preview
#
###############################################################################

from config import conf
from helpers import *
from moeGTK import *

from moeDocIndexView import DocIndexView

###############################################################################
#
# MTE Preview
#
###############################################################################

class EditorViewOutline(gtk.VBox):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbRowActivated(self, view, path, col):
        item = view.get_model()[path][0]
        view = item.getContentEditor()
        if view == None: return
        
        window = gtk.Window()
        window.set_title("moe: " + item.getName())
        window.add(view)
        #allocation = self.notebook.get_allocation()
        #width, height = allocation.width, allocation.height
        window.resize(450, 700)
        window.show_all()

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self, document, mode = None):
        super(EditorViewOutline,self).__init__()

        self.document = document
        
        #----------------------------------------------------------------------
        # Create index
        #----------------------------------------------------------------------
        
        self.indexview = DocIndexView(self.document)
        self.indexview.connect("row-activated", self.cbRowActivated)
        #self.indexview.expand_all()

        def setMultiRow(cell, col, width):
            col.set_property("max_width", width)
            col.set_property("min_width", width-10)
            try:
                cell.set_property("wrap_mode", pango.WRAP_WORD)
                cell.set_property("wrap_width", width-10)
            except TypeError:
                pass


        cell,col = self.indexview.newColumn(
            "#",
            gtk.CellRendererText(), self.indexview.dfColNumber
        )
        self.indexview.set_expander_column(col)
        
        cell,col = self.indexview.newColumn(
            "Name",
            gtk.CellRendererText(),
            self.indexview.dfColName
        )
        setMultiRow(cell, col, 250)

        cell,col = self.indexview.newColumn(
            "Description",
            gtk.CellRendererText(),
            self.indexview.dfColSceneDescription
        )
        setMultiRow(cell, col, 400)

        cell, col = self.indexview.newColumn(
            "",
            gtk.CellRendererText(),
            self.indexview.dfColEmpty
        )
        
        #----------------------------------------------------------------------
        # Expand all _included_ groups
        #----------------------------------------------------------------------
        
        def doExpand(iter):
            item = self.document.get_value(iter, 0)
            #print "Expanding", item.name.get_content()
            if not item.included: return
            path = self.document.get_path(iter)
            self.indexview.expand_row(path, False)
            child = self.document.iter_children(iter)
            while child:
                doExpand(child)
                child = self.document.iter_next(child)
                
        iter = self.document.get_iter_first()
        while iter:
            doExpand(iter)
            iter = self.document.iter_next(iter)
        
        #----------------------------------------------------------------------
        # Create view
        #----------------------------------------------------------------------

        sw = gtk.ScrolledWindow()
        sw.add(self.indexview)
        
        self.pack_start(sw)      

