#!/usr/bin/env python
# -*- encoding: utf-8 -*-
###############################################################################
#
# Exporting document to different formats
#
###############################################################################

import sys
import string
import re

from config import conf
from helpers import *

#------------------------------------------------------------------------------
# Escape sequences: NOTE: This table is similar to moeReadRTF (import)
# replacement table.
#------------------------------------------------------------------------------

escaped = {
    "rtf": {
        "å": r"\'e5",
        "Å": r"\'c5",
        "ä": r"\'e4",
        "Ä": r"\'c4",
        "ö": r"\'f6",
        "Ö": r"\'d6",
        '"': r"\'94",
        '~': r"\~",
    },
    "latex": {
        "ô": "o",
        "é": "e",
        "è": "e",
    },
}

def doEscape(fmt, s):
    s = s.encode("utf-8")
    for char in escaped[fmt].keys():
        s = s.replace(char, escaped[fmt][char])
    return s
    
###############################################################################
#
# Element wrappers
#
###############################################################################

#------------------------------------------------------------------------------
# Wrap element with prefix & postfix
#------------------------------------------------------------------------------

class ElemFmt:
    def __init__(self, prefix, postfix):
        self.prefix = prefix
        self.postfix = postfix

    def wrap(self, text, args = {}):
        return (self.prefix % args) + text + (self.postfix % args) + "\n"
    
#------------------------------------------------------------------------------
# Concate list with separator, and wrap it with prefix and postfix
#------------------------------------------------------------------------------

class ListFmt:
    def __init__(self, prefix, separator, postfix):
        self.prefix = prefix
        self.separator = separator
        self.postfix = postfix
    
    def wrap(self, texts):
        return \
            self.prefix + \
            string.join(texts, self.separator) + \
            self.postfix + "\n"
    

###############################################################################
#
# Exporting loop
#
###############################################################################

class Formatter(object):

    def __init__(self, title_elem):
    
        def getField(title, name):
            field = title.get(name)
            if field == None:
                field = title.find(name)
                if field == None: return None
                value = field.text
            else:
                value = field
            if value == "None": value = None
            return value
        
        def getFieldText(title, name):
            value = getField(title, name)
            if value == None: return ""
            return value
        
        self.doctype  = getField(title_elem, "type")
        self.toplevel = getField(title_elem, "opt_toplevel")
        self.chapters = getField(title_elem, "opt_chapters")
        self.prologue = getField(title_elem, "opt_prologue")
        self.epilogue = getField(title_elem, "opt_epilogue")

        self.title    = getFieldText(title_elem, "title")
        self.subtitle = getFieldText(title_elem, "subtitle")
        self.author   = getFieldText(title_elem, "author")
        self.website  = getFieldText(title_elem, "website")
        self.year     = getFieldText(title_elem, "year")
        self.status   = getFieldText(title_elem, "status")

        self.published= getFieldText(title_elem, "published")
        self.publisher= getFieldText(title_elem, "publisher")

        self.chapNum = 1
        self.partNum = 1

        self.fmtElemEmpty = ElemFmt("", "")
        self.fmtListEmpty = ListFmt("", "", "")

        if self.toplevel == "chapters":
            self.fmtContent = self.fmtChapters
        else:
            self.fmtContent = self.fmtParts            

    #--------------------------------------------------------------------------
    # General wrapping
    #--------------------------------------------------------------------------
    
    def wrap(self, elems, fmt):
        fmtElem, fmtList = fmt
        elems = map(lambda s: fmtElem.wrap(s), elems)
        return fmtList.wrap(elems)
    
    #--------------------------------------------------------------------------
    # Convert text to RTF paragraphs
    #--------------------------------------------------------------------------

    def fmtParagraphs(self, fmt, elem):
        if elem.find("content") == None: return ""
        text = elem.find("content").text
        if text == None: return ""

        if "formatting" in elem.attrib:
            elemfmt = elem.attrib["formatting"]
        else:
            elemfmt = "normal"

        paragraphs = string.split(text, "\n\n")
        paragraphs = map(lambda s: string.join(string.split(s)), paragraphs)
        paragraphs = map(string.strip, paragraphs)
        paragraphs = filter(lambda s: len(s), paragraphs)

        return self.wrap(
            paragraphs,
            self.getPgrFmt(elemfmt, fmt)
        )
    
    #--------------------------------------------------------------------------
    # Traverse subchapters
    #--------------------------------------------------------------------------

    def fmtSubchapters(self, fmt, elems):

        elems = filter(lambda e: e.get("included") == "True", elems)
    
        subchapters = []

        for elem in elems:
            text = [self.fmtParagraphs(fmt, elem)]

            childs = elem.find("childs")
            if childs != None: 
                text.append(self.fmtSubchapters(fmt, childs))
            
            text = filter(lambda t: len(t), text)
            
            subchapters = subchapters + text
        
        return self.wrap(subchapters, self.getSubchFmt(fmt))

    #--------------------------------------------------------------------------
    # Traverse chapters
    #--------------------------------------------------------------------------

    def fmtChapters(self, fmt, elems, chapters):
        
        if not elems: return ""
        
        fmtElem, fmtList = self.getChapterFmt(fmt, chapters)

        elems = filter(lambda e: e.get("included") == "True", elems)

        chapters = []

        for elem in elems:
            text = fmtElem.wrap(
                self.fmtSubchapters(fmt, [elem]),
                {
                    "name": elem.find("name").text,
                    "num": self.chapNum,
                }
            )
            
            chapters.append(text)
            self.chapNum += 1
            
        return fmtList.wrap(chapters)
     
    #--------------------------------------------------------------------------
    # Traverse parts
    #--------------------------------------------------------------------------

    def fmtParts(self, fmt, elems, chapters):

        fmtPart, fmtPartList = self.getPartFmt(fmt)
        
        elems = filter(lambda e: e.get("included") == "True", elems)

        parts = []

        for elem in elems:
            text = fmtPart.wrap(
                self.fmtChapters(fmt, elem.find("childs"), chapters),
                {
                    "name": elem.find("name").text,
                    "num":  int2roman(self.partNum),
                }
            )
            parts.append(text)
            self.partNum += 1
            
        return fmtPartList.wrap(parts)
        
    #--------------------------------------------------------------------------
    # Do export
    #--------------------------------------------------------------------------

    def doExport(self, fmt, contents):

        contents = filter(lambda e: e.get("included") == "True", contents)

        if self.prologue:
            prefix = self.fmtChapters(fmt, [contents[0]], self.prologue)
            prefix = self.getPrologueFmt(fmt).wrap(prefix)
            self.chapNum = 1
            contents = contents[1:]
        else:
            prefix = ""
        
        if self.epilogue:
            postfix = self.fmtChapters(fmt, [contents[-1]], self.epilogue)
            postfix = self.getEpilogueFmt(fmt).wrap(postfix)
            contents = contents[:-1]
        else:
            postfix = ""
        
        text = string.join([
            prefix,
            self.fmtContent(fmt, contents, self.chapters),
            postfix
        ],"")
        
        return self.getDocFmt(fmt).wrap(
            text,
            {
                "title": self.title,
                "subtitle": self.subtitle,
                "author": self.author,
                "year": self.year,
                "website": self.website,
                "status": self.status,
                "published": self.published,
                "publisher": self.publisher,
            }
        )
        
    #----------------------------------------------------------------------
    #----------------------------------------------------------------------

    def getPgrFmt(self, elemfmt, fmt):
        return {
            "rtf": (
                {
                    "normal": ElemFmt("", ""),
                    "bold": ElemFmt("{\B ", "}"),
                    "italic": ElemFmt("{\I ", "}"),
                }[elemfmt],
                ListFmt(
                    r"{\pard\sl-440{",
                    r"\par}" + "\n\n" + r"{\fi567 ",
                    r"\par}}" + "\n\n"
                ),
             ),
            "latex": (
                {
                    "normal": ElemFmt("", ""),
                    "bold": ElemFmt("\B{", "}"),
                    "italic": ElemFmt("\I{", "}"),
                }[elemfmt],
                ListFmt("", "\n\n", "")
             ),
        }[fmt]

    #----------------------------------------------------------------------

    def getSubchFmt(self, fmt):
        return {
            "rtf":   (ElemFmt("", ""), ListFmt("", "{\\par}\n\n", "")),
            "latex": (ElemFmt("", ""), ListFmt("", "\n\n\\psep ", "")),
        }[fmt]

    #----------------------------------------------------------------------

    def getShortChapterFmt(self, fmt, chapters):
        return {
            "separated": {
                "rtf": (
                    ElemFmt("", ""),
                    ListFmt("", r"{\sb480\qc\b * * *\par}" + "\n\n", "")
                ),
                "latex": (
                    ElemFmt("\n\n* * *\n\n", ""),
                    ListFmt("", "", "")
                ),
            },
            "unnamed": {
                "rtf": (
                    ElemFmt("", ""),
                    ListFmt("", "", "")
                ),
                "latex": (
                    ElemFmt("\\subchapter ", ""),
                    ListFmt("", "", "")
                ),
            },
            "numbered": {
                "rtf": (
                    ElemFmt(
                        r"{\sb720\sa240\b %(num)d.\par}" + "\n\n",
                        ""),
                    ListFmt("", "", "")
                ),
                "latex": (
                    ElemFmt(
                        "\\subchapter ",
                        ""),
                    ListFmt("", "", "")
                ),
            },
            "named": {
                "rtf": (
                    ElemFmt(
                        r"{\sb720\sa240\qc\b %(name)s\par}" + "\n\n",
                        ""),
                    ListFmt("", "", "")
                ),
                "latex": (
                    ElemFmt(
                        "\\subchapter{%(name)s} ",
                        ""),
                    ListFmt("", "", "")
                ),
            },
            "both": {
                "rtf": (
                    ElemFmt(
                        r"{\sb720\sa240\qc\b %(num)d. %(name)s\par}" + "\n\n",
                        ""),
                    ListFmt("", "", "")
                ),
                "latex": (
                    ElemFmt(
                        "\\subchapter{%(name)s} ",
                        ""),
                    ListFmt("", "", "")
                ),
            },
        }[chapters][fmt]

    def getLongChapterFmt(self, fmt, chapters):
        return {
            "separated": {
                "rtf": (
                    ElemFmt("", ""),
                    ListFmt("", r"{\sb480\qc\b * * *\par}" + "\n\n", "")
                ),
                "latex": (
                    ElemFmt("\n\n* * *\n\n", ""),
                    ListFmt("", "", "")
                ),
            },
            "numbered": {
                "rtf": (
                    ElemFmt(
                        r"{\pagebb\sb960\sa960\qc\b Luku %(num)d\par}" + "\n\n",
                        ""),
                    ListFmt("", "", "")
                ),
                "latex": (
                    ElemFmt(
                        r"\chapter{%(name)s}",
                        ""),
                    ListFmt("", "", "")
                ),
            },
            "named": {
                "rtf": (
                    ElemFmt(
                        r"{\pagebb\sb960\sa960\qc\fs28\b %(name)s\par}" + "\n\n",
                        ""),
                    ListFmt("", "", "")
                ),
                "latex": (
                    ElemFmt(
                        r"\chapter{%(name)s}",
                        ""),
                    ListFmt("", "", "")
                ),
            },
            "both": {
                "rtf": (
                    ElemFmt(
                        r"{\qc" +\
                        r"{\pagebb\sb480\sa480 Luku %(num)d\par}" +\
                        r"{\sa960\fs28\b %(name)s\par}}" + "\n\n",
                        ""),
                    ListFmt("", "", "")
                ),
                "latex": (
                    ElemFmt(
                        r"\chapter{%(name)s}",
                        ""),
                    ListFmt("", "", "")
                ),
            },
        }[chapters][fmt]

    def getChapterFmt(self, fmt, chapters):
        if chapters == None: chapters = "chapters"
        return {
            #"novel":      self.getLongChapterFmt,
            "longstory":  self.getLongChapterFmt,
            "shortstory": self.getShortChapterFmt,
        }[self.doctype](fmt, chapters)

    #----------------------------------------------------------------------

    def getPartFmt(self, fmt):
        return {
            "chapters": {
                "rtf": (None, None),
                "latex": (None, None),
            },
            "parts": {
                "rtf": (
                    ElemFmt(
                        r"{\qc\b\fs44" +\
                        r"{\pagebb\sb4800 Osa %(num)s\sa960\par}" +\
                        "%(name)s\par}",
                        ""),
                    ListFmt("", "\n\n", "\n\n")
                ),
                "latex": (
                    ElemFmt(
                        r"\part{%(name)s}{}",
                        ""),
                    ListFmt("", "", "")
                ),
            },
            "hiddenparts": {
                "rtf": (
                    ElemFmt("", ""),
                    ListFmt("", "", "")
                ),
                "latex": (
                    ElemFmt("", ""),
                    ListFmt("", "", "")
                ),
            },
        }[self.toplevel][fmt]
        
    #----------------------------------------------------------------------

    def getPrologueFmt(self, fmt):
        if self.toplevel == "chapters":
            return {
                "rtf":   self.fmtElemEmpty,
                "latex": self.fmtElemEmpty,
            }[fmt]
        else:
            return {
                "rtf":   self.fmtElemEmpty,
                "latex": ElemFmt("\\frontmatter", "\\mainmatter"),
            }[fmt]
    
    #----------------------------------------------------------------------

    def getEpilogueFmt(self, fmt):
        if self.toplevel == "chapters":
            return {
                "rtf":   self.fmtElemEmpty,
                "latex": self.fmtElemEmpty,
            }[fmt]
        else:
            return {
                "rtf":   self.fmtElemEmpty,
                "latex": ElemFmt("\\backmatter", ""),
            }[fmt]

    #----------------------------------------------------------------------

    def getDocFmt(self, fmt):
        if fmt == "rtf":
            if self.doctype == "shortstory":
                titlehdr = ""
                titleftr = ""
                titlepg  = ""
            else:
                titlehdr = r"{\sb4800\sa480 %(author)s\par}"
                titleftr = r"\page"
                titlepg  = r"\titlepg{\headerf}{\footerf}"
                
            return ElemFmt(string.join([
                r"{\rtf1\ansi",
                r"{\fonttbl\f0\froman\fcharset0 Times New Roman;}",
                r"{\info{\title %(title)s}{\author %(author)s}}",
                r"\deflang1035",
                r"\paperh16837\paperw11905",
                r"\margl1701\margr1701\margt851\margb1701",
                r"\sectd\sbknone",
                r"\pgwsxn11905\pghsxn16837",
                r"\marglsxn1701\margrsxn1701\margtsxn1701\margbsxn1701",
                r"\gutter0\ltrsect",
                r"\headery851",
                r"\lang1035\f0\fs24\fi0\li0\ri0\rin0\lin0"
                r"{\header",
                    r"\sl-440\tqr\tx8496 %(author)s: %(title)s",
                    r"\tab Sivu %s (%s)" % (
                        r"{\field{\*\fldinst PAGE}}",
                        r"{\field{\*\fldinst NUMPAGES}}"
                    ),
                    r"\par}",
                titlepg,
                r"{\qc",
                    titlehdr,
                    r"{\sa480\b\fs44 %(title)s\par}",
                    r"{\b\fs34 %(subtitle)s\par}",
                    titleftr + r"\par}",
                ], "\n"),
            "}")
        if fmt == "latex":
            if self.doctype == "longstory" and self.chapters in ["separated", "numbered"]:
            	doctype = "\\novel"
            else:
            	doctype = "\\%s" % self.doctype
            return ElemFmt(string.join([ 
                doctype,
                    r"{%(title)s}",
                    r"{%(subtitle)s}",
                    r"{%(status)s}",
                    r"{%(author)s}",
                    r"{%(website)s}",
                    r"{%(year)s}",
                "\\published",
                	r"{%(published)s}",
                	r"{%(publisher)s}",
                ],"\n"),
                ""
            )

###############################################################################
#
# Main
#
###############################################################################

def exportTree(root, fmt):
    elems = list(root)
    elems = filter(lambda e: e.get("included") == "True", elems)
    
    title   = filter(lambda e: e.tag == "TitleItem", elems)[0]
    content = filter(lambda e: e.tag != "TitleItem", elems)
    
    formatter = Formatter(title)

    return doEscape(fmt, formatter.doExport(fmt, content))
    
