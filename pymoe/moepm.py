#!/usr/bin/env python
# -*- coding=utf-8 -*-
###############################################################################
#
# MOE Project Manager: go through the directory hierarchy and extract
# project information.
#
###############################################################################

from config import conf
from helpers import *
from moeGTK import *

from moeXML import *

import sys
import os
import subprocess
import time

###############################################################################
#
# Collections of values of different fields, for filtering rows.
#
###############################################################################

years    = set(["-"])
statuses = set(["-"])
editors  = set(["-"])
doctypes = set(["-"])

def resetSets():
    global years, statuses, editors, doctypes
    years    = set(["-"])
    statuses = set(["-"])
    editors  = set(["-"])
    doctypes = set(["-"])

###############################################################################
#
# Project class for keeping information
#
###############################################################################

class Project(object):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self,
        editor, doctype, title, subtitle, year, status, deadline, words
    ):
        self.editor = editor
        self.doctype = doctype
        self.title = title
        self.subtitle = subtitle
        self.words = words
        
        self.year = year
        self.status = status
        self.deadline = deadline
        
        global years, statuses, editors, doctypes
        if editor != None: editors.add(editor)
        if year != None: years.add(year)
        if status != None: statuses.add(status)
        if doctype != None: doctypes.add(doctype)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cmpDoctypes(self, a):
        doctypes = {
            "shortstory": 0,
            "novel":      0,
            "longstory":  0,
            "research":   1,
            "collection": 2,
            "-":          3,
        }
        
        docindex1 = doctypes[self.doctype]
        docindex2 = doctypes[a.doctype]
        return cmp(docindex2, docindex1)
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __cmp__(self, a):
        if a == None: return 1
        if cmp(self.status, a.status) != 0:
            return cmp(string.lower(self.status), string.lower(a.status))
        if cmp(self.deadline, a.deadline) != 0:
            if self.deadline == "-": return -1
            if a.deadline == "-": return 1
            return cmp(a.deadline, self.deadline)
        if self.cmpDoctypes(a) != 0:
            return self.cmpDoctypes(a)
        return cmp(self.year, a.year)

###############################################################################
#
# Extracting info from moe projects
#
###############################################################################

def extractMoeProject(filename):
    def text(elem, field):
        elem = elem.find(field)
        if elem != None and elem.text != None:
            return elem.text
        else:
            return "-"

    try:
        tree = ET.ElementTree(ET.fromstring(readfile(filename)))
    except (SyntaxError, ExpatError):
        return None

    elem = tree.find("TitleItem")
    return Project(
        "moe",
        elem.get("type"),
        text(elem, "title"),
        text(elem, "subtitle"),
        text(elem, "year"),
        text(elem, "status"),
        text(elem, "deadline"),
        elem.get("words")
    )
   
###############################################################################
#
# Extracting info from old-style directory
#
###############################################################################

tagMainFile = re.compile(r"^MAINFILE=(?P<filename>.*?)$", re.MULTILINE|re.UNICODE)
tagDocName  = re.compile(r"^DOCNAME=(?P<filename>.*?)$", re.MULTILINE|re.UNICODE)
tagTEXcomment = re.compile("\%(.*?)$", re.MULTILINE|re.UNICODE)

tagTEXExtractHeader = re.compile(
        r"\\(?P<type>shortstory|longstory|novel|collection)" +
        r"\s*\{(?P<title>.*?)\}" +
        r"\s*\{(?P<subtitle>.*?)\}" +
        r"\s*\{(?P<status>.*?)\}" +
        r"\s*\{(?P<author>.*?)\}" +
        r"\s*\{(?P<website>.*?)\}" +
        r"\s*\{(?P<year>.*?)\}", re.MULTILINE|re.DOTALL|re.UNICODE
)

tagTEXExtractResearchHeader = re.compile(
        r"\\(?P<type>research)" +
        r"\s*\{(?P<imag_authors>.*?)\}" +
        r"\s*\{(?P<title>.*?)\}" +
        r"\s*\{(?P<subtitle>.*?)\}" +
        r"\s*\{(?P<imag_published>.*?)\}" +
        r"\s*\{(?P<status>.*?)\}" +
        r"\s*\{(?P<author>.*?)\}" +
        r"\s*\{(?P<website>.*?)\}" +
        r"\s*\{(?P<year>.*?)\}", re.MULTILINE|re.DOTALL|re.UNICODE
)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def extractStats(dirname):
    statfile = os.path.join(dirname,".statistics")
    if os.path.exists(statfile):
        exec(readfile(statfile))
        return wc
    else:
        return "-"

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def extractLatexProject(dirname):

    def getMainFile(makefile):
        content = readfile(makefile)
        mainfile = tagMainFile.search(content)
        if mainfile == None:
            mainfile = tagDocName.search(content)
            if mainfile != None:
                mainfile = mainfile.group("filename") + ".tex"
        else:
            mainfile = mainfile.group("filename")
        return mainfile
    
    mainfile = getMainFile(os.path.join(dirname, "Makefile"))
    mainfile = os.path.join(dirname, mainfile)

    if os.path.splitext(mainfile) == ".moe":
        return mainfile, extractMoeProject(mainfile)
    
    try:
        content = readfile(mainfile)
    except IOError:
        return dirname, None
    
    content = tagTEXcomment.sub("", content)
    docinfo = tagTEXExtractHeader.search(content)
    
    if docinfo == None:
        docinfo = tagTEXExtractResearchHeader.search(content)
        if docinfo == None:
            return mainfile, None
    
    wc = extractStats(dirname)
        
    year = docinfo.group("year")
    if year == "": year = "-"
    
    return mainfile, Project(
        "LaTeX",
        docinfo.group("type"),
        docinfo.group("title"),
        docinfo.group("subtitle"),
        year,
        docinfo.group("status"),
        "-",
        wc
    )
    
###############################################################################
#
# Dialog for showing directory scan progress
#
###############################################################################

class DirScanDialog(gtk.Dialog):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self):
        super(DirScanDialog,self).__init__(
            "Scanning...",
            None,
            gtk.DIALOG_MODAL,
            ()
        )
        self.set_has_separator(False)
        self.proclabel = gtk.Label("Projects found: 0")
        self.proclabel.set_size_request(250, 75)
        self.vbox.pack_start(self.proclabel)
        self.count = 0
        self.last_update = time.time()
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def start(self):
        self.show_all()
        self.queue_draw()
        processGtkMessages()

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def pulse(self):
        self.count += 1
        if time.time() - self.last_update > 0.25:
            self.proclabel.set_text("Projects found: %d" % self.count)
            processGtkMessages()
            self.last_update = time.time()
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def stop(self):
        self.destroy()        

###############################################################################
#
# GTK ListStore containing projects
#
###############################################################################

class ProjectStore(gtk.ListStore):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self):
        super(ProjectStore,self).__init__(str, object)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def _storeProject(self, directory, project):
        self.append([directory, project])
        self.dialog.pulse()
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def _populate(self, dirname):
        files = os.listdir(dirname)
        
        prune = [
            "defaults", "moe",          # Exclude source directories
            "versions", "version",      # Exclude version directories
            ".moerc",                   # Exclude MOE settings
        ]

        files = filter(lambda f: f not in prune, files)

        def fullname(f): return os.path.join(dirname, f)
        
        #----------------------------------------------------------------------
        # Do not follow symbolic links
        #----------------------------------------------------------------------

        files = filter(lambda f: not os.path.islink(fullname(f)), files)
        
        #----------------------------------------------------------------------
        # Does this directory contain any .moe files? If so, extract
        # projects and do NOT go any deeper.
        #----------------------------------------------------------------------

        moefiles = filter(
            lambda f: os.path.splitext(f)[1] == ".moe", files
        )
        if len(moefiles):
            for f in moefiles:
                project = extractMoeProject(fullname(f))
                self._storeProject(fullname(f), project)
            return
            
        #----------------------------------------------------------------------
        # Does this directory contain Makefile? If so, extract
        # project and continue deeper.
        #----------------------------------------------------------------------

        if "Makefile" in files:
            mainfile, project = extractLatexProject(dirname)
            self._storeProject(mainfile, project)

        files = filter(lambda f: os.path.isdir(fullname(f)), files)
        
        for f in files: self._populate(fullname(f))

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def populate(self, dirname):
        self.dialog = DirScanDialog()
        self.dialog.start()        
        self._populate(dirname)
        self.dialog.stop()
        
###############################################################################
#
# Filtering options
#
###############################################################################

class FilterBox(gtk.Frame):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbToggled(self, widget, value):
        if widget.get_active():
            self.filterset.add(value)
        else:
            self.filterset.remove(value)
        self.model.refilter()

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbComboChanged(self, widget):
        index = widget.get_active()
        text = self.lookup[index]
        for checkbox in self.checkboxes:
            if index > 0 and checkbox[0] != text:
                checkbox[1].set_active(False)
            else:
                checkbox[1].set_active(True)
        self.model.refilter()
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self, model, name, values):
        super(FilterBox,self).__init__(name)

        self.set_property("border-width", 5)
        self.filterset = set()
        self.model = model
        self.checkboxes = []
        
        hbox = gtk.HBox(spacing = 20)
        
        vbox = gtk.VBox()
        rows = 0
        
        for value in sorted(values):
            self.filterset.add(value)
            cb = gtk.CheckButton(value)
            self.checkboxes.append([value, cb])
            cb.set_active(True)
            cb.connect("toggled", self.cbToggled, value)
            rows += 1
            if rows > 4:
                hbox.pack_start(vbox, False, False)
                vbox = gtk.VBox()
                rows = 1
            vbox.pack_start(cb, False, False)
        hbox.pack_start(vbox, False, False)
        
        vbox = gtk.VBox()
        
        self.lookup = []
        self.combo = gtk.combo_box_new_text()
        for value in ["All"] + list(values):
            self.lookup.append(value)
            self.combo.append_text(value)
        self.combo.set_active(0)
        self.combo.connect("changed", self.cbComboChanged)

        vbox.pack_start(self.combo, False, True)
        vbox.pack_start(hbox, False, False)
        vbox.set_property("border-width", 5)
        self.add(vbox)
        
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class FilterView(gtk.Frame):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbVisible(self, item):
        if item == None:
            year = "-"
            status = "-"
            editor = "-"
            doctype = "-"
        else:
            year = item.year
            status = item.status
            editor = item.editor
            doctype = item.doctype
            
        if year not in self.year_filter.filterset:
            return False
        if status not in self.status_filter.filterset:
            return False
        if doctype not in self.doctype_filter.filterset:
            return False
        return editor in self.editor_filter.filterset
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self, model):
        super(FilterView,self).__init__("Filter Options")

        self.set_property("border-width", 0)
        #self.set_expanded(True)
         
        self.editor_filter = FilterBox(model, "Editors",  editors)
        self.year_filter = FilterBox(model, "Years",    years)
        self.status_filter = FilterBox(model, "Statuses", statuses)
        self.doctype_filter = FilterBox(model, "Document Types", doctypes)
        
        hbox = gtk.HBox()
        hbox.pack_start(self.doctype_filter, False, False)
        hbox.pack_start(self.status_filter, False, False)
        hbox.pack_start(self.year_filter, False, False)
        hbox.pack_start(self.editor_filter, False, False)
        self.add(hbox)
        
###############################################################################
#
# GTK TreeView for viewing projects
#
###############################################################################

class ProjectIndexView(gtk.ScrolledWindow):

    #--------------------------------------------------------------------------
    # Column data functions
    #--------------------------------------------------------------------------
    
    def dfRowNumber(self, col, cell, store, itr):
        cell.set_property("text", store.get_path(itr)[0] + 1)

    def dfPath(self, col, cell, store, itr):
        cell.set_property(
            "text",
            os.path.relpath(store.get_value(itr, 0), conf.rootdir)
        )

    def dfEditor(self, col, cell, store, itr):
        project = store.get_value(itr, 1)
        if project == None:
            cell.set_property("text", "-")
        else:
            cell.set_property("text", project.editor)
            
    def dfTitle(self, col, cell, store, itr):
        project = store.get_value(itr, 1)
        if project == None:
            cell.set_property("text", "-")
        else:
            cell.set_property("text", project.title)
            
    def dfSubtitle(self, col, cell, store, itr):
        project = store.get_value(itr, 1)
        if project == None:
            cell.set_property("text", "-")
        else:
            cell.set_property("text", project.subtitle)
            
    def dfWords(self, col, cell, store, itr):
        project = store.get_value(itr, 1)
        if project == None:
            cell.set_property("text", "-")
        else:
            cell.set_property("text", project.words)
            
    def dfYear(self, col, cell, store, itr):
        project = store.get_value(itr, 1)
        if project == None:
            cell.set_property("text", "-")
        else:
            cell.set_property("text", project.year)
            
    def dfStatus(self, col, cell, store, itr):
        project = store.get_value(itr, 1)
        if project == None:
            cell.set_property("text", "-")
        else:
            cell.set_property("text", project.status)
            
    def dfDeadline(self, col, cell, store, itr):
        project = store.get_value(itr, 1)
        if project == None:
            cell.set_property("text", "-")
        else:
            cell.set_property("text", project.deadline)
            
    def dfDoctype(self, col, cell, store, itr):
        project = store.get_value(itr, 1)
        if project == None:
            cell.set_property("text", "-")
        else:
            cell.set_property("text", project.doctype)
            
    #--------------------------------------------------------------------------
    # Double click
    #--------------------------------------------------------------------------

    def cbRowActivated(self, view, path, col):
        filename = view.get_model()[path][0]
        item = view.get_model()[path][1]
        if item != None and item.editor == "moe":
            execMoe(filename)
        elif os.path.isfile(filename):
            execEdit(filename)
        else:
            execOpenFolder(filename)

    #--------------------------------------------------------------------------
    # Opening projects
    #--------------------------------------------------------------------------

    def openWithMoe(self, action, menuitem):
        treeview = self.treeview
        path, col = treeview.get_cursor()
        filename = treeview.get_model()[path][0]
        execMoe(filename)
            
    def openWithGedit(self, action, menuitem):
        treeview = self.treeview
        path, col = treeview.get_cursor()
        filename = treeview.get_model()[path][0]
        execEdit(filename)
            
    def openFolder(self, action, menuitem):
        treeview = self.treeview
        path, col = treeview.get_cursor()
        dirname = os.path.dirname(treeview.get_model()[path][0])
        execOpenFolder(dirname)
            
    #--------------------------------------------------------------------------
    # Context menu
    #--------------------------------------------------------------------------
    
    def createContextMenu(self):
        menu_items = (
            #------------------------------------------------------------------
            # Project menu
            #------------------------------------------------------------------
            ( "/Open With moe", None, self.openWithMoe, 0, None ),
            ( "/Open With text editor", None, self.openWithGedit, 0, None ),
            ( "/Open Folder", None, self.openFolder, 0, None ),
        )
                
        item_factory = gtk.ItemFactory(gtk.Menu, "<popup>", None)
        item_factory.create_items(menu_items)
        self.popup = item_factory.get_widget("<popup>")

    def onButtonPress(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor( path, col, 0)
                self.popup.popup( None, None, None, event.button, time)
            return True
        
    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------

    def __init__(self, model):
        super(ProjectIndexView,self).__init__()

        self.createContextMenu()
        treeview = gtk.TreeView(model)
        self.treeview = treeview
        treeview.connect("button-press-event", self.onButtonPress)
        treeview.connect("row-activated", self.cbRowActivated)
        
        def addColumn(listbox, col, cell, datafunc):
            col.pack_start(cell, False)
            col.set_cell_data_func(cell, datafunc)
            cell.set_property("yalign", 0.0)
            return cell, col
        
        def newColumn(listbox, name, cell, datafunc):
            col = gtk.TreeViewColumn(name)
            listbox.append_column(col)
            return addColumn(listbox, col, cell, datafunc)
            
        cell, col = newColumn(treeview,
            "#",
            gtk.CellRendererText(),
            self.dfRowNumber
        )

        cell, col = newColumn(
            treeview,
            "Type",
            gtk.CellRendererText(),
            self.dfDoctype
        )
        
        cell, col = newColumn(
            treeview,
            "Title",
            gtk.CellRendererText(),
            self.dfTitle
        )
        
        cell, col = newColumn(
            treeview,
            "Status",
            gtk.CellRendererText(),
            self.dfStatus
        )
        
        cell, col = newColumn(
            treeview,
            "Deadline",
            gtk.CellRendererText(),
            self.dfDeadline
        )
        
        cell, col = newColumn(
            treeview,
            "Year",
            gtk.CellRendererText(),
            self.dfYear
        )        
        
        cell, col = newColumn(
            treeview,
            "Words",
            gtk.CellRendererText(),
            self.dfWords
        )
        cell.set_property("xalign", 1.0)

        cell, col = newColumn(
            treeview,
            "Editor",
            gtk.CellRendererText(),
            self.dfEditor
        )
        
        cell, col = newColumn(
            treeview,
            "Path",
            gtk.CellRendererText(),
            self.dfPath
        )
        
        self.add(treeview)

###############################################################################
#
# Project Manager main window
#
###############################################################################

doRefresh = True

class ProjectWindow(gtk.Window):

    #--------------------------------------------------------------------------
    # Filtering & sorting functions
    #--------------------------------------------------------------------------

    def cbFilter(self, model, iter):
        item = model.get_value(iter,1)
        return self.filterview.cbVisible(item)
            
    def cbSort(self, model, iter1, iter2):
        item1 = model.get_value(iter1,1)
        item2 = model.get_value(iter2,1)
        return cmp(item1, item2)
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbRefresh(self, widget, event = None):
        global doRefresh
        doRefresh = True
        gtk.main_quit()
        
    def showAbout(self, widget, event = None):
        about = gtk.AboutDialog()
        about.set_name("moepm")
        about.set_version(conf.version)
        about.set_copyright("(c) Markus Koskimies")
        about.set_comments(
            "Project manager for MOE."
        )
        about.set_website("http://mkoskim.drivehq.com")
        about.run()
        about.destroy()

    def cbNewMoe(self, widget, event = None):
        execMoe("--new")

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def makeMenuBar(self):
        hotkeys = (
            #( "<control>Page_Up", self.prevItem ),
            #( "<control>Page_Down", self.nextItem ),
            #( "<alt>I", self.focusList ),
            #( "<alt>C", self.focusContent ),
            #( "<alt>H", self.focusDescription ),
        )

        menu_items = (
            #------------------------------------------------------------------
            # Project menu
            #------------------------------------------------------------------

            ( "/_File", None, None, 0, "<Branch>" ),
            ( "/File/New",     None, self.cbNewMoe, 0, None),

            ( "/File/s1", None, None, 0, "<Separator>" ),
            ( "/File/_Refresh",  None, self.cbRefresh, 0, None),
            
            ( "/File/s2", None, None, 0, "<Separator>" ),
            ( "/File/_Quit",    "<control>Q", self.exit, 0, None),

            #------------------------------------------------------------------
            # Help menu
            #------------------------------------------------------------------

            ( "/_Help",        None, None, 0, "<Branch>" ),
            ( "/Help/Contents", "F1", None, 0, None ),
            ( "/Help/About", None, self.showAbout, 0, None ),
        )

        accel_group = gtk.AccelGroup()

        for hotkey in hotkeys:
            keyval, mod = gtk.accelerator_parse(hotkey[0])
            accel_group.connect_group(
                keyval, mod, 0, hotkey[1]
            )

        item_factory = gtk.ItemFactory(gtk.MenuBar, "<main>", accel_group)
        item_factory.create_items(menu_items)
        self.add_accel_group(accel_group)
        self.item_factory = item_factory
        return item_factory.get_widget("<main>")
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def exit(self, window, event = None):
        conf.set_gui("PMWindow", "width", self.get_allocation().width)
        conf.set_gui("PMWindow", "height", self.get_allocation().height)
        conf.save()

        gtk.main_quit()

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self):
        super(ProjectWindow,self).__init__(gtk.WINDOW_TOPLEVEL)
        
        self.resize(
            int(conf.get_gui("PMWindow", "width")),
            int(conf.get_gui("PMWindow", "height"))
        )

        self.connect("delete-event", self.exit)
        self.set_title("moe: Project Manager")
        
        resetSets()        
        model = ProjectStore()
        model.populate(conf.rootdir)
        
        self.treefilter = model.filter_new()

        self.treesorter = gtk.TreeModelSort(self.treefilter)
        self.treesorter.set_sort_func(0, self.cbSort)
        self.treesorter.set_sort_column_id(0, gtk.SORT_DESCENDING)
        
        self.filterview = FilterView(self.treefilter)

        self.treefilter.set_visible_func(self.cbFilter)
        self.treefilter.refilter()

        self.indexview = ProjectIndexView(self.treesorter)
        
        vbox = gtk.VBox()
        vbox.pack_start(self.makeMenuBar(), False, False)
        vbox.pack_start(self.filterview, False, False)
        vbox.pack_start(self.indexview)
        self.add(vbox)
        
        self.show_all()
        pass

###############################################################################
#
# Main
#
###############################################################################

if __name__ == "__main__":
    while doRefresh:
        doRefresh = False
        window = ProjectWindow()
        gtk.main()
        window.destroy()
    pass
    
