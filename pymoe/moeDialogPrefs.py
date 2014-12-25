from config import conf
from helpers import *
from moeGTK import *

class PreferencesDialog(gtk.Dialog):
    
    #--------------------------------------------------------------------------
    #--------------------------------------------------------------------------

    def __init__(self):
        super(PreferencesDialog,self).__init__(parent = conf.mainwnd)

        self.set_title("Preferences")
        
        #----------------------------------------------------------------------
        #----------------------------------------------------------------------

        self.author  = TextBuf(conf.get_default("author"))
        self.website = TextBuf(conf.get_default("website"))

        #----------------------------------------------------------------------
        #----------------------------------------------------------------------

        box = createEditGrid(
            None,
            [
                [ "Author", createEntry(self.author) ],
                [ "Website", createEntry(self.website) ]
            ],
            False, False
        )

        box.set_size_request(300, -1)
        box.show()
        
        #vbox = self.get_content_area()
        vbox = self.vbox
        
        vbox.pack_start(box, False, False)
        
        #----------------------------------------------------------------------
        #----------------------------------------------------------------------

        self.add_button("OK", gtk.RESPONSE_OK)
        self.add_button("Cancel", gtk.RESPONSE_CANCEL)
        
    #dialog = gtk.FontSelectionDialog("Select font")
    #if dialog.run() == gtk.RESPONSE_OK:
    #    conf.editfont = pango.FontDescription(dialog.get_font_name())
    #    self.view.fontChanged()
    #dialog.destroy()

def editPreferences():
    
    dialog = PreferencesDialog()
    dialog.show_all()
    
    if dialog.run() == gtk.RESPONSE_OK:
        conf.set_default("author",  None, dialog.author.get_content())
        conf.set_default("website", None, dialog.website.get_content())
        conf.save()

    dialog.destroy()

