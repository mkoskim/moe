###############################################################################
#
# Converting ASCII to text block suitable for MOE
#
###############################################################################

import string

def convertASCII(content):

    lines = content.split("\n")

    maxlength = max(
        map(lambda l: len(l), lines)
    )

    if maxlength > 120:
        content = string.join(lines, "\n\n")
    else:
        content = string.join(lines, "\n")

    return content    
