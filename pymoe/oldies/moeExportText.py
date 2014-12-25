#!/usr/bin/env python
###############################################################################
#
# Exporting document as text
#
###############################################################################

import sys
import string

def travel(fout, root, level = 0):
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def printout(*strs):
        for s in strs:
            print>>fout, s.encode("utf-8"),
        print>>fout

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def center(text):
        if text == None: return ""
        pad = (80 - len(text))/2
        return (" " * pad) + text
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def stretch(line, width = 80):
        line = string.split(line)
        words = len(line)
        space_pos = words - 1
        if space_pos < 2:
            return string.join(line, " ")
        missing = width - len(string.join(line,""))
        spaces = int(missing/space_pos)
        extras = missing - spaces*space_pos
        if extras == 0:
            return string.join(line, " " * spaces)
        else:
            return\
                string.join(line[:extras], " " * (spaces+1)) +\
                (" " * spaces) + \
                string.join(line[extras:], " " * spaces)

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def justify(text, width = 80):
        words = text.split()
        lines = [words[0]]
        for word in words[1:]:
            if len(lines[-1]) + len(word) + 1 >= width:
                #lines[-1] = stretch(lines[-1], width)
                lines.append(word)
            else:
                lines[-1] = lines[-1] + " " + word
        lines = string.join(lines,"\n")
        return lines

    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def paragraphs(text, width = 80):
        paragraphs = string.split(text, "\n\n")
        paragraphs = map(lambda s: string.join(string.split(s)), paragraphs)
        paragraphs = map(string.strip, paragraphs)
        paragraphs = filter(lambda s: len(s), paragraphs)
        paragraphs = map(lambda s: justify(s,width), paragraphs)
        return string.join(paragraphs, "\n\n")
        
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    first = True
    for elem in root:
        if elem.get("included") != "True":
            continue
            
        if elem.tag == "TitleItem":
            printout()
            printout()
            printout(center(elem.find("author").text))
            printout()
            printout(center(string.upper(elem.find("title").text)))
            printout(center(elem.find("subtitle").text))
            printout()
            printout(center(elem.find("website").text))
            printout()
            printout()           
        elif elem.tag == "ChapterItem":
            if not first and level == 0:
                printout()
                printout()
                printout(center("* * *"))
                printout()
            first = False
        elif elem.tag == "SceneItem":
            if not first:
                if level == 0:
                    printout()
                    printout()
                    printout(center("* * *"))
                    printout()
                else:
                    printout()
                    printout(center("- - -"))
                    printout()
            printout(paragraphs(elem.find("content").text))
            first = False
            
        childs = elem.find("childs")
        if childs != None: 
            travel(fout, childs, level + 1)

###############################################################################
#
# Exporting document as text
#
###############################################################################

def exportText(tree):
    travel(sys.stdout, tree.getroot())
    
