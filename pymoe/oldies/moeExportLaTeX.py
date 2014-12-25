#!/usr/bin/env python
# -*- encoding: utf-8 -*-
###############################################################################
#
# Exporting document as text
#
###############################################################################

import sys
import string
from helpers import int2roman

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

escaped = {
#    "å": r"\'e5",
#    "Å": r"\'c5",
#    "ä": r"\'e4",
#    "Ä": r"\'c4",
#    "ö": r"\'f6",
#    "Ö": r"\'d6",
#    '"': r"\'94",
}

def escape(s):
    s = s.encode("utf-8")
    for char in escaped.keys():
        s = s.replace(char, escaped[char])
    return s
    
###############################################################################
###############################################################################
#
# Formatting:
# - Prefix and postfix for every element
# - Prefix, separator and postfix for every list
#
###############################################################################
###############################################################################

class Formatter(object):

    #--------------------------------------------------------------------------
    # Wrap element with prefix & postfix
    #--------------------------------------------------------------------------
    
    class ElemFmt:
        def __init__(self, prefix, postfix):
            self.prefix = prefix
            self.postfix = postfix

        def wrap(self, text, args = {}):
            return (self.prefix % args) + text + (self.postfix % args) + "\n"
        
    #--------------------------------------------------------------------------
    # Concate list with separator, and wrap it with prefix and postfix
    #--------------------------------------------------------------------------
    
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
        
    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------
    
    def __init__(self,
        contains = "chapters",
        chapters = None,
        prologue = None,
        epilogue = None):
    
        #----------------------------------------------------------------------

        self.fmtElemEmpty = self.ElemFmt("", "")
        self.fmtListEmpty = self.ListFmt("", "", "")

        #----------------------------------------------------------------------

        self.fmtPgr     = self.ElemFmt("", "")
        self.fmtPgrList = self.ListFmt("", "\n\n", "")

        #----------------------------------------------------------------------

        self.fmtSubch     = self.ElemFmt("", "")
        self.fmtSubchList = self.ListFmt("", "\n\n---\n\n", "")

        self.chapNum = 1
        self.partNum = 1

        #----------------------------------------------------------------------

        self.chapters = chapters
        self.prologue = prologue
        self.epilogue = epilogue
        
        if contains == "chapters":
            self.fmtContent = self.fmtChapters
        else:
            self.fmtContent = self.fmtParts
            
        #----------------------------------------------------------------------

        self.fmtDoc = self.ElemFmt("", "")

    #--------------------------------------------------------------------------
    # Convert text to RTF paragraphs
    #--------------------------------------------------------------------------

    def fmtParagraphs(self, elem):
        if elem.find("content") == None: return ""
        text = elem.find("content").text
        if text == None: return ""

        paragraphs = string.split(text, "\n\n")
        paragraphs = map(lambda s: string.join(string.split(s)), paragraphs)
        paragraphs = map(string.strip, paragraphs)
        paragraphs = filter(lambda s: len(s), paragraphs)
        
        paragraphs = map(lambda s: self.fmtPgr.wrap(s), paragraphs)
        return self.fmtPgrList.wrap(paragraphs)
    
    #--------------------------------------------------------------------------
    # Traverse subchapters
    #--------------------------------------------------------------------------

    def fmtSubchapters(self, elems):

        elems = filter(lambda e: e.get("included") == "True", elems)
    
        subchapters = []

        for elem in elems:
            text = [self.fmtParagraphs(elem)]

            childs = elem.find("childs")
            if childs != None: 
                text.append(self.fmtSubchapters(childs))
            
            text = filter(lambda t: len(t), text)
            
            subchapters = subchapters + text
        
        subchapters = map(
            lambda s: self.fmtSubch.wrap(s),
            subchapters
        )
        return self.fmtSubchList.wrap(subchapters)

    #--------------------------------------------------------------------------
    # Traverse chapters
    #--------------------------------------------------------------------------

    def fmtChapters(self, elems, fmt):
        
        fmtElem, fmtList = self.getChapterFmt(fmt)

        if elems == None: return ""
        
        elems = filter(lambda e: e.get("included") == "True", elems)

        chapters = []

        for elem in elems:
            text = fmtElem.wrap(
                self.fmtSubchapters([elem]),
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

    def fmtParts(self, elems, chapters):

        elems = filter(lambda e: e.get("included") == "True", elems)

        parts = []

        for elem in elems:
            text = self.fmtPart.wrap(
                self.fmtChapters(elem.find("childs"), chapters),
                {
                    "name": elem.find("name").text,
                    "num":  int2roman(self.partNum),
                }
            )
            parts.append(text)
            self.partNum += 1
            
        return self.fmtPartList.wrap(parts)
        
    #--------------------------------------------------------------------------
    # Do export
    #--------------------------------------------------------------------------

    def doExport(self, title, contents):

        contents = filter(lambda e: e.get("included") == "True", contents)

        if self.prologue:
            prefix = \
                "\\frontmatter\n" + \
                self.fmtChapters([contents[0]], self.prologue) + \
                "\\mainmatter\n"
            self.chapNum = 1
            contents = contents[1:]
        else:
            prefix = ""
        
        if self.epilogue:
            postfix = \
                "\\backmatter\n" + \
                self.fmtChapters([contents[-1]], self.epilogue)
            contents = contents[:-1]
        else:
            postfix = ""
        
        text = string.join([
            prefix,
            self.fmtContent(contents, self.chapters),
            postfix
        ],"")
        
        def getElement(name):
            elem = title.find(name).text
            if elem == None: return ""
            return elem
        
        return self.fmtDoc.wrap(
            text,
            {
                "title":    getElement("title"),
                "subtitle": getElement("subtitle"),
                "author":   getElement("author"),
                "website":  getElement("website"),
                "year":     getElement("year"),
                "status":   getElement("status"),
            }
        )

###############################################################################
#
# Short story formatter
#
###############################################################################

class FmtShortStory(Formatter):

    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------
    
    def getChapterFmt(self, chapters):
        if chapters == None: chapters = "separated"
        return {
            "separated": (
                self.ElemFmt("\n\n* * *\n\n", ""),
                self.ListFmt("", "", "")
            ),
            "unnamed": (
                self.ElemFmt("\\subchapter ", ""),
                self.ListFmt("", "", "")
            ),
            "numbered": (
                self.ElemFmt(
                    "\\subchapter ",
                    ""),
                self.ListFmt("", "", "")
            ),
            "named": (
                self.ElemFmt(
                    "\\subchapter[%(name)s] ",
                    ""),
                self.ListFmt("", "", "")
            ),
            "both": (
                self.ElemFmt(
                    "\\subchapter[%(name)s] ",
                    ""),
                self.ListFmt("", "", "")
            ),
        }[chapters]
    
    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------
    
    def __init__(self,
        contains = None,
        chapters = None,
        prologue = False,
        epilogue = False):

        super(FmtShortStory,self).__init__(
            chapters = chapters,
            prologue = prologue,
            epilogue = epilogue
        )
        
        #----------------------------------------------------------------------

        self.fmtDoc.prefix += string.join([
            r"\shortstory",
                r"{%(title)s}",
                r"{%(subtitle)s}",
                r"{%(status)s}",
                r"{%(author)s}",
                r"{%(website)s}",
                r"{%(year)s}",
            ], "\n")


###############################################################################
#
# Long story formatter
#
###############################################################################

class FmtLongStory(Formatter):

    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------
    
    def getChapterFmt(self, chapters):
        if chapters == None: chapters = "numbered"
        return {
            "numbered": (
                self.ElemFmt(
                    r"\chapter{%(name)s}",
                    ""),
                self.ListFmt("", "", "")
            ),
            "named": (
                self.ElemFmt(
                    r"\chapter{%(name)s}",
                    ""),
                self.ListFmt("", "", "")
            ),
            "both": (
                self.ElemFmt(
                    r"\chapter{%(name)s}",
                    ""),
                self.ListFmt("", "", "")
            ),
        }[chapters]

    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------

    def getPartFmt(self, parts):
        return {
            "chapters": (None, None),
            "parts": (
                self.ElemFmt(
                    r"\parttitlepage{%(name)s}{}",
                    ""),
                self.ListFmt("", "", "")
            ),
            "hiddenparts": (
                self.ElemFmt("", ""),
                self.ListFmt("", "", "")
            )
        }[parts]
        
    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------
    
    def __init__(self,
        contains = "chapters",
        chapters = "numbered",
        prologue = False,
        epilogue = False):

        super(FmtLongStory, self).__init__(
            contains = contains,
            chapters = chapters,
            prologue = prologue,
            epilogue = epilogue
        )

        #----------------------------------------------------------------------

        self.fmtDoc.prefix += string.join([
            r"\longstory",
                r"{%(title)s}",
                r"{%(subtitle)s}",
                r"{%(status)s}",
                r"{%(author)s}",
                r"{%(website)s}",
                r"{%(year)s}",
            ], "\n")

        #----------------------------------------------------------------------

        self.fmtPart, self.fmtPartList = self.getPartFmt(contains)

###############################################################################
#
# Formatter
#
###############################################################################

def exportLaTeX(root):

    elems = list(root)
    elems = filter(lambda e: e.get("included") == "True", elems)
    
    title   = filter(lambda e: e.tag == "TitleItem", elems)[0]
    content = filter(lambda e: e.tag != "TitleItem", elems)
    
    doctype = title.find("type").text

    def getFormattingField(name):
        field = title.find(name)
        if field == None: return None
        value = field.text
        if value == "None": value = None
        return value

    toplevel = getFormattingField("toplevel")
    chapters = getFormattingField("chapters")
    prologue = getFormattingField("prologue")
    epilogue = getFormattingField("epilogue")
        
    formatter = {
        "longstory": FmtLongStory,
        "shortstory": FmtShortStory,
    }[doctype](
        contains = toplevel,
        chapters = chapters,
        prologue = prologue,
        epilogue = epilogue
    )

    return escape(formatter.doExport(title, content))
    
