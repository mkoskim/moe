#!/usr/bin/env python
###############################################################################
#
# Document Index View
#
###############################################################################

import string
import re

from moeGTK import *
from helpers import *
from moeItemDoc import DocItem

###############################################################################
#
# Document Index View
#
###############################################################################

class DocIndexView(gtk.TreeView):

    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------

    def __init__(self, document = None):
        super(DocIndexView,self).__init__()

        if document != None:
            self.set_model(document)

        self.percentages = False
    
        self.drag_source_set(
            gtk.gdk.BUTTON1_MASK,
            self.TARGETS,
            gtk.gdk.ACTION_MOVE
        )
        self.drag_source_set_icon_stock(gtk.STOCK_DND)
        
        #self.drag_dest_set(
        #    0,
        self.enable_model_drag_dest(
            self.TARGETS,
            gtk.gdk.ACTION_MOVE
        )
        
        #self.connect("drag-begin", self.cbDragBegin)
        
        #self.connect("drag-motion", self.cbDragMotion)
        #self.connect("drag-drop", self.cbDragDrop)
        
        #self.connect("drag-data-delete", self.cbDragDataDelete)
        self.connect("drag-data-get", self.cbDragDataGet)
        self.connect("drag-data-received", self.cbDragDataReceived)
        
        self.set_rules_hint(True)

        #self.set_reorderable(True)
        #self.columns_autosize()
        #self.set_fixed_height_mode(True)

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
    # Update view
    #--------------------------------------------------------------------------

    def update(self):
        
        def update_row(model, path, iter):
            model.row_changed(path, iter)
            
        self.get_model().foreach(update_row)

    #--------------------------------------------------------------------------
    #
    # Drag'n'drop
    #
    #--------------------------------------------------------------------------

    TARGETS = [
        ('Reorder', gtk.TARGET_SAME_WIDGET, 0),
    ]

    #--------------------------------------------------------------------------
    #
    # Drag'n'drop (enable_model_drag_XXX variants)
    #
    #--------------------------------------------------------------------------

    def cbDragBegin(self, view, ctx):
        #print "CB drag-begin", locals()
        #self.drag_source_set_icon_stock(gtk.STOCK_DND)
        #view.drag_source_set_icon_pixbuf(self.dnd_pixbuf)
        #ctx.set_icon_pixbuf(self.dnd_pixbuf, 16, 16)
        #ctx.set_icon_stock(gtk.STOCK_DND, 10, 10)
        
        return True

    def cbDragMotion(self, view, ctx, x, y, time):
        #print "CB drag-motion", locals()
        ctx.drag_status(gtk.gdk.ACTION_COPY, time)
        return True
        
    def cbDragDataDelete(self, view, ctx):
        #print "CB drag-data-delete", locals()
        return True
    
    def cbDragDrop(self, view, ctx, x, y, etime):
        print "CB drag-drop", locals()
        return False
    
    def cbDragDataGet(self, treeview, context, selection, targetid, etime):
        #print "CB drag-data-get", locals()
        
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        data = model.get_string_from_iter(iter)
        selection.set(selection.target, 8, data)
        return True
            
    def cbDragDataReceived(self, treeview, context, x, y, selection, info, etime):
        #print "CB drag-data-received", locals()
        model = treeview.get_model()

        #----------------------------------------------------------------------
        # Source item
        #----------------------------------------------------------------------
        
        src_iter = model.get_iter_from_string(selection.data)
        src_item = model.get_value(src_iter, 0)
        
        if src_item.sticky:
            print "Source is sticky"
            context.finish(False, False, etime)
            return True
            
        #----------------------------------------------------------------------
        # Destination
        #----------------------------------------------------------------------

        drop_info = treeview.get_dest_row_at_pos(x,y)
        if drop_info == None:
            path = model.get_path(model.iter_last())
            position = gtk.TREE_VIEW_DROP_AFTER
        else:
            path, position = drop_info

        dst_iter = model.get_iter(path)            
        dst_item = model.get_value(dst_iter, 0)

        if src_item == dst_item:
            print "Nothing to move"
            context.finish(False, False, etime)
            return True

        #----------------------------------------------------------------------
        # Is it drop in?
        #----------------------------------------------------------------------

        try_drop_in = False
        if position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
            try_drop_in = True
            position = gtk.TREE_VIEW_DROP_BEFORE
        elif position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
            try_drop_in = True
            position = gtk.TREE_VIEW_DROP_AFTER

        #----------------------------------------------------------------------
        # Do it
        #----------------------------------------------------------------------
        
        can_drop = (dst_item.level != 0)
        
        #can_drop = \
        #    (dst_item.level != 0) and \
        #    ((dst_item.level == -1) or (dst_item.level > src_item.level))
        
        if try_drop_in and can_drop:
            model.drop_in(src_iter, dst_iter)
        elif position == gtk.TREE_VIEW_DROP_BEFORE:
            if dst_item.keep_first:
                context.finish(False, False, etime)
                return True
            model.move_before(src_iter, dst_iter)
        elif position == gtk.TREE_VIEW_DROP_AFTER:
            if dst_item.keep_last:
                context.finish(False, False, etime)
                return True
            model.move_after(src_iter, dst_iter)

        if context.action == gtk.gdk.ACTION_MOVE:
            context.finish(True, False, etime)

        model.renum()
        return True
        
    #--------------------------------------------------------------------------
    # Callbacks to get column information
    #--------------------------------------------------------------------------

    def dfColIncluded(self, tvcol, cell, model, index):
        item = model.get_value(index, 0)
        cell.set_property("active", item.included)

    #--------------------------------------------------------------------------

    def dfColWords(self, tvcol, cell, model, index):
        item = model.get_value(index, 0)
        words = item.getWordCount()
        if words == None:
            cell.set_property("text", "-")
        elif self.percentages:
            total = int(self.get_model().title.getWordCount())
            if total == 0:
                cell.set_property("text", "-")
            else:
                cell.set_property("text", str(int(100.0*words/total)) + " %")
        else:
            cell.set_property("text", str(words))
        pass
            
    #--------------------------------------------------------------------------

    def dfColNumber(self, tvcol, cell, model, index):
        item = model.get_value(index, 0)
        cell.set_property("text", item.number)
    
    #--------------------------------------------------------------------------

    def dfColSeparator(self, tvcol, cell, model, index):
        item = model.get_value(index, 0)
        separator = item.getSeparator()
        cell.set_property("text", separator)
        #if separator == None:
        #    path = model.get_path(index)
        #    if len(path) == 1:
        #        cell.set_property("text", "Chapter")
        #    else:
        #        cell.set_property("text", "")
        #else:
        #    cell.set_property("text", separator)
        pass
            
    #--------------------------------------------------------------------------

    def dfColName(self, tvcol, cell, model, index):
        item = model.get_value(index, 0)
        cell.set_property("text", item.getName())
        pass

    #--------------------------------------------------------------------------

    def dfColDescription(self, tvcol, cell, model, index):
        item = model.get_value(index, 0)
        #if item.__class__.__name__ == "SceneItem":
        if hasattr(item, "elements") and ("synopsis" in item.elements):
            text = item.elements["synopsis"].get_content()
        else:
            text = ""
        cell.set_property("text", text)
        
    #--------------------------------------------------------------------------

    def dfColSceneDescription(self, tvcol, cell, model, index):
        item = model.get_value(index, 0)
        if item.included and item.__class__.__name__ == "SceneItem":
        #if hasattr(item, "elements") and ("description" in item.elements):
            text = item.elements["synopsis"].get_content()
        else:
            text = ""
        cell.set_property("text", text)
        
    #--------------------------------------------------------------------------

    def dfColEmpty(self, tvcol, cell, model, index):
        cell.set_property("text","")


