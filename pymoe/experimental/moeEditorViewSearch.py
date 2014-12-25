from config import conf
from helpers import *
from moeGTK import *

###############################################################################
#
# Spellchecker
#
###############################################################################

try:
    import libvoikko
    lang = libvoikko.Voikko("fi")
    lang.setNoUglyHyphenation(True)

    INFO("Voikko loaded.")
except ImportError:
    lang = None
    INFO("No hyphenation.")

###############################################################################
#
# Index View for Search Items
#
###############################################################################

class SearchItemIndexView(gtk.TreeView):

    def __init__(self, model):
        super(SearchItemIndexView,self).__init__()
        self.set_model(model)
        self.set_rules_hint(True)

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
    # Callbacks to get column information
    #--------------------------------------------------------------------------

    def dfColName(self, tvcol, cell, model, iter):
        item = model.get_value(iter, 0)
        path = model.get_path(iter)
        text = "        " * item.depth() + item.item.getName()
        cell.set_property("text", text)

    #--------------------------------------------------------------------------

###############################################################################
#
# Index View for Words
#
###############################################################################

class WordIndexView(gtk.TreeView):

    def __init__(self, model):
        super(WordIndexView,self).__init__()
        self.set_model(model)
        self.set_rules_hint(True)

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
    # Callbacks to get column information
    #--------------------------------------------------------------------------

    def dfColName(self, tvcol, cell, model, iter):
        item = model.get_value(iter, 0)
        #path = model.get_path(iter)
        #text = "        " * item.depth() + item.item.getName()
        cell.set_property("text", item)

    #--------------------------------------------------------------------------



###############################################################################
#
# Editor View for Searching
#
###############################################################################

class EditorViewSearch(gtk.HBox):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    words = gtk.ListStore(str)

    def cutBuf(self, textbuf):
        e = textbuf.get_start_iter()
        last_s = None
        while not e.is_end():
            e.forward_word_end()
            #if e.starts_word(): continue
            s = e.copy()
            s.backward_word_start()
            if last_s != None and s.equal(last_s): continue
            last_s = s.copy()
            text = s.get_text(e)
            if text in self.words:
                self.words[text] += 1
            else:
                self.words[text] = 1

    def cutWords(self):
        iter = self.items.get_iter_root()
        while iter:
            item = self.items.get_value(iter,0)
            if item.elements != None:
                for elem in item.elements:
                    self.cutBuf(elem[1])
            iter = self.items.iter_next(iter)
            
        #for word in self.words:
        #    print word, self.words[word]

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    class SearchItem:
    
        def __init__(self, model, iter, filtering = None):
            self.model = model
            self.iter = iter
            self.item = model.get_value(iter, 0)
            if filtering == "official":
                fields = self.item.officialfields
            else:
                fields = self.item.searchfields
            
            if fields != None:
                self.elements = []
                for elem in fields:
                    self.elements.append([elem, self.item.elements[elem]])
            else:
                self.elements = None
            
        def path(self):
            return self.model.get_path(self.iter)
        
        def depth(self):
            return len(self.path()) - 1
        
        def namelist(self):
            path = self.path()
            text = []
            for i in range(len(path)):
                parent = self.model[path[:i+1]][0]
                text.append(parent.getName())
            return text

        def visiblename(self, elemindex):
            return self.item.visiblenames[self.elements[elemindex][0]]

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    items = gtk.ListStore(object)

    def fillItems(self, widget = None, event = None):
    
        document = self.document
        self.items.clear()
        
        def fill(iter = None):
            if iter != None:
                item = self.document.get_value(iter, 0)
                if self.itemfilter.get_content() != "all" and\
                    not item.included:
                    return
                self.items.append([self.SearchItem(
                    document,
                    iter,
                    self.itemfilter.get_content()
                )])
                iter = document.iter_children(iter)
            else:
                iter = document.get_iter_root()

            while iter:
                fill(iter)
                iter = document.iter_next(iter)
    
        fill()
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def changeElement(self, item, elemindex = None):
        if item.elements == None:
            item.textbuf = None
            #self.contentedit.grabber.set_buffer(None)
            return
        if elemindex != None: item.elemindex = elemindex
        item.textbuf = item.elements[item.elemindex][1]
        item.textbuf.place_cursor(item.textbuf.get_start_iter())
    
    def cbChangeItem(self, treeview, event = None):
        model = treeview.get_model()
        path, col = treeview.get_cursor()
        item = model[path][0]

        self.changeElement(item, 0)
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def replace(self):
        textbuf = self.contentedit.grabber.get_buffer()
        if textbuf.delete_selection(True, True):
            textbuf.insert_at_cursor(
                self.replacewith.grabber.get_buffer().get_content()
            )

    def searchNextRegular(self):
        return None
        needle = self.searchfor.grabber.get_buffer().get_content()

        treeview = self.itemindex
        model = treeview.get_model()
        path, col = treeview.get_cursor()
        iter = model.get_iter(path)

        while iter:
            item = model.get_value(iter, 0)
            
            if item.textbuf == None:
                result = None
            else:
                if item.textbuf.get_has_selection():
                    result = item.textbuf.get_selection_bounds()[1]
                else:
                    result = item.textbuf.get_iter_at_mark(item.textbuf.get_insert())
                result = result.forward_search(needle, 0)
                
            if result == None:
                if item.elements != None:
                    item.elemindex += 1
                    if item.elemindex < len(item.elements):
                        self.changeElement(item)
                        continue
                iter = model.iter_next(iter)
                if iter:
                   treeview.set_cursor(model.get_path(iter)[0])
                continue
            s, e = result
            item.textbuf.select_range(s, e)
            self.contentedit.grabber.scroll_to_iter(s, 0.1, True, 0.5, 0.5)
            break
            
        self.contentedit.grabber.grab_focus()

    def _searchNextWord(self):
        treeview = self.itemindex
        model = treeview.get_model()
        path, col = treeview.get_cursor()
        iter = model.get_iter(path)

        while iter:
            item = model.get_value(iter, 0)
            
            if item.textbuf == None:
                e = None
            else:
                if item.textbuf.get_has_selection():
                    e = item.textbuf.get_selection_bounds()[1]
                else:
                    e = item.textbuf.get_iter_at_mark(item.textbuf.get_insert())
                if not e.is_end():
                    e.forward_word_end()
                    if not e.ends_word(): e = None
                else:
                    e = None
                #if not e.ends_word(): continue
                
            if e == None:
                if item.elements != None:
                    item.elemindex += 1
                    if item.elemindex < len(item.elements):
                        self.changeElement(item)
                        continue
                iter = model.iter_next(iter)
                if iter:
                   treeview.set_cursor(model.get_path(iter)[0])
                continue
            
            s = e.copy()
            s.backward_word_start()
            return s, e            
        return None
        
    def searchNextSpellcheck(self):
        return None
        while True:
            result = self._searchNextWord()
            if result == None:
                return None
            s, e = result

            treeview = self.itemindex
            model = treeview.get_model()
            path, col = treeview.get_cursor()
            iter = model.get_iter(path)
            item = model.get_value(iter, 0)

            word = unicode(item.textbuf.get_text(s,e), "utf-8")
            item.textbuf.place_cursor(e)
                            
            if not lang.spell(word): break
            processGtkMessages()
        item.textbuf.select_range(s, e)

        while self.fieldlabel.get_n_pages():
            self.fieldlabel.remove_page(0)
        if item.elements != None:
            for index in range(len(item.elements)):
                self.fieldlabel.append_page(
                    gtk.VBox(),
                    gtk.Label(item.visiblename(index))
                )
        self.fieldlabel.show_all()
        self.fieldlabel.set_current_page(item.elemindex)
        self.contentedit.grabber.set_buffer(item.textbuf)
        self.contentedit.grabber.scroll_to_iter(s, 0.1, True, 0.5, 0.5)
        self.contentedit.grabber.grab_focus()

        #self.fieldlabel.disconnect(self.fieldlabel.sigSwitch)        
        
        #self.fieldlabel.sigSwitch = self.fieldlabel.connect("switch-page", self.cbFieldChanged)
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def editBoxKeyPressed(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if event.state & gtk.gdk.CONTROL_MASK:
            if keyname == "g" or keyname == "f":
                #self.searchNext()
                return True
            elif keyname == "r":
                #self.replace()
                #self.searchNext()
                return True
        return False

    def searchBoxKeyPressed(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname == "Return":
            #self.searchNext()
            return True
        #print keyname #event.state, event.keyval #dir(event)
        return False

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    #def hotKeys(self):
    # 
    #    hotkeys = (
    #        ( "<control>G", self.searchNext ),
            #( "<control>Page_Up", self.prevItem ),
            #( "<control>Page_Down", self.nextItem ),
            #( "<alt>I", self.focusList ),
            #( "<alt>C", self.focusContent ),
            #( "<alt>H", self.focusDescription ),
    #    )
    #
    #    for hotkey in hotkeys:
    #        keyval, mod = gtk.accelerator_parse(hotkey[0])
    #        self.add_accelerator(
                
            #accel_group.connect_group(
            #    keyval, mod, 0, hotkey[1]
            #)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbRestart(self, widget, pageref, page):
        print widget, page
        self.mode = ["find", "assisted", "spellcheck"][page]
        if page == 0:
            self.searchNext = self.searchNextRegular
        elif page == 2:
            self.searchNext = self.searchNextSpellcheck
            self.searchNext()
        else:
            self.searchNext = None
        
    def cbInitNotebook(self, widget, event = None):
        print "init nb"
        widget.disconnect(widget.sigExpose)
        widget.connect("switch-page", self.cbRestart)

        page = {"find": 0, "assisted": 1, "spellcheck": 2}[self.mode]
        
        if page == widget.get_current_page():
            self.cbRestart(widget, None, page)
        else:
            widget.set_current_page(page)
        return False
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbFieldChanged(self, widget, pageref, page):
        treeview = self.itemindex
        model = treeview.get_model()
        path, col = treeview.get_cursor()
        item = model[path][0]
        if not hasattr(item, "elemindex") or item.elemindex != page:
            self.changeElement(item, page)
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    opt_items = [
        [ "all",      "All" ],
        [ "included", "Included only" ],
        [ "official", "Official only" ],
    ]

    def refill(self, widget = None):
        print "Refill", self.mode
        self.fillItems()
        self.itemindex.set_cursor(0)
        page = {"find": 0, "assisted": 1, "spellcheck": 2}[self.mode]
        #self.cbRestart(None, None, page)
        
    #def switchIn(self):
    #    print "Switch in"
    #    #self.refill()

    #def switchOut(self):
    #    print "Switch out", self.mode

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self, document, mode = "find"):
        super(EditorViewSearch,self).__init__()

        print "__init__"
        self.document = document
        self.mode = mode
        self.persistent = True
        
        #----------------------------------------------------------------------
        #----------------------------------------------------------------------

        #self.cutWords()
        
        self.itemfilter  = TextCombo(self.opt_items)
        self.itemfilter.connect("changed", self.refill)

        #self.fillItems()

        #----------------------------------------------------------------------
        # Normal search & replace
        #----------------------------------------------------------------------

        self.searchfor   = createEntry(TextBuf())
        self.replacewith = createEntry(TextBuf())
        
        findedit = createEditGrid(
            None,
            [
                [ "Search for",   self.searchfor ],
                [ "Replace with", self.replacewith ]
            ],
            False, False
        )
        
        findbox = gtk.VBox()
        findbox.pack_start(findedit, False, False)

        #----------------------------------------------------------------------
        # Assisted search & replace
        #----------------------------------------------------------------------

        #assistededit = createEditGrid(
        #    None,
        #    [
        #        #[ "Find from",    self.itemfilter ],
        #    ],
        #    False, False
        #)
        #assistedbox = gtk.VBox()
        #assistedbox.pack_start(assistededit, False, False)
        
        #----------------------------------------------------------------------
        # Spellcheck
        #----------------------------------------------------------------------

        #----------------------------------------------------------------------
        # Notebook for selecting search&replace operation
        #----------------------------------------------------------------------

        searchnb = gtk.Notebook()
        searchnb.append_page(findbox, gtk.Label("Find"))
        searchnb.append_page(gtk.Label("Assisted"), gtk.Label("Assisted"))
        if lang != None:
            searchnb.append_page(gtk.Label("Spellcheck"), gtk.Label("Spellcheck"))
        #searchnb.connect("switch-page", self.cbRestart)
        searchnb.show()
        #searchnb.sigExpose = searchnb.connect("expose-event", self.cbInitNotebook)
           
        searchbox = gtk.VBox()
        searchbox.pack_start(createEditGrid
            (
                None,
                [
                    [ "Find from",    self.itemfilter ],
                ],
                False, False
            ), False, False
        )
        searchbox.pack_start(searchnb)
        searchbox.set_size_request(
            int(conf.get_gui("IndexView", "index_width")),
            -1
        )
        
        #----------------------------------------------------------------------
        
        self.fieldlabel = gtk.Notebook()
        self.fieldlabel.set_show_tabs(True)
        self.fieldlabel.set_show_border(False)
        self.fieldlabel.set_tab_pos(gtk.POS_BOTTOM)
        self.fieldlabel.set_scrollable(True)
        #self.fieldlabel.sigSwitch = self.fieldlabel.connect("switch-page", self.cbFieldChanged)
        
        self.contentedit = createScrolledTextBox(
            None,
            pad_leftright = 40,
            pad_topbottom = 20
        )

        #----------------------------------------------------------------------

        self.itemindex = SearchItemIndexView(self.items)
        self.itemindex.set_size_request(-1, 250)
        self.itemindex.connect("cursor-changed", self.cbChangeItem)
        self.itemindex.set_cursor(0)

        #----------------------------------------------------------------------
        # Create index columns
        #----------------------------------------------------------------------

        cell, col = self.itemindex.newColumn(
            "Name",
            gtk.CellRendererText(), self.itemindex.dfColName
        )

        indexsw = gtk.ScrolledWindow()
        indexsw.add(self.itemindex)
        indexsw.grabber = self.itemindex
        indexsw = createFrame("Index", indexsw)
        
        #----------------------------------------------------------------------

        #----------------------------------------------------------------------
        
        showbox = gtk.VBox()
        
        showbox.pack_start(self.contentedit)
        showbox.pack_start(self.fieldlabel, False, False)
        #showbox.pack_start(gtk.HSeparator(), False, False)
        showbox.pack_start(indexsw, False, False)

        editbox = gtk.HBox()
        #editbox.pack_start(self.fieldlabel, False, False)
        editbox.pack_start(showbox)
        #self.editbox.grabber = self.contentedit.grabber
        #self.editbox = createFrame("Content", self.editbox)
        
        self.pack_start(searchbox, False, False, 5)
        self.pack_start(editbox, 5)
        self.show_all()
        
        #self.connect("key-press-event", self.viewKeyPressed)
        self.searchfor.grabber.connect("key-press-event", self.searchBoxKeyPressed)
        self.replacewith.grabber.connect("key-press-event", self.searchBoxKeyPressed)
        self.contentedit.grabber.connect("key-press-event", self.editBoxKeyPressed)
        
        self.grabber = self.searchfor.grabber

