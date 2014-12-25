###############################################################################
#
# Viewing document as hierarchy
#
###############################################################################

from config import conf
from helpers import *
from moeGTK import *

###############################################################################
#
# 
#
###############################################################################

class EditorViewSynopses(gtk.Notebook):

    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------
    
    def __init__(self, document, mode = None):
        super(EditorViewSynopses,self).__init__()

        self.document = document
        if document == None: return
        
        self.set_show_tabs(False)
        self.set_show_border(False)
        
        self._createPage(None)

    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------

    def cbForward(self, widget, event):
        #print "Forward", widget.iter, widget.page
        if widget.page == None:
            widget.page = self._createPage(widget.iter)
        self.set_current_page(widget.page)
        
    def cbBack(self, widget, event):
        #print "Back"
        self.set_current_page(widget.page)
        
    def cbEdit(self, widget, event):
        item = widget.item

        if widget.page == None:
            widget.page = self._createEditPage(widget.item)
        self.set_current_page(widget.page)
    
    #--------------------------------------------------------------------------

    def _createBackButton(self, backpage):
        backbtn = gtk.Button("<- Back")
        backbtn.page = backpage
        backbtn.connect("button-press-event", self.cbBack)
        return backbtn
        
    def _createForwardButton(self, iter):
        forwardbtn = gtk.Button("View ->")
        forwardbtn.iter = iter
        forwardbtn.page = None
        forwardbtn.connect("button-press-event", self.cbForward) 
        return forwardbtn

    def _createEditButton(self, item):
        editbtn = gtk.Button("Edit ->")
        editbtn.item = item
        editbtn.page = None
        editbtn.connect("button-press-event", self.cbEdit) 
        return editbtn
        
    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------
    
    def _createLeftBoxTitle(self):
        document = self.document
        tmpbox = gtk.VBox()
        titleedit    = createEntry(document.title["title"])
        subtitleedit = createEntry(document.title["subtitle"])
        descedit     = createScrolledTextBox(
            document.title["synopsis"],
            pad_leftright = 10,
            pad_topbottom = 10)

        basicbox = createEditGrid(
            None,
            [
                [ "Title", titleedit ],
                [ "Subtitle", subtitleedit ],
            ],
            False, False
        )

        descbox = createFrame(
            "Synopsis",
            descedit,
            border_width = 0,
        )
        
        tmpbox.pack_start(basicbox, False, False, 0)
        tmpbox.pack_start(gtk.HSeparator(), False, False, 5)
        tmpbox.pack_start(descbox, True, True, 0)
        tmpbox.grabber = titleedit.grabber
        return tmpbox        
        
    #--------------------------------------------------------------------------

    def _createLeftBoxOther(self, item, backpage):
        tmpbox = gtk.VBox()
        
        nameedit = createEntry(item.elements["name"])
        backbtn  = self._createBackButton(backpage)
        
        namebox = gtk.HBox()
        namebox.pack_start(backbtn, False, False, 0)
        namebox.pack_start(nameedit)
        
        descbox = createFrame(
            "Synopsis",
            createScrolledTextBox(item["synopsis"],
                pad_leftright = 10,
                pad_topbottom = 10,
            ),
            border_width = 0,
        )
        
        commentbox = createFrame(
            "Comments",
            createEntry(item["comments"],
                pad_leftright = 10,
                pad_topbottom = 10,
            ),
            border_width = 0,
        )
        
        tmpbox.pack_start(namebox, False, False, 0)
        tmpbox.pack_start(gtk.HSeparator(), False, False, 10)
        tmpbox.pack_start(descbox, True, True, 0)
        tmpbox.pack_start(commentbox, False, False, 0)
        tmpbox.grabber = nameedit.grabber
        
        return tmpbox

    #--------------------------------------------------------------------------

    def _createRightBox(self, iter, count, item):
        
        nameedit = createEntry(item["name"])
        
        if self.document.iter_children(iter) != None:
            forwardbtn = self._createForwardButton(iter)
        else:
            forwardbtn = self._createEditButton(item)
        
        namebox = gtk.HBox()
        namebox.pack_start(nameedit)
        namebox.pack_start(forwardbtn, False, False, 0)        

        descbox = createEntry(item["synopsis"],
            pad_leftright = 40,
            pad_topbottom = 10
        )

        tmpbox = gtk.VBox()
        tmpbox.pack_start(namebox, False, False, 0)
        tmpbox.pack_start(descbox, False, False, 0)
        tmpbox.grabber = nameedit.grabber
            
        tmpbox = createFrame(
            "%s" % count,
            tmpbox
        )
        return tmpbox
        
    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------

    def _createLeftBoxEdit(self, item, backpage):
        tmpbox = gtk.VBox()

        nameedit = createEntry(item["name"])
        backbtn  = self._createBackButton(backpage)
        
        namebox = gtk.HBox()
        namebox.pack_start(backbtn, False, False, 0)
        namebox.pack_start(nameedit)
        
        descbox = createFrame(
            "Synopsis",
            createEntry(
                item["synopsis"],
                pad_leftright = 10,
                pad_topbottom = 10,
            ),
            border_width = 0,
        )
        
        sketchbox = createFrame(
            "Comments",
            createEntry(item["comments"],
                pad_leftright = 10,
                pad_topbottom = 10,
            ),
            border_width = 0,
        )
        
        tmpbox.pack_start(namebox, False, False, 0)
        tmpbox.pack_start(gtk.HSeparator(), False, False, 10)
        tmpbox.pack_start(descbox, False, False, 0)
        tmpbox.pack_start(sketchbox, False, False, 5)
        tmpbox.grabber = nameedit.grabber
        
        return tmpbox

    
    #--------------------------------------------------------------------------

    def _createRightBoxEdit(self, item):
        return createScrolledTextBox(
            item.elements["content"],
            pad_leftright = 40,
            pad_topbottom = 20
        )

    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------

    def _createEditPage(self, item):
        view = gtk.HBox()

        leftside = self._createLeftBoxEdit(item, self.get_current_page())
        rightside = self._createRightBoxEdit(item)

        leftside.set_size_request(
            int(conf.get_gui("IndexView", "index_width")),
            -1
        )

        view.pack_start(leftside, False, False, 0)
        view.pack_start(rightside, True, True, 0)

        pageno = self.append_page(view)
        view.show_all()
        return pageno
        
    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------

    def _createPage(self, iter):
    
        view = gtk.HBox()
        document = self.document
        
        #----------------------------------------------------------------------
        # Left side: Upper level description
        #----------------------------------------------------------------------
        
        if iter == None:
            leftbox = self._createLeftBoxTitle()
            iter = document.get_iter_root()
        else:
            leftbox = self._createLeftBoxOther(
                document.get_value(iter,0),
                self.get_current_page()
            )
            iter = document.iter_children(iter)
            
        leftbox = createFrame("Main", leftbox)
        leftbox.set_size_request(
            int(conf.get_gui("IndexView", "index_width")),
            -1
        )
        
        #----------------------------------------------------------------------
        # Right side: Lower level descriptions
        #----------------------------------------------------------------------

        rightbox = gtk.VBox()
        
        count = 1
        while iter:
            item = document.get_value(iter, 0)
            if item.included and item.__class__.__name__ != "TitleItem":
                tmpbox = self._createRightBox(iter, count, item)
                rightbox.pack_start(tmpbox, False, False, 1)
                count += 1
            iter = document.iter_next(iter)
            
        #----------------------------------------------------------------------
        # Pack together
        #----------------------------------------------------------------------
        
        sw = gtk.ScrolledWindow()
        sw.add_with_viewport(rightbox)
         
        self.leftside = leftbox
        self.rightside = sw

        view.pack_start(self.leftside, False, False, 0)
        view.pack_start(self.rightside, True, True, 0)

        pageno = self.append_page(view)
        view.show_all()
        return pageno
        
