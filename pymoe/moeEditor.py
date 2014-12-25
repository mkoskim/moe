#!/usr/bin/env python
###############################################################################
#
# Multi-part Text Editor
#
###############################################################################
#
# This part of the mte project contains the actual multi-part file editing
# GUI and such. The idea is, that the text is splitted to ASCII files into
# one directory, which contains index.tex file telling the structure of
# the text.
#
###############################################################################

import sys
import re
import string
import os

from config import conf
from helpers import *
from moeGTK import *

from moeDocument import Document
from moeItemScene import SceneItem

from views import EditorViewIndex
from views import EditorViewFlatten, EditorViewNew

from experimental import EditorViewSynopses
from experimental import EditorViewSearch

class Editor(gtk.VBox):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self, mainwnd, filename = None):
        super(Editor,self).__init__()
        
        self.mainwnd = mainwnd
        
        self.document = None
        self.toolbar = self.makeToolBar()
        self.pack_start(self.toolbar, False, False)
        
        if filename == None:
            self.new()
        else:
            if os.path.isfile(filename):
                self.load(filename)
            else:
                self.new()
                self.document.filename = filename

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def set_title(self, title):
        if self.document and self.document.isDirty():
            dirty_marker = "*"
        else:
            dirty_marker = ""
            
        self.mainwnd.set_title(dirty_marker + "moe: " + title)

    #--------------------------------------------------------------------------
    # Views
    #--------------------------------------------------------------------------

    views = { }
    view = None
    
    def EditorViewDraft(document, mode):
        scenes = document.collect(
            lambda item: isinstance(item, SceneItem) and item.included
        )
        if len(scenes) == 1:
            return EditorViewNew(document, scenes[0], mode)
        else:
            document.flatten(document._FlatContent)
            return EditorViewFlatten(document, mode)

    def EditorViewOutline(document, mode):
        document.flatten(document._FlatSynopses)
        return EditorViewFlatten(document, mode)
    
    viewchoices = {
        None: EditorViewIndex,
        "Draft": EditorViewDraft,
        "Outline": EditorViewOutline,
        "Index": EditorViewIndex,
        "Synopses": EditorViewSynopses,
        "Find": EditorViewSearch,
    }

    def _createView(self, viewname, mode = None):
        if viewname in self.views:
            view = self.views[viewname]
        else:
            view = None
        if view == None:
            if viewname not in self.viewchoices:
                viewname = None
            view = self.viewchoices[viewname](self.document, mode)
            self.views[viewname] = view
        view.viewname = viewname
        return view

    def _destroyView(self):
        if self.view == None: return
        if hasattr(self.view, "switchOut"): self.view.switchOut()        
        self.view.hide_all()
        self.remove(self.view)
        if not hasattr(self.view, "persistent") or not self.view.persistent:
            self.views[self.view.viewname] = None
            self.view.destroy()
        self.view = None
            
    def _toggleViewButton(self, viewname):
        viewbuttons = self.toolbar.RadioButton.groups["view"][1]
        if viewname in viewbuttons:
            viewbuttons[viewname].set_active(True)
        else:
            viewbuttons["Index"].set_active(True)

    def _changeView(self, viewname, mode = None):
        if self.view != None and self.view.viewname == viewname: return
        if viewname == None: viewname = "Draft"
        self._destroyView()
        self.view = self._createView(viewname, mode)
        self.pack_start(self.view)
        self.view.show_all()
        if hasattr(self.view, "switchIn"): self.view.switchIn()
        if hasattr(self.view, "grabber"):
            self.view.grabber.grab_focus()
        
    def cbShowIndex(self, widget = None):
        self._changeView("Index")
            
    def cbShowDraft(self, widget = None):
        self._changeView("Draft")

    def cbShowOutline(self, widget = None):
        self._changeView("Outline")
                    
    def cbShowSynopses(self, widget = None):
        self._changeView("Synopses")

    def search(self, widget = None, mode = "find"):
        self._changeView("Find", mode)

    #--------------------------------------------------------------------------
    # Toolbox
    #--------------------------------------------------------------------------

    def makeToolBar(self):

        return ToolBar(
            ToolBar.RadioButton(
                "Index", "view", self.cbShowIndex,
                "Show index"
            ),
            
            ToolBar.RadioButton(
                "Draft", "view", self.cbShowDraft,
                "Show draft"
            ),
            
            ToolBar.Separator(),

            ToolBar.RadioButton(
                "Synopses", "view", self.cbShowSynopses,
                "Show synopses"
            ),
            
            ToolBar.RadioButton(
                "Outline", "view", self.cbShowOutline,
                "Show outline"
            ),

            ToolBar.Separator(),

            ToolBar.RadioButton(
                "Find", "view", self.search,
                "Find & Replace"
            ),

            ToolBar.Separator(),

        )            

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def close(self, confirmed = False):
        if not self.document: return True
            
        if not confirmed and self.isDirty():
            answer = userSaveDiscardCancel(
                ("Project '%s' has been modified. " + \
                "Do you want to save it before closing?") % \
                (self.document.getTitle())
            )
            
            if answer == gtk.RESPONSE_CANCEL:
                print "Cancelling"
                return False
            if answer == gtk.RESPONSE_YES:
                self.save()
                
        # ---------------------------------------------------------------------

        width, height = self.mainwnd.get_size()
        conf.set_gui("Window", "width", width)
        conf.set_gui("Window", "height", height)
        conf.set_doc("View", "name", self.view.viewname)

        # ---------------------------------------------------------------------

        for view in self.views.values():
            if not view: continue
            if hasattr(view, "switchOut"): view.switchOut()
            view.hide_all()
            self.remove(view)
            view.destroy()

        self.toolbar.hide_all()

        # ---------------------------------------------------------------------
        # Save config last (but before closing document). Some components may
        # store configs at closing.
        # ---------------------------------------------------------------------

        conf.save(self.document.filename)
        
        # ---------------------------------------------------------------------

        self.document.close()
        self.document = None
        self.set_title("moe")

        return True
        
    #--------------------------------------------------------------------------
    # Views. Note: if we choose the same view that is activated by toolbar
    # by default, we need explicitely create the view.
    #--------------------------------------------------------------------------

    def finalize(self, viewname = "Index"):
        self.toolbar.show_all()
        self._toggleViewButton(viewname)
        if not self.view:
            self._changeView(viewname)

    #--------------------------------------------------------------------------
    # New, load, save project
    #--------------------------------------------------------------------------

    def new(self):
        if not self.close(): return
        self.document = Document(self)
        self.finalize("Draft")
        
    def load(self, filename, confirmed = False):
        if not self.close(confirmed): return
        self.document = Document(self,filename)
        self.finalize(conf.get_doc("View", "name"))
        
    def save(self, filename = None):
        if filename != None:
            self.document.filename = filename
        self.document.save()
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def updateWordCount(self):
        self.document.updateWordCount()

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def isDirty(self):
        return self.document != None and self.document.isDirty()

    def reload_current(self):
        self.view.reload_current()

    def delete_current(self):
        self.view.delete_current()
        
    def insert(self, item):
        self.view.insert(item)    
        
    def split_current(self):
        self.view.split_current()
        
    def merge_current(self):
        self.view.merge_current()

    #--------------------------------------------------------------------------
    # Picking parts from MOE files
    #--------------------------------------------------------------------------

    def pickSnippets(self, filename = None):
        self.view.pickSnippets(filename)


