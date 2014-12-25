###############################################################################
#
# MOE Spell Checking
#
###############################################################################

try:
    import libvoikko
    lang = libvoikko.Voikko("fi")
    lang.setNoUglyHyphenation(True)

    INFO("Voikko loaded.")
except ImportError:
    lang = None
    INFO("No hyphenation.")


