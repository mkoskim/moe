# -*- coding: utf-8 -*-
###############################################################################
#
# Converting RTF to text block suitable for MOE. We might want to use
# e.g. LibreOffice to do it.
#
###############################################################################

import string

from moeReadASCII import convertASCII

#------------------------------------------------------------------------------

def convertRTF(content):
    
    #--------------------------------------------------------------------------
    # NOTE: This table is similar to moeExport replacement table!
    #--------------------------------------------------------------------------
    
    reptbl = (
        (r"\u228\'e4", "ä"),
        (r"\u246\'f6", "ö"),
        (r"\u231\'e7", "ç"),
        
        (r"\u8220\'1c", '"'),
        (r"\u8221\'1d", '"'),

        (r"\'e5", "å"),
        (r"\'c5", "Å"),
        (r"\'e4", "ä"),
        (r"\'c4", "Ä"),
        (r"\'f6", "ö"),
        (r"\'d6", "Ö"),
        (r"\'94", '"'),
        (r"\~",   '~'),

        (r"\'94", '"'),
    )

    for find, rep in reptbl:
        content = content.replace(find, rep)
    
    #--------------------------------------------------------------------------

    reptbl2 = (
        ("\\pard", "\n\n"),
        ("\\par",  "\n\n"),
        ("{", ""),
        ("}", ""),
    )
    
    for find, rep in reptbl2:
        content = content.replace(find, rep)

    #--------------------------------------------------------------------------

    content = string.split(content, "\n\n")
    
    for i in range(len(content)):

        words = content[i].split()
        words = map(lambda w: string.strip(w), words)
        words = filter(lambda w: len(w), words)
        words = filter(lambda w: w[0] != "\\", words)
        content[i] = string.join(words, " ")
        
        content[i].replace("\n", " ")
        content[i] = string.strip(content[i])

    content = filter(lambda s: len(s), content)
    content = string.join(content, "\n\n")

    return content

#------------------------------------------------------------------------------
# Possible improved importer
#------------------------------------------------------------------------------

def rtf_scan(content):

    def lookup(content, i):
        if i < len(content):
            return content[i]
        return '\0'
        
    def next(content, i):
        if i < len(content):
            return content[i], i + 1
        return '\0', i

    tokens = []
    i = 0

    while lookup(content, i) != '\0':
        c, i = next(content, i)
        if c == "{":
            tokens.append("{")
        elif c == "}":
            tokens.append("}")
        elif c == "\\":
            word = "\\"
            while lookup(content, i) not in "\\ \n\r\t\0{}":
                c, i = next(content, i)
                word = word + c
            tokens.append(word)
        elif c in " \n\r\t":
            word = ""
            while lookup(content, i) in " \n\r\t":
                c, i = next(content, i)
                word = word + c
            tokens.append(" ")
        else:
            word = c
            while lookup(content, i) not in "\\ \n\r\t\0{}":
                c, i = next(content, i)
                word = word + c
            tokens.append(word)

    return tokens


