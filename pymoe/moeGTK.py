#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
# GTK
#
###############################################################################

import sys
import pygtk
pygtk.require('2.0')
import gtk, gobject
import pango

#print>>sys.stderr, "PyGTK version:", gtk.pygtk_version
#print>>sys.stderr, "GTK version..:", gtk.gtk_version

import string
import re

import extformats
from config import conf
from helpers import *
from UndoableBuffer import UndoableBuffer

###############################################################################
#
# GTK Helpers
#
###############################################################################

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------

def processGtkMessages():
    while gtk.events_pending():
        gtk.main_iteration()        

###############################################################################
#
# Widgets and such
#
###############################################################################

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

reMultiSpaces = re.compile(r"\s+")

class TextBuf(UndoableBuffer):

    def __init__(self, content = None):
        super(TextBuf,self).__init__()
        if content: self.set_content(content)

    def get_content(self):
        return string.strip(self.get_text(
            self.get_start_iter(),
            self.get_end_iter()
        ))

    def set_content(self, content):
        replaces = {
            "\r": "",
            "“": '"',
            "”": '"',
            "’": "'",
            "–": "-",
            "…": "...",
        }
        
            
        if content == None:
            super(TextBuf,self).set_text("")
        elif isinstance(content, TextBuf):
            content = content.get_content()
        else:
            for char in replaces.keys():
                content = content.replace(char,replaces[char])
                
            global reMultiSpaces
            content = string.split(content, "\n\n")
            for i in range(len(content)):
                content[i] = string.strip(content[i])
                content[i].replace("\n", " ")
                content[i] = reMultiSpaces.sub(" ", content[i])
            content = string.join(content, "\n\n")
            
            super(TextBuf,self).set_text(content)
        self.place_cursor(self.get_start_iter())
        self.undo_stack = []
        self.redo_stack = []
        
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class TextCombo(gtk.Frame):

    def __init__(self, items):
        super(TextCombo,self).__init__()
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.keys   = map(lambda i: i[0], items)
        self.values = map(lambda i: i[1], items)
        
        self.combo = gtk.combo_box_new_text()
        for value in self.values:
            self.combo.append_text(value)
        self.combo.set_active(0)
        self.add(self.combo)
        
    def get_content(self):
        return self.keys[self.combo.get_active()]
        
    def set_content(self, value):
        index = self.keys.index(value)
        self.combo.set_active(index)

    def connect(self, signal, callback):
        self.combo.connect(signal, callback)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class ToolBar(gtk.Toolbar):        

    class RadioButton(gtk.RadioToolButton):
        groups = {}
        
        def __init__(self, label, group, callback, tooltip):
            if group not in self.groups:
                self.groups[group] = [ self, { } ]
                leader = self
            else:
                leader = self.groups[group][0]
            self.groups[group][1][label] = self
            super(ToolBar.RadioButton,self).__init__(leader)
            #self.set_icon_widget(gtk.Button(label))
            self.set_label_widget(gtk.Label(label))
            self.tooltip = tooltip
            self.connect("clicked", callback)
            
    class CheckButton(gtk.ToggleToolButton):
        def __init__(self, label, toggled, callback, tooltip):
            super(ToolBar.CheckButton,self).__init__()
            #self.set_icon_widget(gtk.Button(label))
            self.set_label_widget(gtk.Label(label))
            self.connect("clicked", callback)
            self.set_active(toggled)
            self.tooltip = tooltip
    
    class Button(gtk.ToolButton):
        def __init__(self, label, callback, tooltip):
            #super(ToolBar.Button,self).__init__(gtk.Button(label))
            super(ToolBar.Button,self).__init__()
            self.set_label_widget(gtk.Label(label))
            self.connect("clicked", callback)
            self.tooltip = tooltip

    class Separator(gtk.SeparatorToolItem):
        tooltip = None
        pass

    def __init__(self, *buttons):
        super(ToolBar,self).__init__()
        self.set_style(gtk.TOOLBAR_TEXT)
        for button in buttons:
            self.insert(button, -1) #button.tooltip, None)


###############################################################################
#
# Functions for creating widgets
#
###############################################################################

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def createLabel(text):
    label = gtk.Label(text)
    hbox = gtk.HBox()
    hbox.pack_start(label, False, False)
    vbox = gtk.VBox()
    vbox.pack_start(hbox, False, False)
    vbox.grabber = label
    return vbox

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

class _TextView(gtk.TextView):

    def __init__(self, buf):
        super(_TextView,self).__init__()
        self.set_buffer(buf)
        
    def set_buffer(self, buf):
        super(_TextView,self).set_buffer(buf)
        if hasattr(buf, "undo"): self.undo = buf.undo
        if hasattr(buf, "redo"): self.redo = buf.redo

def createTextView(
        buf, 
        pad_leftright = 10,
        pad_topbottom = 5,
        justify = gtk.JUSTIFY_LEFT,
        font = None,
        width = -1,
        height = -1,
        bgcolor = None,
        fgcolor = None,
    ):
    textview = _TextView(buf)
    
    textview.set_justification(justify)
    textview.set_accepts_tab(False)
    #textview.connect("move-cursor", trace_event)
    #textview.connect("set-scroll-adjustments", trace_event)
    
    textview.set_wrap_mode(gtk.WRAP_WORD)
    textview.set_size_request(width, height)
    
    textview.set_border_window_size(gtk.TEXT_WINDOW_LEFT, pad_leftright)
    textview.set_border_window_size(gtk.TEXT_WINDOW_RIGHT, pad_leftright)
    textview.set_border_window_size(gtk.TEXT_WINDOW_TOP, pad_topbottom)
    textview.set_border_window_size(gtk.TEXT_WINDOW_BOTTOM, pad_topbottom)
    
    if bgcolor:
        textview.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(bgcolor))
        textview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(bgcolor))
    else:
        textview.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#FFFFFF"))
    
    if fgcolor: textview.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse(fgcolor))
    
    if font != None:
        font = pango.FontDescription(font)
        textview.modify_font(font)

    return textview
    
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def createTextBox(
        buf, 
        border = gtk.SHADOW_IN,
        border_width = 1,
        pad_leftright = 1,
        pad_topbottom = 2,
        justify = gtk.JUSTIFY_LEFT,
        font = None,
        bgcolor = None,
        fgcolor = None,
    ):

    textview = createTextView(
        buf,
        pad_leftright = pad_leftright,
        pad_topbottom = pad_topbottom,
        justify = justify,
        font = font,
        bgcolor = bgcolor,
        fgcolor = fgcolor,
    )

    frame = gtk.Frame()
    frame.add(textview)
    frame.set_shadow_type(border)
    frame.set_border_width(border_width)
    frame.get_buffer = textview.get_buffer
    frame.grabber = textview
    return frame

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def createEntry(
        buf,
        border = gtk.SHADOW_IN,
        border_width = 1,
        pad_leftright = 1,
        pad_topbottom = 2,
        justify = gtk.JUSTIFY_LEFT,
        font = None,
        bgcolor = None,
        fgcolor = None,
    ):
    return createTextBox(
        buf,
        border = border,
        border_width = border_width,
        pad_leftright = pad_leftright,
        pad_topbottom = pad_topbottom,
        justify = justify,
        font = font,
        bgcolor = bgcolor, fgcolor = fgcolor,
    )

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def createScrolledTextBox(
        buf,
        border = gtk.SHADOW_IN,
        border_width = 1,
        pad_leftright = 1,
        pad_topbottom = 2,
        justify = gtk.JUSTIFY_LEFT,
        font = None,
        bgcolor = None, fgcolor = None,        
    ):

    textview = createTextView(
        buf,
        pad_leftright = pad_leftright,
        pad_topbottom = pad_topbottom,
        justify = justify,
        font = font,
        bgcolor = bgcolor, fgcolor = fgcolor,
    )

    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    
    sw.add(textview)
    sw.set_shadow_type(border)
    sw.set_border_width(border_width)

    sw.grabber = textview
    return sw
    
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def createExpander(label, widget, padding = 0):
    frame = gtk.Expander()
    frame.add(widget)

    if label != None:
        label = gtk.Label(label)
        label.set_use_underline(True)
        label.set_mnemonic_widget(widget.mnemonicWidget)
        frame.set_label_widget(label)
    return frame
    
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def createFrame(label, widget, expander = False, expanded = True, 
    border_width = 1
):
    if expander:
        frame = gtk.Expander()
        frame.set_expanded(expanded)
    else:
        frame = gtk.Frame()

    frame.add(widget)

    if label != None:
        label = gtk.Label(label)
        label.set_use_underline(True)
        label.set_mnemonic_widget(widget.grabber)
        frame.set_label_widget(label)

    if border_width == 0:
        frame.set_shadow_type(gtk.SHADOW_NONE)
    else:
        frame.set_border_width(border_width)
    return frame
    
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def createEditGrid(label, fields, expander = False, expanded = True):    
    table = gtk.Table(len(fields), 2)
    table.grabber = fields[0][1]
    for lineno in range(len(fields)):
        if len(fields[lineno]) == 1:
            table.attach(
                fields[lineno][0],
                0,2,
                lineno, lineno+1,
                gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL,
                5, 5,
            )
            continue
            
        prompt, widget = fields[lineno][0], fields[lineno][1]

        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(prompt), False, False)
        vbox = gtk.VBox()
        vbox.pack_start(hbox, False, False)
        
        table.attach(
            vbox,
            0, 1,
            lineno, lineno+1,
            gtk.FILL, gtk.FILL,
            5, 5
        )
        table.attach(
            widget,
            1,2,
            lineno, lineno+1,
            gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL,
            5, 5,
        )
    if label != None:
        return createFrame(label, table, expander, expanded)
    else:
        return table

###############################################################################
#
# Message dialogs
#
###############################################################################

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def userConfirm(action, default_response = gtk.RESPONSE_YES):
    question = gtk.MessageDialog(
        conf.mainwnd,
        gtk.DIALOG_MODAL,
        gtk.MESSAGE_WARNING,
        gtk.BUTTONS_YES_NO,
        action
    )
    question.set_default_response(default_response)
    answer = question.run()
    question.destroy()
    return answer == gtk.RESPONSE_YES
    
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def userInform(action, msgtype = gtk.MESSAGE_INFO):
    question = gtk.MessageDialog(
        conf.mainwnd,
        gtk.DIALOG_MODAL,
        msgtype,
        gtk.BUTTONS_OK,
        action
    )
    answer = question.run()
    question.destroy()

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def userSaveDiscardCancel(action):
    question = gtk.MessageDialog(
        conf.mainwnd,
        gtk.DIALOG_MODAL,
        gtk.MESSAGE_WARNING,
        gtk.BUTTONS_NONE,
        action
    )
    question.add_buttons(
        gtk.STOCK_SAVE, gtk.RESPONSE_YES,
        "_Discard", gtk.RESPONSE_NO,
        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL
    )
    answer = question.run()
    question.destroy()
    return answer            

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def _addFileFilter(dialog, patterns):
    if patterns == None: return
    for pattern in patterns:
        filefilter = gtk.FileFilter()
        filefilter.set_name(pattern[0])
        for wildcard in pattern[1]:
            filefilter.add_pattern(wildcard)
        dialog.add_filter(filefilter)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def userLoadFile(action, patterns = [ ["All files", [ "*.*"]] ]):
    dialog = gtk.FileChooserDialog(
        action,
        conf.mainwnd,
        gtk.FILE_CHOOSER_ACTION_OPEN,
        (
            gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        )
    if patterns != None: _addFileFilter(dialog, patterns)
    dialog.set_default_response(gtk.RESPONSE_OK)
    answer = dialog.run()
    filename = dialog.get_filename()
    dialog.destroy()
    
    if answer == gtk.RESPONSE_OK:
        return filename
    else:
        return None

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def userSaveFile(action, suggestion = None, patterns = None):
    dialog = gtk.FileChooserDialog(
        action,
        conf.mainwnd,
        gtk.FILE_CHOOSER_ACTION_SAVE,
        (
            gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        )
    _addFileFilter(dialog, patterns)
    dialog.set_default_response(gtk.RESPONSE_OK)
    
    if suggestion: dialog.set_current_name(suggestion)
        
    if hasattr(dialog, "set_do_overwrite_confirmation"):
        dialog.set_do_overwrite_confirmation(True)

    answer = dialog.run()
    filename = dialog.get_filename()
    dialog.destroy()
    
    if answer == gtk.RESPONSE_OK:
        return filename
    else:
        return None
    
