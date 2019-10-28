#!/usr/bin/env python

import sys
import re
import string
import os

#print>>sys.stderr, "Python version:", sys.version_info

from config import conf

#------------------------------------------------------------------------------
# Internal error handling
#------------------------------------------------------------------------------

def ERROR(msg):
    raise Exception("\nERROR:" + msg)

def ERRORIF(cond, msg):
    if cond: ERROR(msg)    

def WARN(msg):
    print>>sys.stderr, "Warning:", msg

def WARNIF(cond, msg):
    if cond: WARN(msg)

def INFO(msg):
    print>>sys.stderr, "Info:", msg

#------------------------------------------------------------------------------
# Older Pythons doesn't have relpath (here's implementation for those)
#------------------------------------------------------------------------------

def relpath(path, start = None):
    if start == None: start = os.curdir
    
    start = os.path.realpath(start)
    path  = os.path.realpath(path)
    
    if not os.path.isdir(path):
        filename = os.path.basename(path)
        path     = os.path.dirname(path)
    else:
        filename = None

    start = start.split("/")
    path  = path.split("/")
    
    for i in range(min(len(start), len(path))):
        if start[0] == path[0]:
            start.pop(0)
            path.pop(0)
            continue
    
    path = string.join(path, "/")
    path = "../" * len(start) + path
    
    if filename:
        path = path + "/" + filename
    
    return path

try:
    os.path.relpath(".")
    print>>sys.stderr, "Using os.path.relpath"
except:
    os.path.relpath = relpath
    print>>sys.stderr, "Using helpers.relpath"
    
###############################################################################
#
# Helpers
#
###############################################################################

def readfile(filename): return conf.readfile(filename)
def writefile(filename, content): return conf.writefile(filename, content)

def readlines(filename):
    return readfile(filename).splitlines()

def writelines(filename, lines):
    writefile(filename, string.join(lines,"\n"))

#-------------------------------------------------------------------------------
# Piping
#-------------------------------------------------------------------------------

#if sys.version_info[:2] == (2,6):

from subprocess import Popen, PIPE

def pipein(cmd):
	return Popen(cmd, shell=True, stdout=PIPE).communicate()[0]

if os.name == "posix":
   devnull = open("/dev/null", "w")
elif os.name == "nt":
   devnull = open("NUL")
else:
   ERROR("Unknown platform: %s", os.name)

def system2devnull(cmd):
	global devnull
	p = Popen(cmd, shell=True, stdout=devnull, stderr=devnull)
	pid, stat = os.waitpid(p.pid, 0)
	return stat

# Python versions sub-2.6
#else:
#
#	def pipein(cmd):
#		from popen2 import popen2
#		childout, childin = popen2(cmd)
#		return childout.read()
#
#	def system2devnull(cmd):
#		return os.system(cmd + " &> /dev/null")	

#------------------------------------------------------------------------------
# OS (Linux/Windows) specific execution
#------------------------------------------------------------------------------

if os.name == "posix":

    def execMoe(filename = None):
        os.system("%s %s &" % (
            os.path.join(conf.scriptdir, "moe.py"),
            filename or "--new")
        )

    def execMoePM():
        os.system("%s &" % (
            os.path.join(conf.scriptdir, "moepm.py"))
        )

    def execEdit(filename):
        os.system("gedit %s &" % (filename))

    def execOpenFolder(filename):
        os.system("nautilus %s &" % (filename))
    
    def execOpenDoc(filename):
        os.system("xdg-open %s &" % (filename))
    
    def execOpenPDF(filename):
        os.system("xdg-open %s &" % (filename))
    
    def execOpenEPUB(filename):
        os.system("xdg-open %s &" % (filename))
    
elif os.name == "nt":

    import subprocess

    def execMoe(filename):
        subprocess.Popen(
            r'""%s\moe.py" "%s""' % (
                os.path.join(conf.scriptdir, "moe.py"),
                filename),
            shell = True,
        )
    def execEdit(filename):
        subprocess.Popen(
            r'notepad "%s"' % (filename),
            shell = True,
        )
    def execOpenFolder(dirname):
        os.startfile(dirname)
        
else:
    ERROR("Unknown platform: %s" % os.name)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def gotodir(filename):
    try:
        dirname = os.path.dirname(filename)
        if dirname != '': os.chdir(dirname)
    except AttributeError:
        pass

#def copyfile(srcfile, dstfile):
#    writefile(dstfile, readfile(srcfile))
#
#def deletefile(filename):
#    os.system("rm %s" % filename)
#
#def makedir(dirname):
#    os.system("mkdir %s" % dirname)
#    
#def touch(filename):
#    os.system("touch %s" % filename)

#------------------------------------------------------------------------------
# Roman numbers
#------------------------------------------------------------------------------

def int2roman(number):
    numerals = { 1 : "I", 4 : "IV", 5 : "V", 9 : "IX", 10 : "X", 40 : "XL", 
        50 : "L", 90 : "XC", 100 : "C", 400 : "CD", 500 : "D", 900 : "CM", 1000 : "M" }
    result = ""
    for value, numeral in sorted(numerals.items(), reverse=True):
        while number >= value:
            result += numeral
            number -= value
    return result
    
