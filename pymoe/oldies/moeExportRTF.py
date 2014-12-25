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
    "å": r"\'e5",
    "Å": r"\'c5",
    "ä": r"\'e4",
    "Ä": r"\'c4",
    "ö": r"\'f6",
    "Ö": r"\'d6",
    '"': r"\'94",
    '~': r"\~",
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
        epilogue = None
    ):
    
        #----------------------------------------------------------------------

        self.fmtElemEmpty = self.ElemFmt("", "")
        self.fmtListEmpty = self.ListFmt("", "", "")

        #----------------------------------------------------------------------

        self.fmtPgr     = self.ElemFmt("", "")
        self.fmtPgrList = self.ListFmt(
            r"{\pard\sl-440{",
            r"\par}" + "\n\n" + r"{\fi567 ",
            r"\par}}" + "\n\n"
        )

        #----------------------------------------------------------------------

        self.fmtSubch     = self.ElemFmt("", "")
        self.fmtSubchList = self.ListFmt("", r"{\par}" + "\n\n", "")

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

        self.fmtRTF = self.ElemFmt(
            string.join([
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
                ], "\n"),
            "}")

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
            prefix = self.fmtChapters([contents[0]], self.prologue)
            self.chapNum = 1
            contents = contents[1:]
        else:
            prefix = ""
        
        if self.epilogue:
            postfix = self.fmtChapters([contents[-1]], self.epilogue)
            contents = contents[:-1]
        else:
            postfix = ""
        
        text = string.join([
            prefix,
            self.fmtContent(contents, self.chapters),
            postfix
        ],"")
        
        return self.fmtRTF.wrap(
            text,
            {
                "title": title.find("title").text,
                "subtitle": title.find("subtitle").text,
                "author": title.find("author").text,
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
                self.ElemFmt("", ""),
                self.ListFmt("", r"{\sb480\qc\b * * *\par}" + "\n\n", "")
            ),
            "unnamed": (
                self.ElemFmt("", ""),
                self.ListFmt("", "", "")
            ),
            "numbered": (
                self.ElemFmt(
                    r"{\sb720\sa240\b %(num)d.\par}" + "\n\n",
                    ""),
                self.ListFmt("", "", "")
            ),
            "named": (
                self.ElemFmt(
                    r"{\sb720\sa240\qc\b %(name)s\par}" + "\n\n",
                    ""),
                self.ListFmt("", "", "")
            ),
            "both": (
                self.ElemFmt(
                    r"{\sb720\sa240\qc\b %(num)d. %(name)s\par}" + "\n\n",
                    ""),
                self.ListFmt("", "", "")
            ),
        }[chapters]
    
    #--------------------------------------------------------------------------
    #
    #--------------------------------------------------------------------------
    
    def __init__(self,
        subtitle = False,
        contains = None,
        chapters = None,
        prologue = False,
        epilogue = False,
    ):

        super(FmtShortStory,self).__init__(
            chapters = chapters,
            prologue = prologue,
            epilogue = epilogue,
        )
        
        #----------------------------------------------------------------------

        if subtitle:
            subtitle = r"{\sb240\b\fs28 %(subtitle)s\par}"
        else:
            subtitle = ""
            
        self.fmtRTF.prefix += string.join([
            r"{\qc",
                r"{\b\fs32 %(title)s\par}",
                subtitle,
            r"{\sa480\par}}",
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
                    r"{\pagebb\sb960\sa960\qc\b Luku %(num)d\par}" + "\n\n",
                    ""),
                self.ListFmt("", "", "")
            ),
            "named": (
                self.ElemFmt(
                    r"{\pagebb\sb960\sa960\qc\fs28\b %(name)s\par}" + "\n\n",
                    ""),
                self.ListFmt("", "", "")
            ),
            "both": (
                self.ElemFmt(
                    r"{\qc{\pagebb\sb480\sa480 Luku %(num)d\par}{\sa960\fs28\b %(name)s\par}}" + "\n\n",
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
                    r"{\qc\b\fs44{\pagebb\sb4800 Osa %(num)s\sa960\par} %(name)s\par}",
                    ""),
                self.ListFmt("", "\n\n", "\n\n")
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
        subtitle = False,
        contains = "chapters",
        chapters = "numbered",
        prologue = False,
        epilogue = False,
    ):

        super(FmtLongStory, self).__init__(
            contains = contains,
            chapters = chapters,
            prologue = prologue,
            epilogue = epilogue,
        )

        #----------------------------------------------------------------------

        if subtitle:
            subtitle = r"{\b\fs44 %(subtitle)s\par}"
        else:
            subtitle = ""

        self.fmtRTF.prefix += string.join([
            r"\titlepg{\headerf}{\footerf}",
            r"{\qc",
                r"{\sb4800\sa480 %(author)s\par}",
                r"{\sa480\b\fs44 %(title)s\par}",
                subtitle,
            r"\page}" + "\n\n",
            ], "\n")

        #----------------------------------------------------------------------

        self.fmtPart, self.fmtPartList = self.getPartFmt(contains)

###############################################################################
#
# Formatter
#
###############################################################################

def exportRTF(root):

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

    opt_toplevel = getFormattingField("opt_toplevel")
    opt_chapters = getFormattingField("opt_chapters")
    opt_prologue = getFormattingField("opt_prologue")
    opt_epilogue = getFormattingField("opt_epilogue")
    
    formatter = {
        "novel": FmtLongStory,
        "longstory": FmtLongStory,
        "shortstory": FmtShortStory,
    }[doctype](
        subtitle = title.find("subtitle").text,
        contains = opt_toplevel,
        chapters = opt_chapters,
        prologue = opt_prologue,
        epilogue = opt_epilogue,
    )

    return escape(formatter.doExport(title, content))
    
