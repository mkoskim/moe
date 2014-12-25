###############################################################################
#
# Handling external file formats
#
###############################################################################

from helpers import *

from moeReadASCII import convertASCII
from moeReadRTF import convertRTF

#------------------------------------------------------------------------------
# For importing RTF etc.
#------------------------------------------------------------------------------

def importFile(filename):

    ext = os.path.splitext(filename)[1]

    formats = {
        None:   convertASCII,
        ".rtf": convertRTF,
    }

    if ext not in formats: ext = None
        
    return formats[ext](readfile(filename))

