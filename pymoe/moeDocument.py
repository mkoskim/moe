#!/usr/bin/env python
###############################################################################
#
# MOE Document
#
###############################################################################

import string
import re
import socket

from config import conf
from helpers import *
from moeGTK import *

import extformats

import moeXML
from moeXML import ET, ExpatError

from moeItemScene import SceneItem
from moeItemGroup import GroupItem
from moeItemTitle import TitleItem
from moeItemTrashcan import TrashcanItem

###############################################################################
#
# Store of items
#
###############################################################################

class Document(gtk.TreeStore):

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def setTitle(self, title):
        if self.mainwnd: self.mainwnd.set_title(title)
        
    def getTitle(self):
        return self.title.title.get_content()

    def cbTitleChanged(self, widget):
        self.setTitle(self.getTitle())

    #--------------------------------------------------------------------------
    # Dirty control
    #--------------------------------------------------------------------------

    def cbModified(self, widget, event = None):
        #print self.dirty, "Document.cbModified()", widget        
        if not self.dirty:
            self.dirty = True
            self.cbTitleChanged(self)

    def isDirty(self):
        return self.dirty

    def clearDirty(self):
        if self.dirty:
            self.dirty = False
            self.cbTitleChanged(self)
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def cbRenumRequest(self, widget, event = None):
        self.renum()
        
    def watchDirty(self, *widgets):
        for widget in widgets:
            widget.connect("changed", self.cbModified)

    def watchRenum(self, *widgets):
        for widget in widgets:
            widget.connect("changed", self.cbRenumRequest)
                        
    def cbRowInserted(self, model, path, iter):
        self.cbModified(self)
        
    def cbRowDeleted(self, model, path):
        self.cbModified(self)
        
    #--------------------------------------------------------------------------
    # Create doc: if mainwnd = None: creates doc for automatic processing,
    # either loaded from file, or totally empty.
    #--------------------------------------------------------------------------

    def __init__(self, mainwnd, filename = None):
        super(Document,self).__init__(object)
        
        self.mainwnd = mainwnd
        self.title = None
        self.dirty = False
            
        if mainwnd:
            self.connect("row-inserted", self.cbRowInserted)
            self.connect("row-deleted", self.cbRowDeleted)
        
        if filename == None:
            if mainwnd: self.new()
        else:
            filename = os.path.abspath(filename)
            self.load(filename)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def move_subtree(self, from_iter, to_iter):
        if not self.iter_has_child(from_iter):
            return
            
        from_child = self.iter_children(from_iter)
        while from_child != None:
            from_child_path = self.get_path(from_child)
            to_child = self.append(to_iter, row=self[tuple(from_child_path)])
            self.move_subtree(from_child, to_child)
            from_child = self.iter_next(from_child)

    def drop_in(self, from_iter, to_iter):
        from_path = self.get_path(from_iter)
        to_iter = self.append(to_iter, self[tuple(from_path)])
        self.move_subtree(from_iter, to_iter)
        return self.remove(from_iter)
    
    def move_after(self, from_iter, to_iter):
        from_path = self.get_path(from_iter)
        to_iter = self.insert_after(
            self.iter_parent(to_iter),
            to_iter,
            self[tuple(from_path)]
        )
        self.move_subtree(from_iter, to_iter)
        return self.remove(from_iter)
        
    def move_before(self, from_iter, to_iter):
        from_path = self.get_path(from_iter)
        to_iter = self.insert_before(
            self.iter_parent(to_iter),
            to_iter,
            self[tuple(from_path)]
        )
        self.move_subtree(from_iter, to_iter)
        return self.remove(from_iter)
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def iter_first_child(self, iter):
        return self.iter_children(iter)
        
    def iter_last_child(self, iter):
        n = self.iter_n_children(iter)
        if n == 0:
            return self.iter_children(iter)
        else:
            return self.iter_nth_child(iter, n)

    def iter_last(self):
        next = self.get_iter_first()
        while next:
            last = next
            next = self.iter_next(last)
        return last

    #--------------------------------------------------------------------------
    # Traversing
    #--------------------------------------------------------------------------

    def foreach(self, func, iter = None, prune = lambda item: True):
        if iter == None:
            iter = self.get_iter_first()
        while iter != None:
            item = self.get_value(iter, 0)
            if prune(item):
                func(self, self.get_path(iter), iter)
                if self.iter_has_child(iter):
                    self.foreach(func, self.iter_children(iter), prune)
            iter = self.iter_next(iter)

    #--------------------------------------------------------------------------

    def collect(self, criteria = lambda item: True):

        items = []
        
        self.foreach(lambda model, path, iter: items.append(self[path][0]))

        return filter(criteria, items)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def find(self, item):
        class FoundException(Exception):
            def __init__(self, iter):
                self.iter = iter
        
        def match(model, path, iter):
            if model.get_value(iter,0) == item:
                raise FoundException(iter)
        
        try:
            self.foreach(match)
        except FoundException, (instance):
            return instance.iter

        return None
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def dump(self, iter = None):
        if iter == None:
            print "Items:", len(self)
            iter = self.get_iter_first()
        level = self.iter_depth(iter)

        while iter != None:
            item = self.get_value(iter,0)
            print "   " * level, item.getName()
            if self.iter_has_child(iter):
                self.dump(self.iter_children(iter))
            iter = self.iter_next(iter)

    #--------------------------------------------------------------------------
    # TODO: Change to use foreach()
    #--------------------------------------------------------------------------
    
    def updateWordCount(self):

        def updateWords(iter):
            if iter == None:
                item = self.title
                child = self.get_iter_root()
                wc = 0
            else:
                item = self.get_value(iter, 0)
                wc = item.calcWordCount()
                child = self.iter_children(iter)
            while child != None:
                child_words = updateWords(child)
                if self.get_value(child,0).included:
                    wc += child_words
                child = self.iter_next(child)
            if item.included:
                item.setWordCount(wc)
            else:
                item.setWordCount(None)
            if iter != None:
                self.row_changed(self.get_path(iter), iter)
            return wc

        updateWords(None)            
        self.cbModified(self)
        
    #--------------------------------------------------------------------------
    # Renumbering & level adjusting
    #--------------------------------------------------------------------------

    def renum(self):
    
        def _clearNumber(self, path, iter):
            item = self.get_value(iter,0)
            item.number = ""
            if hasattr(item, "scene"): item.scene = None
            self.row_changed(path, iter)
        
        self.foreach(_clearNumber)
        
        #----------------------------------------------------------------------
        #----------------------------------------------------------------------
        
        class Numbers:
            part = 1
            chapter = 1
            scene = 1

        num = Numbers()        

        #----------------------------------------------------------------------
        #----------------------------------------------------------------------
        
        def renumScene(item, level, num):
            if level == 0:
                item.number = "Osa %s" % int2roman(num.part)
                num.part += 1
            elif level == 1:
                item.number = "%d." % num.chapter
                num.chapter += 1
            item.scene = num.scene
            num.scene += 1

        def renumGroup(item, level, num):    
            if level == 0:
                item.number = "Osa %s" % int2roman(num.part)
                num.part += 1
            elif level == 1:
                item.number = "%d." % num.chapter
                num.chapter += 1
            else:
                item.number = ""
        
        def _renum_childs(iter, level, num):
            child = self.iter_children(iter)
            if child != None:
                while child:
                    _renum(child, level + 1, num)
                    child = self.iter_next(child)
        
        def _renum(iter, level, num):
            item = self.get_value(iter, 0)
            if not item.included: return
            
            if item.__class__.__name__ == "GroupItem":
                renumGroup(item, level, num)
            elif item.__class__.__name__ == "SceneItem":
                renumScene(item, level, num)                

            _renum_childs(iter, level, num)

        #----------------------------------------------------------------------
        #----------------------------------------------------------------------
        
        iters = []
        iter = self.get_iter_first()
        while iter:
            item = self.get_value(iter, 0)
            if item.included:
                if item.__class__.__name__ in [ "GroupItem", "SceneItem" ]:
                    iters.append(iter)
            iter = self.iter_next(iter)
        
        #----------------------------------------------------------------------
        #----------------------------------------------------------------------

        toplevel = { 1: 1, 2: 0 }[self.title.getTopLevel()]
        
        if self.title.hasPrologue():
            prologue, iters = iters[0], iters[1:]
        else:
            prologue = None
            
        if self.title.hasEpilogue():
            epilogue, iters = iters[-1], iters[:-1]
        else:
            epilogue = None
            
        if prologue:
            _renum_childs(prologue, toplevel + 1, num)
            item = self.get_value(prologue, 0)
            item.number = "Prologue"
            
        for iter in iters: _renum(iter, toplevel, num)

        if epilogue:
            _renum_childs(epilogue, toplevel + 1, num)
            item = self.get_value(epilogue, 0)
            item.number = "Epilogue"
        
        self.updateWordCount()
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def close(self):
        self.clear()

    def finalize(self, filename):
        self.trashcan = TrashcanItem(self)
        self.append(None, [self.trashcan])

        self.filename = filename
        conf.load(filename)
        
        self.title.name.connect("changed", self.cbTitleChanged)
        self.cbTitleChanged(self)
        self.renum()
        self.clearDirty()
        
    def tree2item(self, ET, root, iter_parent = None):
        for elem in root:
            if elem.tag == "SceneItem":
                item = SceneItem(self, ET, elem)
            elif elem.tag == "GroupItem":
                item = GroupItem(self, ET, elem,
                    level = int(elem.get("level")),
                    alterable = bool(elem.get("alterable"))
                )
            elif elem.tag == "ChapterItem":
                item = GroupItem(self, ET, elem, level = 1)
            elif elem.tag == "PartItem":
                item = GroupItem(self, ET, elem, level = 2)
            elif elem.tag == "DesignItem":
                item = GroupItem(self, ET, elem,
                    included = False,
                    alterable = False
                )
            elif elem.tag == "settings":
                continue
            else:
                raise Exception("Unknown tag: %s" % elem.tag)
                
            iter_child = self.append(iter_parent, [item])
            childs = elem.find("childs")
            if childs != None: 
                self.tree2item(ET, childs, iter_child)

    def configTitle(self, ET, elem):
        item = TitleItem(self, ET, elem)
        self.title = item
        self.append(None, [item])
        
    def content2item(self, content):
        tree = ET.ElementTree(ET.fromstring(content))
        root = tree.getroot()    
        
        elems = list(root)
        title   = filter(lambda e: e.tag == "TitleItem", elems)[0]
        content = filter(lambda e: e.tag != "TitleItem", elems)
        
        self.configTitle(tree, title)
        self.tree2item(ET, content)
    
    def load(self, filename):
        content = readfile(filename)
        try:
            self.content2item(content)        
        except (SyntaxError, ExpatError):
            return self.new(
                scene = SceneItem(
                    self,
                    content = extformats.importFile(filename)
                )
            )
            
        self.finalize(filename)

    def new(self, scene = None):
        self.title = TitleItem(self)
        self.append(None, [self.title])
        
        if scene == None:
            self.append(None, [SceneItem(self)])
        else:
            self.append(None, [scene])
            
        self.finalize(None)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def items2tree(self, root, iter = None):
        if iter == None:
            iter = self.get_iter_first()
        while iter != None:
            item = self.get_value(iter,0)
            child_root = item.save(ET, root)
            if self.iter_has_child(iter) and child_root != None:
                child_list = ET.SubElement(child_root, "childs")
                self.items2tree(child_list, self.iter_children(iter))
            iter = self.iter_next(iter)
    
    def getXMLTree(self):
        root = ET.Element("story")
        self.items2tree(root)
        
        moeXML.prettyFormat(root)
        return root
    
    def save(self, filename = None):
        self.deflatten()

        self.updateWordCount()
        tree = self.getXMLTree()
        content = ET.tostring(tree, conf.encoding)
        if filename == None:
            filename = self.filename
        writefile(filename, content)

        self.clearDirty()

    #--------------------------------------------------------------------------
    # "Flattening" and "deflattening" the document
    #--------------------------------------------------------------------------

    class FlatBuf(TextBuf):

        def __init__(self):
            super(Document.FlatBuf, self).__init__()

            self.blocks = []

            self.create_tag("normal")
            self.create_tag("synopsis",
                background = conf.bg_synopses,
                paragraph_background = conf.bg_synopses,
                background_full_height = True,
                invisible = not (conf.get_doc("DraftEdit", "Synopses") == "True")
            )

            self.create_tag("blockname",
                editable=False,
                justification=gtk.JUSTIFY_CENTER,
                weight = pango.WEIGHT_BOLD,
            )

        class ListItem:
            def __init__(self, name, buf, tag = "normal", index = None):
                self.name  = name
                self.buf   = buf
                self.tag   = tag
                self.index = index
                self.start = None
                self.end   = None

        def addbuf(self, name, buf, tag = "normal", index = None):
            self.blocks.append(
                Document.FlatBuf.ListItem(name, buf, tag, index)
            )

        def finalize(self):
        
            def _emptyblock(s): return (s and len(s)) and s or "..."
            def _emptyname(s):  return (s and len(s)) and s or "---"

            prev = self.blocks[0]
            prev.start = self.create_mark(None, self.get_start_iter(), True)
            self.insert_with_tags_by_name(
                self.get_end_iter(),
                _emptyblock(prev.buf.get_content()),
                prev.tag
                )

            for next in self.blocks[1:]:
            
                self.insert_with_tags_by_name(
                    self.get_end_iter(),
                    "\n\n",
                    "blockname", prev.tag,
                )
                prev.end = self.create_mark(None, self.get_end_iter(), True)
                
                self.insert_with_tags_by_name(
                    self.get_end_iter(),
                    _emptyname(next.name) + "\n\n",
                    "blockname", prev.tag,
                )
                next.start = self.create_mark(None, self.get_end_iter(), True)
                self.insert_with_tags_by_name(
                    self.get_end_iter(),
                    _emptyblock(next.buf.get_content()),
                    next.tag
                )
                prev = next
                
            prev.end = self.create_mark(None, self.get_end_iter(), False)

            self.place_cursor(self.get_start_iter())
            self.set_modified(False)

        def commit(self):
            if not self.get_modified(): return
            
            for item in self.blocks:
                item.buf.set_content(
                    string.strip(
                        self.get_text(
                            self.get_iter_at_mark(item.start),
                            self.get_iter_at_mark(item.end),
                            True
                        )
                    )
                )
            
            self.set_modified(False)

    #--------------------------------------------------------------------------

    @staticmethod
    def _FlatContent(self, path, iter):
        item = self.get_value(iter,0)
        if "content" in item.elements:
            self.flat.addbuf(
                item.getName(),
                item["synopsis"],
                "synopsis",
                index = None
            )
            self.flat.addbuf(
                None,
                item["content"],
                index = item.getName()
            )
                
    @staticmethod
    def _FlatSynopses(self, path, iter):
        item = self.get_value(iter,0)
        if isinstance(item, SceneItem):
            self.flat.addbuf(
                item.getName(),
                item["synopsis"],
                index = item.getName()
            )
                
    #--------------------------------------------------------------------------

    def flatten(self, flatfunc):
    
        self.flat = Document.FlatBuf()

        self.foreach(
            flatfunc,
            prune = lambda item: item.included
        )
        self.flat.finalize()
        

    def deflatten(self):

        if not hasattr(self, "flat"): return
        if not self.flat: return
        self.flat.commit()
        

