#!/usr/bin/env python
###############################################################################
#
# MOE (Markus' Own Editor): Multipart file editor, with project manager
#
###############################################################################

from config import conf
from helpers import *
from moeGTK import *

import extformats

from moeEditor import Editor
from moeItemScene import SceneItem
from moeItemGroup import GroupItem
from moeItemTitle import TitleItem

from moeExport import exportTree

from moeDialogPrefs import editPreferences
#from moeDialogSearch import search

###############################################################################
#
# Application (Project)
#
###############################################################################

class EditorWindow(gtk.Window):

    def traceEvent(self, widget, event):
        print widget, event
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self, filename = None):
        super(EditorWindow,self).__init__(gtk.WINDOW_TOPLEVEL)

        conf.mainwnd = self

        self.set_resizable(True)  
        self.connect("delete-event", self.exit)

        if filename != None:
            self.editor = Editor(self, filename)
            gotodir(filename)
        else:
            self.editor = Editor(self)

        vbox = gtk.VBox()
        vbox.pack_start(self.makeMenuBar(), False, False)
        vbox.pack_start(self.editor)
        self.add(vbox)
        
        self.resize(
            int(conf.get_gui("Window", "width")),
            int(conf.get_gui("Window", "height"))
        )

        self.show_all()

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def showAbout(self, widget, event = None):
        about = gtk.AboutDialog()
        about.set_name("moe")
        about.set_version(conf.version)
        about.set_copyright("(c) Markus Koskimies")
        about.set_comments(
            "Specialized text editor for novel/novellette writing."
        )
        about.set_website("http://mkoskim.drivehq.com")
        about.run()
        about.destroy()

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def isBrandNew(self):
        return \
            self.editor.document.filename == None and \
            not self.editor.isDirty()

    def isEmpty(self):
        return self.editor.view == None

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def close(self, widget, event = None):
        if self.isEmpty():
            gtk.main_quit()
        else:
            self.editor.close()
        return True
        
    def exit(self, widget, event = None):
        print "Exiting..."
        if not self.editor.close():
            print "Cancelled."
            return True
        gtk.main_quit()

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def new(self, widget, event = None):
        if self.isEmpty():
            self.editor.new()
        elif self.isBrandNew():
            pass
        else:
            execMoe()

    def load(self, widget, event = None):
        filename = userLoadFile(
            "Load",
            patterns = [
                [ "MOE Files (.moe)", ["*.moe"]],
                [ "All files", ["*.*"]],
            ]
        )
        if filename != None:
            if self.isEmpty() or self.isBrandNew():
                self.editor.close()
                self.editor.load(filename)
                gotodir(filename)
            else:
                execMoe(filename)

    def revert(self, widget, event = None):
        if not self.editor.isDirty():
            userInform("Document has not been changed. No need to reload.")
            return

        if self.editor.document.filename == None:
            userInform(
                "Cannot reload. Project is not saved yet.",
                gtk.MESSAGE_ERROR
            )
            return
            
        answer = userConfirm(
            "All changes will be discarded. " +
            "Are you sure to continue?"
        )
        
        if answer:
            print "Reverting project..."
            filename = self.editor.document.filename
            self.editor.close(True)
            self.editor.load(filename, True)

    def _save(self, filename = None):
        self.editor.save(filename)
        if filename: gotodir(filename)
        
    def suggestName(self):
        document = self.editor.document
        if document.filename != None:
            return os.path.splitext(os.path.basename(document.filename))[0]
        else:
            return document.title.title.get_content()
    
    def save_as(self, widget, event = None):
        filename = userSaveFile("Save",
            suggestion = self.suggestName() + ".moe", 
            patterns = [ 
                ["MOE Files (.moe)", ["*.moe"]],
                ["All files", ["*.*"]]
            ]
        )
        if filename != None: self._save(filename)
    
    def save(self, widget, event = None):
        #if not self.editor.isDirty(): return

        if self.editor.document.filename != None:
            self._save()
        else:
            self.save_as(self)
        
    #--------------------------------------------------------------------------
    # Simple exporting (no processing of texifier tags)
    #--------------------------------------------------------------------------

    def _export(self, fmt, pattern):
        filename = userSaveFile(
            "Export",
            suggestion = self.suggestName() + pattern[1][0][1:],
            patterns = [
                pattern,
                [ "All files", ["*.*"] ],
            ]
        )
        if filename:
            writefile(
                filename,
                exportTree(self.editor.document.getXMLTree(), fmt)
            )
        return filename
        
    def export2RTF(self, widget, event = None):
        filename = self._export("rtf", [ "RTF (.rtf)",   ["*.rtf"] ])
        if filename: execOpenDoc(filename)
    
    #--------------------------------------------------------------------------
    # Texifying (exporting with processing texifier tags)
    #--------------------------------------------------------------------------

    def _texify(self, widget, fmt):

        print "Texifying to:", fmt
        
        # Check, if texifier exists
        texifierdir = relpath(conf.rootdir + "/defaults")
        print "Texifier:", texifierdir
        if not os.path.isdir(texifierdir): return

        # Save and check file name
        self.save(widget)
        docname = self.editor.document.filename
        if not docname: return

        # Get document directory
        docdir  = os.path.abspath(os.path.dirname(docname))

        # Run texifier
        docbase = os.path.splitext(os.path.basename(docname))[0]
        os.system("make -f %s/defaults.mak ROOTDIR=%s DOCNAME=%s %s" % (
            texifierdir,
            conf.rootdir,
            docbase,
            fmt)
        )
        return docbase + "." + fmt

    def texify2RTF(self, widget, event = None):
        exported = self._texify(widget, "rtf")
        if exported: execOpenDoc(exported)
        
    def texify2PDF(self, widget, event = None):
        exported = self._texify(widget, "pdf")
        if exported: execOpenPDF(exported)

    def texify2EPUB(self, widget, event = None):
        exported = self._texify(widget, "epub")
        if exported: execOpenEPUB(exported)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def insertScene(self, widget, event = None):
        self.editor.insert(SceneItem(self.editor.document))
    
    def insertGroup(self, widget, event = None):
        self.editor.insert(GroupItem(self.editor.document,
            name = "<Unnamed Group>",
            level = -1
        ))
    
    def insertDesign(self, widget, event = None):
        self.editor.insert(GroupItem(self.editor.document,
            name = "<Unnamed Design>",
            included = False,
            alterable = False
        ))
    
    def insertFile(self, widget, event = None):
        filename = userLoadFile("Insert File...")
        if filename != None:
            content = extformats.importFile(filename)
            self.editor.insert(
                SceneItem(
                    self.editor.document,
                    name = relpath(filename, os.getcwd()),
                    content = content,
                )
            )
            gotodir(filename)

    #--------------------------------------------------------------------------
    # Picking parts from MOE files
    #--------------------------------------------------------------------------

    def pickSnippets(self, widget, event = None):
        self.editor.pickSnippets(conf.snippetfile)
    
    def pickFromFile(self, widget, event = None):
        self.editor.pickSnippets()
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def splitItem(self, widget, event = None):
        self.editor.split_current()
        
    def mergeItem(self, widget, event = None):
        self.editor.merge_current()

    def deleteItem(self, widget, event = None):
        self.editor.delete_current()

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def undo(self, widget, event = None):
        focus = self.get_focus()
        if hasattr(focus, "undo"): focus.undo()

    def redo(self, widget, event = None):
        focus = self.get_focus()
        if hasattr(focus, "redo"): focus.redo()

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def updateWordCount(self, widget, event = None):
        self.editor.updateWordCount()

    def preferences(self, widget, event = None):
        editPreferences()

    def search(self, widget, event = None):
        self.editor.search(mode = "find")
        
    def spellcheck(self, widget, event = None):
        self.editor.search(mode = "spellcheck")

    def projectmanager(self, widget, event = None):
        execMoePM()

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
            # File menu
            #------------------------------------------------------------------

            ( "/_File", None, None, 0, "<Branch>" ),
            ( "/File/New",     None, self.new, 0, None),
            ( "/File/Open...", None, self.load, 0, None),

            ( "/File/s1", None, None, 0, "<Separator>" ),
            ( "/File/_Save",    "<control>S", self.save, 0, None),
            ( "/File/Save _As...", None, self.save_as, 0, None),
            ( "/File/_Reload",  None, self.revert, 0, None),

            ( "/File/s2", None, None, 0, "<Separator>" ),
            ( "/File/Texify",      None, None, 0, "<Branch>"),
            ( "/File/Texify/RTF",  None, self.texify2RTF, 0, None),
            ( "/File/Texify/PDF",  None, self.texify2PDF, 0, None),
            ( "/File/Texify/EPUB", None, self.texify2EPUB, 0, None),
            ( "/File/Export RTF",  None, self.export2RTF, 0, None),

            ( "/File/s3", None, None, 0, "<Separator>" ),
            ( "/File/_Close",   "<control>W", self.close, 0, None),
            ( "/File/_Quit",    "<control>Q", self.exit, 0, None),

            #------------------------------------------------------------------
            # Edit menu
            #------------------------------------------------------------------

            ( "/_Edit", None, None, 0, "<Branch>"),
            ( "/Edit/_Undo", "<control>Z", self.undo, 0, None),
            ( "/Edit/_Redo", "<shift><control>Z", self.redo, 0, None),

            ( "/Edit/s1", None, None, 0, "<Separator>"),
            ( "/Edit/_Split",     "<alt>X",     self.splitItem, 0, None ),
            ( "/Edit/_Merge",     "<alt>M",     self.mergeItem, 0, None ),
            ( "/Edit/_Delete",     "<alt>D",    self.deleteItem, 0, None ),

            ( "/Edit/s2", None, None, 0, "<Separator>"),
            ( "/Edit/Find...", "<ctrl>F", self.search, 0, None),
            
            ( "/Edit/s3", None, None, 0, "<Separator>"),
            ( "/Edit/Preferences", None, self.preferences, 0, None ),
            
            #------------------------------------------------------------------
            # Insert menu
            #------------------------------------------------------------------

            ( "/_Insert", None, None, 0, "<Branch>"),
            
            ( "/Insert/_Scene",  "<control>N", self.insertScene, 0, None ),
            ( "/Insert/_Group",  None, self.insertGroup, 0, None ),
            ( "/Insert/_Design", None, self.insertDesign, 0, None),

            ( "/Insert/s1", None, None, 0, "<Separator>" ),
            ( "/Insert/_Pick", None, None, 0, "<Branch>" ),
            ( "/Insert/Pick/Snippets", None, self.pickSnippets, 0, None),
            ( "/Insert/Pick/From file", None, self.pickFromFile, 0, None),

            ( "/Insert/s2", None, None, 0, "<Separator>" ),
            ( "/Insert/_File", None, self.insertFile, 0, None),

            #------------------------------------------------------------------
            # Tools menu
            #------------------------------------------------------------------

            ( "/_Tools", None, None, 0, "<Branch>" ),
            ( "/Tools/Spelling...", "F7", self.spellcheck, 0, None ),
            ( "/Tools/Word Count", "<control>U", self.updateWordCount, 0, None),
            ( "/Tools/s1", None, None, 0, "<Separator>"),
            ( "/Tools/Project Manager", None, self.projectmanager, 0, None),

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

###############################################################################
#
# Main
#
###############################################################################

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--new":
            EditorWindow()
        else:
            EditorWindow(sys.argv[1])
    else:
        files = os.listdir(".")
        files = filter(lambda s: os.path.splitext(s)[1] == ".moe", files)
        if len(files) == 1:
            EditorWindow(files[0])
        else:
            EditorWindow()
    gtk.main()
