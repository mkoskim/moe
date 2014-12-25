#!/usr/bin/env python
###############################################################################
#
# Basic View
#
###############################################################################

from config import conf
from helpers import *
from moeGTK import *

from moeItemGroup import GroupItem

from moeDocIndexView import DocIndexView

from moeDialogSnippet import SnippetDialog

###############################################################################
#
# Helper function moving trees between models
#
###############################################################################

def _copySnippet(to_model, to_path, from_model, from_path):

    def copyChilds(to_iter, from_iter):
        from_iter = from_model.iter_children(from_iter)
        while from_iter:
            item = from_model.get_value(from_iter, 0)
            child_iter = to_model.insert_before(to_iter, None, [item])
            copyChilds(child_iter, from_iter)
            from_iter = from_model.iter_next(from_iter)

    to_iter   = to_model.get_iter(to_path)
    from_iter = from_model.get_iter(from_path)

    item = from_model.get_value(from_iter, 0)
    to_iter = to_model.insert_after(None, to_iter, [item])
    
    copyChilds(to_iter, from_iter)
    return to_iter

###############################################################################
#
# View items in a notebook (using TreeView)
#
###############################################################################

class EditorViewIndex(gtk.HPaned):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def switchIn(self):
        self.set_position(int(conf.get_gui("IndexView", "index_width")))
        
    def switchOut(self):
        conf.set_gui("IndexView", "index_width", self.get_position())

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbToggleIncluded(self, cell, path, model):
        item = model[path][0]
        if item.alterable:
            item.included = not item.included
            model.cbModified(self)
            model.cbRenumRequest(self)
        else:
            cell.set_active(item.included)
            
    def cbCurrentChanged(self, widget, treeview, store):
        path, col = treeview.get_cursor()
        iter = store.get_iter(path)
        store.row_changed(path, iter)
        
    #--------------------------------------------------------------------------
    #
    # At right side, there is a hidden notebook, which has pages containing
    # item editing widgets. Whenever user chooses an item from index,
    # this kind of page is created.
    #
    #--------------------------------------------------------------------------

    def update_notebook(self):
        self.show_all()
        processGtkMessages()

    def _create_page(self, item):
        if item.name != None: item.name.connect(
            "changed", self.cbCurrentChanged, self.indexview, self.document
        )

        if not hasattr(item, "getContentEditor"): return gtk.Label()
        
        itembox = item.getContentEditor()
        grabber = itembox.grabber
        itembox = createFrame("_2 - Content", itembox)
        itembox.grabber = grabber
        return itembox
        
    def _create_view(self, item):
        item.view = self._create_page(item)
        self.notebook.append_page(item.view)
        self.update_notebook()
        
    def cbChangeItem(self, treeview, event = None):
        model = treeview.get_model()
        path, col = treeview.get_cursor()
        item = model[path][0]
        if not hasattr(item, "view") or item.view == None:
            self._create_view(item)
        newpage = self.notebook.page_num(item.view)
        self.notebook.set_current_page(newpage)
        if hasattr(item.view, "grabber"):
            self.grabber = item.view.grabber
            
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbDetach(self, widget, event = None):
        print "Detaching..."
        path, col = self.indexview.get_cursor()
        item = self.document[path][0]
        
        window = gtk.Window()
        window.set_title("moe: " + item.getName())
        allocation = self.notebook.get_allocation()
        width, height = allocation.width, allocation.height
        window.add(item.getContentEditor())
        window.resize(width, height)
        window.show_all()
    
    def cbFlatten(self, widget, event = None):
        print "Flattening..."
        model = self.document
        path, col = self.indexview.get_cursor()
        group = model.get_iter(path)
        current = group
        child = model.iter_first_child(group)
        while child:
            model.move_after(child, current)
            current = model.iter_next(current)
            child = model.iter_first_child(group)
        self.document.renum()
    
    def cbDeepen(self, widget, event = None):
        print "Deepening..."
        model = self.document
        path, col = self.indexview.get_cursor()
        item = model[path][0]
        
        if item.level == 0:
            group = GroupItem(model, level = 1, name = "<Unnamed>")
        elif item.level == 1:
            group = GroupItem(model, level = 2, name = "<Unnamed>")
        else:
            print "Cannot deepen"
            return
        
        group["synopsis"].set_content(item["synopsis"])
        
        current = model.get_iter(path)
        group = self.insert(group)
        model.drop_in(current, group)
        self.document.renum()
    
    def cbPopOut(self, widget, event = None):
        print "Popping out..."
        model = self.document
        path, col = self.indexview.get_cursor()
        item = model[path][0]

        current = model.get_iter(path)        
        parent = model.iter_parent(current)
        self.document.move_after(current, parent)        
        self.document.renum()
    
    def cbItem2File(self, widget, event = None):
        self.writeItem2File()

    def cbIndexPopup(self, widget, event):
        if event.button == 3:
            self.indexpopup.popup(None, None, None, event.button, event.time)
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbToggleWordsPercentages(self, widget):
        self.indexview.percentages = not self.indexview.percentages
        self.indexview.update()
    
    def cbExpandAll(self, widget):
        self.indexview.expand_all()
        
    def cbCollapseAll(self, widget):
        self.indexview.collapse_all()
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self, document, mode = None):
        super(EditorViewIndex,self).__init__()

        self.document = document
        self.persistent = True
        
        #----------------------------------------------------------------------
        # Create notebook
        #----------------------------------------------------------------------

        vbox = gtk.VBox()

        self.notebook  = gtk.Notebook()
        self.notebook.set_property("show-tabs", False)
        self.notebook.set_show_border(False)
        self.notebook.set_border_width(0)
        
        """notetools = ToolBar(
            ToolBar.Button(
                "Popout", self.cbPopOut,
                "Pop out current item"
            ),
            ToolBar.Button(
                "Deepen", self.cbDeepen,
                "Deepen current item"
            ),
            ToolBar.Button(
                "Flatten", self.cbFlatten,
                "Flatten current group"
            ),
            ToolBar.Separator(),
            ToolBar.Button(
                "Detach", self.cbDetach,
                "Detach item to own window"
            ),
            ToolBar.Separator(),
            ToolBar.Button(
                "To file", self.cbItem2File,
                "Write item to new file"
            ),
            ToolBar.Separator(),
        )
        vbox.pack_start(notetools, False, False)"""

        vbox.pack_start(ToolBar(ToolBar.Separator()), False, False)
        vbox.pack_start(self.notebook)
                
        self.pack2(vbox)
        
        #----------------------------------------------------------------------
        # Index popup menu
        #----------------------------------------------------------------------

        item_factory = gtk.ItemFactory(gtk.Menu, "<main>", None)
        item_factory.create_items(
            (
                ( "/Detach", None, self.cbDetach, 0, None ),
                ( "/s1", None, None, 0, "<Separator>" ),
                ( "/Flatten", None, self.cbFlatten, 0, None ),
                ( "/Deepen", None,  self.cbDeepen,  0, None ),
                ( "/Pop Out", None, self.cbPopOut,  0, None ),
                ( "/s2", None, None, 0, "<Separator>" ),
                ( "/Write to file", None, self.cbItem2File,  0, None ),
            )
        )
        self.indexpopup = item_factory.get_widget("<main>")

        #----------------------------------------------------------------------
        # Create index
        #----------------------------------------------------------------------

        self.indexview = DocIndexView(document)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.indexview)
        sw.grabber = self.indexview

        self.indexview.connect("cursor-changed", self.cbChangeItem)
        self.indexview.connect("button-press-event", self.cbIndexPopup)
        
        #----------------------------------------------------------------------
        # Create index columns
        #----------------------------------------------------------------------

        cell, col = self.indexview.newColumn(
            "#",
            gtk.CellRendererText(), self.indexview.dfColNumber
        )
        cell.set_property("xalign", 1.0)
        
        cell,col = self.indexview.newColumn(
            "",
            gtk.CellRendererToggle(), self.indexview.dfColIncluded
        )
        cell.set_property("activatable", True)
        cell.connect("toggled",
            self.cbToggleIncluded,
            self.indexview.get_model()
        )
        
        cell, col = self.indexview.newColumn(
            "Words",
            gtk.CellRendererText(), self.indexview.dfColWords
        )
        cell.set_property("xalign", 1.0)
        
        cell,col = self.indexview.newColumn(
            "Name",
            gtk.CellRendererText(), self.indexview.dfColSeparator
        )
        
        cell,col = self.indexview.addColumn(
            col,
            gtk.CellRendererText(), self.indexview.dfColName
        )
        
        #cell,col = self.indexview.newColumn(
        #    "Name",
        #    gtk.CellRendererText(), self.indexview.dfColName
        #)
        
        self.indexview.set_expander_column(col)
        
        frame = createFrame("_1 - Index", sw)

        #----------------------------------------------------------------------
        # Index tools
        #----------------------------------------------------------------------

        indextools = ToolBar(
            ToolBar.Button(
                "+", self.cbExpandAll,
                "Expand all"
            ),
            ToolBar.Button(
                "-", self.cbCollapseAll,
                "Collapse all"
            ),
            ToolBar.Separator(),
            ToolBar.CheckButton(
                "%", self.indexview.percentages, self.cbToggleWordsPercentages,
                "Show words/percentages"
            ),
            ToolBar.Separator(),
        )
        vbox = gtk.VBox()
        vbox.pack_start(indextools, False, False)
        vbox.pack_start(frame)
        
        self.pack1(vbox)

        #----------------------------------------------------------------------
        # Add items to view
        #----------------------------------------------------------------------

        self.indexview.set_cursor(1)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def selected_item(self):
        path, col = self.indexview.get_cursor()
        return self.document[path][0]

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def fontChanged(self):
    
        def useNewFont(model, path, iter):
            item = model.get_value(iter,0)
            if item.view.contentedit != None:
                item.view.contentedit.grabber.modify_font(conf.editfont)
            
        self.document.foreach(useNewFont)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def delete_current(self):
        treeview = self.indexview
        path, col = treeview.get_cursor()
        model = treeview.get_model()

        if path == None: return
        
        iter = model.get_iter(path)
        item = model.get_value(iter, 0)

        if not item.removable: return

        trash_iter = self.document.find(self.document.trashcan)
        parent = model.iter_parent(iter)
        
        # NOTE: Page still exists in trashcan!
        #pagenum = self.notebook.page_num(item.view)
        #self.notebook.remove_page(pagenum)
        #self.update_notebook()
        
        if model.drop_in(iter, trash_iter):
            treeview.set_cursor(model.get_path(iter))
        else:
            treeview.set_cursor(model.get_path(parent))
        self.document.renum()

    def split_current(self):
        treeview = self.indexview
        path, col = treeview.get_cursor()
        model = treeview.get_model()

        if path == None: return
        
        iter = model.get_iter(path)
        
        current = model.get_value(iter, 0)
        if not current.view.grabber.get_property("has-focus"):
            return

        splitted = current.split()
        if splitted != None:
            self.insert(splitted)
            splitted.view.grabber.grab_focus()
            self.document.renum()

    def merge_current(self):
        treeview = self.indexview
        path, col = treeview.get_cursor()
        model = treeview.get_model()

        if path == None: return
        
        cur_iter = model.get_iter(path)
        next_iter = model.iter_next(cur_iter)
        if next_iter == None: return
        
        current = model.get_value(cur_iter, 0)
        next = model.get_value(next_iter, 0)
        
        if current.merge(next):
            model.remove(next_iter)
            if hasattr(next, "view"):
                pagenum = self.notebook.page_num(next.view)
                self.notebook.remove_page(pagenum)
            #self.update_notebook()
            self.document.renum()

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def insert(self, item):
        treeview = self.indexview
        path, col = treeview.get_cursor()
        model = treeview.get_model()

        if path == None:
            iter = self.document.find(self.document.trashcan)
        else:
            iter = model.get_iter(path)
            parent = model.iter_parent(iter)
            if item.alterable and parent != None:
                parent = model.get_value(parent, 0)
                item.included = parent.included

        if model.get_value(iter,0).keep_last:
            iter = model.insert_before(None,iter,[item])
        else:
            iter = model.insert_after(None,iter,[item])

        self.document.renum()
        treeview.set_cursor(model.get_path(iter))
        return iter
        
    #--------------------------------------------------------------------------
    # Pick a tree from another MOE file
    #--------------------------------------------------------------------------

    def pickSnippets(self, filename = None):

        if not filename:
            filename = userLoadFile(
                "File to pick",
                patterns = [
                    [ "MOE Files (.moe)", ["*.moe"]],
                ]
            )
            if not filename: return

        dialog = SnippetDialog(filename)
        dialog.show_all()
    
        if dialog.run() == gtk.RESPONSE_OK:
            path, col = dialog.treeview.get_cursor()
            iter = _copySnippet(
                self.document, self.indexview.get_cursor()[0],
                dialog.snippets, path
            )
            self.document.renum()
            self.indexview.set_cursor(self.document.get_path(iter))
            
        dialog.destroy()

    def writeItem2File(self):
        from_model = self.document
        from_path, col = self.indexview.get_cursor()

        item = from_model[from_path][0]
        suggest = item.name.get_content()

        filename = userSaveFile("Save snippet to",
            suggestion = suggest + ".moe", 
            patterns = [ 
                ["MOE Files (.moe)", ["*.moe"]],
                ["All files", ["*.*"]]
            ]
        )
        if not filename: return

        import moeDocument
        import moeItemTitle

        to_model = moeDocument.Document(None)
        to_model.title = moeItemTitle.TitleItem(to_model)
        to_model.append(None, [to_model.title])

        to_model.title["author"]   = from_model.title["author"]
        to_model.title["website"]  = from_model.title["website"]

        to_model.title["title"]    = item["name"]
        to_model.title["synopsis"] = item["description"]
        
        print from_path
        
        _copySnippet(
            to_model, (0, ),
            from_model, from_path
        )

        to_model.save(filename)
        execMoe(filename)        

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

