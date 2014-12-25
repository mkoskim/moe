from config import conf
from helpers import *
from moeGTK import *

from moeDocument import Document

#------------------------------------------------------------------------------
# Treeview for showing snippet hierarchy
#------------------------------------------------------------------------------

class SnippetView(gtk.TreeView):

    def __init__(self, snippets):
        super(SnippetView,self).__init__()
        self.set_model(snippets)

    #--------------------------------------------------------------------------
    # Columns
    #--------------------------------------------------------------------------

    def addColumn(self, col, cell, datafunc):
        col.pack_start(cell, False)
        col.set_cell_data_func(cell, datafunc)
        cell.set_property("yalign", 0.0)
        return cell, col

    def newColumn(self, name, cell, datafunc):
        col = gtk.TreeViewColumn(name)
        self.append_column(col)
        return self.addColumn(col, cell, datafunc)

    #--------------------------------------------------------------------------
    # Column data functions
    #--------------------------------------------------------------------------

    def dfColSeparator(self, tvcol, cell, model, index):
        item = model.get_value(index, 0)
        separator = item.getSeparator()
        cell.set_property("text", separator)

    def dfColName(self, tvcol, cell, model, index):
        item = model.get_value(index, 0)
        cell.set_property("text", item.getName())
        pass                

#------------------------------------------------------------------------------
# Dialog for selecting snippets
#------------------------------------------------------------------------------

class SnippetDialog(gtk.Dialog):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbRowActivated(self, view, path, col):
        self.response(gtk.RESPONSE_OK)
        
    def __init__(self, filename = None):
        super(SnippetDialog,self).__init__()

        if not filename: filename = conf.defsdir + "/snippets.moe"
        self.snippets = Document(self, filename)
        
        self.treeview = SnippetView(self.snippets)
        self.treeview.set_size_request(300, 300)
        self.treeview.connect("row-activated", self.cbRowActivated)

        cell,col = self.treeview.newColumn(
            "Name",
            gtk.CellRendererText(), self.treeview.dfColSeparator
        )

        cell,col = self.treeview.addColumn(
            col,
            gtk.CellRendererText(), self.treeview.dfColName
        )
        self.treeview.set_expander_column(col)

        #----------------------------------------------------------------------
        #----------------------------------------------------------------------

        #vbox = self.get_content_area()
        vbox = self.vbox
        
        vbox.pack_start(self.treeview, False, False)
        
        #----------------------------------------------------------------------
        #----------------------------------------------------------------------

        self.add_button("OK", gtk.RESPONSE_OK)
        self.add_button("Cancel", gtk.RESPONSE_CANCEL)
    
