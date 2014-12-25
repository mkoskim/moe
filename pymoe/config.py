#!/usr/bin/env python
###############################################################################
#
# Configurations
#
# The overall principle is this:
#
# 1. Script knows the directory it is located, e.g.
#
#       <script>    = "stories/moe/moepy/moe.py"
#       <scriptdir> = "stories/moe/moepy/"
#       <rootdir>   = "stories/"
#
# 2. Shared, "read-only" default settings are located in the
#    "defaults/" directory in script directory:
#
#       "<rootdir>/moe/settings/moe.xml"
#
# 3. User-modified shared settings are located in the ".moerc/"
#    directory in the document root directory:
#
#       "<rootdir>/.moerc/"
#
#    This enables moe to share personal settings with texifier
#    script package.
#
# 4. Document-specific settings are stored in the document
#    itself, under element named "settings"
#
# 5. GUI-specific settings are stored separately to each host
#    (as their display sizes, fonts and such differ):
#
#       <settings>
#           <host>
#               <hostname1> ... </hostname1>
#               <hostname2> ... </hostname2>
#           </host>
#       </settings>
#
###############################################################################

import os
import sys
import socket   # For determining host name
import shutil   # For copying files

import moeXML
from moeXML import ET, ExpatError

scriptname = os.path.realpath(sys.argv[0])
scriptdir  = os.path.abspath(os.path.dirname(scriptname))
rootdir    = os.path.abspath(os.path.dirname(scriptname)+"/../../")
defsdir    = os.path.abspath(scriptdir+"/../settings/")
confdir    = os.path.abspath(rootdir+"/.moerc/")

snippetfile = confdir + "/snippets.moe"

###############################################################################
#
# Configurations
#
###############################################################################

class Config(object):

    #-------------------------------------------------------------------------
    # Different global settings etc
    #-------------------------------------------------------------------------

    bg_synopses = '#FFFFDD'

    #-------------------------------------------------------------------------
    # File decoding/encoding
    #-------------------------------------------------------------------------

    encoding = "utf-8"
    decodings = [ "utf-8", "latin-1" ]

    def decode(self, content):
        for codec in self.decodings:
            try:
                content = unicode(content, codec)
            except UnicodeDecodeError:
                continue
            return content
        raise Exception("Unknown encoding: " + filename)

    def encode(self, content):
        return content.encode(self.encoding)

    #-------------------------------------------------------------------------
    # File reading/writing
    #-------------------------------------------------------------------------

    def readfile(self, filename):
        f = open(filename, "r")
        content = f.read()
        f.close()
        return self.decode(content)    

    def writefile(self, filename, content):
        f = open(filename, "w")
        f.write(self.encode(content))
        f.close()

    #-------------------------------------------------------------------------
    # Config file reading/writing
    #-------------------------------------------------------------------------

    def readConfigFile(self, filename):
        global confdir, defsdir
        
        if os.path.isfile(os.path.join(confdir, filename)):
            filename = os.path.join(confdir, filename)
        else:
            filename = os.path.join(defsdir, filename)
        return self.readfile(filename)

    def writeConfigFile(self, filename, content):
        global confdir
        filename = os.path.join(confdir, filename)
        return self.writefile(filename, content)

    #-------------------------------------------------------------------------
    # Config XML file reading/writing
    #-------------------------------------------------------------------------

    def readXMLTree(self, filename):
        try:
            content = self.readfile(filename)
            return ET.ElementTree(ET.fromstring(content))
        except IOError:
            return ET.ElementTree(ET.Element("settings"))

    def writeXMLTree(self, filename, tree):
        moeXML.prettyFormat(tree.getroot())
        content = ET.tostring(tree.getroot(), self.encoding)
        self.writefile(filename, content)
        
    #-------------------------------------------------------------------------
    #-------------------------------------------------------------------------

    def _findHostDefaults(self, tree):
        self.hostdefaults = tree.findall("host")
        for host in self.hostdefaults:
            if host.get("name") == self.host:
                self.hostdefaults = ET.ElementTree(host)
                return
        self.hostdefaults = ET.SubElement(tree.getroot(), "host")
        self.hostdefaults.set("name", self.host)
        self.hostdefaults = ET.ElementTree(self.hostdefaults)

    #-------------------------------------------------------------------------
    # Constructor
    #-------------------------------------------------------------------------

    def __init__(self):
        global scriptname, scriptdir, rootdir, defsdir, confdir
        self.scriptname = scriptname
        self.scriptdir  = scriptdir
        self.rootdir    = rootdir
        self.defsdir    = defsdir
        self.confdir    = confdir

        self.host = socket.gethostname()

        self.sysdefaults = self.readXMLTree(os.path.join(self.defsdir,"moe.xml"))
        self.usrdefaults = self.readXMLTree(os.path.join(self.confdir,"moe.xml"))
        self.docdefaults = None
        
        self._findHostDefaults(self.usrdefaults)
        
        self.version = self.readfile(os.path.join(self.defsdir,"VERSION"))
        
    #-------------------------------------------------------------------------
    # Get settings section from doc for later use
    #-------------------------------------------------------------------------

    def load(self, docname):
        if docname != None and os.path.isfile(docname + "rc"):
            self.docdefaults = self.readXMLTree(docname + "rc")
        else:
            self.docdefaults = None
        
        if self.docdefaults == None:
            self.docdefaults = ET.ElementTree(ET.Element("settings"))
            self.hostdefaults = ET.ElementTree(ET.SubElement(self.docdefaults.getroot(), "host"))
            self.hostdefaults.getroot().set("name", self.host)
        else:
            self._findHostDefaults(self.docdefaults)
        
    #-------------------------------------------------------------------------
    # Save general settings (doc-specific settings are saved with doc)
    #-------------------------------------------------------------------------

    def save(self, docname = None):
        if not os.path.exists(self.confdir):
            os.mkdir(self.confdir)
        self.writeXMLTree(os.path.join(self.confdir,"moe.xml"), self.usrdefaults)
        if docname:
            self.writeXMLTree(docname + "rc", self.docdefaults)

    #-------------------------------------------------------------------------
    # Get/set texifier fields, find elements
    #-------------------------------------------------------------------------

    texconf = {
        "author":  "author.tex",
        "website": "website.tex",
    }

    def _get_texfield(self, field):
        return self.readConfigFile(self.texconf[field])

    def _set_texfield(self, field, content):
        if not os.path.exists(self.confdir):
            os.mkdir(self.confdir)
        return self.writeConfigFile(self.texconf[field], content)

    def _get_texfield_level(self, field):
        if os.path.isfile(os.path.join(confdir, self.texconf[field])):
            return "usr"
        return "sys"

    #-------------------------------------------------------------------------
    # Get/set fields, find elements
    #-------------------------------------------------------------------------

    def _get_field(self, elem, field):
        if elem == None: raise Exception("_get_field() with elem == None.")
        if field == None:
            value = elem.text
        else:
            value = elem.get(field)
        #print "get(%s[%s]) --> %s" % (elem.tag, field, value)
        return value

    def _set_field(self, elem, field, value):
        if elem == None: raise Exception("_set_field() with elem == None.")
        if field == None:
            elem.text = value
        else:
            elem.set(field, str(value))

    def _look4read(self, name, *trees):
        for tree in trees:
            if tree == None: continue
            elem = tree.find(name)
            if elem != None: return elem
        return None
    
    def _look4write(self, name, tree):
        elem = tree.find(name)
        if elem != None: return elem
        return ET.SubElement(tree.getroot(), name)

    #-------------------------------------------------------------------------
    # Getting/setting non-doc defaults
    #-------------------------------------------------------------------------

    def get_default(self, name, field = None):
        if name in self.texconf:
            return self._get_texfield(name)
        else:
            return self._get_field(
                self._look4read(
                    name,
                    self.usrdefaults,
                    self.sysdefaults),
                field)

    def get_default_level(self, name, field = None):
        if name in self.texconf:
            return self._get_texfield_level(name)
        else:
            if self._look4read(self, name, self.usrdefaults): return "usr"
        return "sys"

    def set_default(self, name, field, value):
        if name in self.texconf:
            self._set_texfield(name, value)
        else:
            self._set_field(
                self._look4write(name, self.usrdefaults),
                field, value
            )

    #-------------------------------------------------------------------------
    # Getting/setting doc defaults
    #-------------------------------------------------------------------------

    def get_doc(self, name, field = None):
        return self._get_field(
            self._look4read(
                name,
                self.docdefaults,
                self.usrdefaults,
                self.sysdefaults
            ),
            field)

    def set_doc(self, name, field, value):
        self._set_field(
            self._look4write(name, self.docdefaults),
            field, value
        )

    #-------------------------------------------------------------------------
    # Getting/setting host specific info, usually GUI settings
    #-------------------------------------------------------------------------

    def get_host(self, name, field = None):
        return self._get_field(
            self._look4read(
                name,
                self.hostdefaults,
                self.sysdefaults.find("host")
            ),
            field)

    def set_host(self, name, field, value):
        if self.hostdefaults is not None: self._set_field(
            self._look4write(name,
                self.hostdefaults,
            ),
            field, value
        )
            
    def get_gui(self, name, field = None):
        return self.get_host(name, field)
    
    def set_gui(self, name, field, value):
        return self.set_host(name, field, value)
    
conf = Config()
