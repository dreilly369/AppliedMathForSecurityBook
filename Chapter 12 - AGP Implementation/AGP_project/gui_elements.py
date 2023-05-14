#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 14:27:39 2021

@author: dreilly
"""

"""<title>Dialogs and Documents</title>
"""
import pygame
from pygame.locals import *

# the following line is not needed if pgu is installed
import sys; sys.path.insert(0, "..")

from pgu import gui

##Documents layout widgets like words and images in a HTML document.  This
##example also demonstrates the ScrollBox container widget.
##::
class AboutDialog(gui.Dialog):
    def __init__(self,**params):
        title = gui.Label("About The AGP Solver")
        
        width = 400
        height = 200
        doc = gui.Document(width=width)
        
        space = title.style.font.size(" ")
        
        doc.block(align=0)
        for word in """The Art Gallery Problem Solver by Daniel Reilly""".split(" "): 
            doc.add(gui.Label(word))
            doc.space(space)
        doc.br(space[1])
        doc.br(space[1])
        doc.block(align=-1)
        for word in """Thank you for your interest in AGP and PAMS! A book for the modern security practicioner""".split(" "): 
            doc.add(gui.Label(word))
            doc.space(space)
        doc.br(space[1])

        
        for word in """The art gallery problem is formulated in geometry as the minimum number of guards that need to be placed in a polygon such that all points of the interior are visible to at least one guard.""".split(" "):
            doc.add(gui.Label(word))
            doc.space(space)
        doc.br(space[1])
        doc.br(space[1])
        for word in """A gallery is defined as a connected closed region whose boundary is defined by a finite number of line segments.""".split(" "):
            doc.add(gui.Label(word))
            doc.space(space)
        doc.br(space[1])
        doc.br(space[1])

        for word in """Visibility is define such that two points u and v are mutually visible if the line segment joining them lies inside the polygon.""".split(" "):
            doc.add(gui.Label(word))
            doc.space(space)
        doc.br(space[1])
        doc.br(space[1])
        
        for word in """Using these definitions, Steve Fisk was able toprove Chv'atal’s initial theorem using triangulation and vertex coloring.""".split(" "):
            doc.add(gui.Label(word))
            doc.space(space)
        doc.br(space[1])
        doc.br(space[1])

        for word in """We use a similar method here to solve floor plans loaded from background images""".split(" "):
            doc.add(gui.Label(word))
            doc.space(space)
        doc.br(space[1])
                
        gui.Dialog.__init__(self,title,gui.ScrollArea(doc,width,height))

class ColorDialog(gui.Dialog):
    def __init__(self,value,**params):
        self.value = list(gui.parse_color(value))
        
        title = gui.Label("Color Picker")
        
        main = gui.Table()
        
        main.tr()
        
        self.color = gui.Color(self.value,width=64,height=64)
        main.td(self.color,rowspan=3,colspan=1)
        
        ##The sliders CHANGE events are connected to the adjust method.  The 
        ##adjust method updates the proper color component based on the value
        ##passed to the method.
        ##::
        main.td(gui.Label(' Red: '),1,0)
        e = gui.HSlider(value=self.value[0],min=0,max=255,size=32,width=128,height=16)
        e.connect(gui.CHANGE,self.adjust,(0,e))
        main.td(e,2,0)
        ##

        main.td(gui.Label(' Green: '),1,1)
        e = gui.HSlider(value=self.value[1],min=0,max=255,size=32,width=128,height=16)
        e.connect(gui.CHANGE,self.adjust,(1,e))
        main.td(e,2,1)

        main.td(gui.Label(' Blue: '),1,2)
        e = gui.HSlider(value=self.value[2],min=0,max=255,size=32,width=128,height=16)
        e.connect(gui.CHANGE,self.adjust,(2,e))
        main.td(e,2,2)
                        
        gui.Dialog.__init__(self,title,main)
        
    ##The custom adjust handler.
    ##::
    def adjust(self,value):
        (num, slider) = value
        self.value[num] = slider.value
        self.color.repaint()
        self.send(gui.CHANGE)
    ##
    
class SettingsDialog(gui.Dialog):
    def __init__(self,**params):
        title = gui.Label("New Picture...")
        
        ##Once a form is created, all the widgets that are added with a name
        ##are added to that form.
        ##::
        self.value = gui.Form()
        
        t = gui.Table()
        
        t.tr()
        t.td(gui.Label("Size"),align=0,colspan=2)
        
        tt = gui.Table()
        tt.tr()
        tt.td(gui.Label("Width: "),align=1)
        tt.td(gui.Input(name="width",value=256,size=4))
        tt.tr()
        tt.td(gui.Label("Height: "),align=1)
        tt.td(gui.Input(name="height",value=256,size=4))
        t.tr()
        t.td(tt,colspan=2)
        ##
        
        t.tr()
        t.td(gui.Spacer(width=8,height=8))
        t.tr()
        t.td(gui.Label("Format",align=0))
        t.td(gui.Label("Background",align=0))

        t.tr()        
        g = gui.Group(name="color",value="#ffffff")
        tt = gui.Table()
        tt.tr()
        tt.td(gui.Radio(g,value="#000000"))
        tt.td(gui.Label(" Black"),align=-1)
        tt.tr()
        tt.td(gui.Radio(g,value="#ffffff"))
        tt.td(gui.Label(" White"),align=-1)
        tt.tr()

        t.tr()        
        t.td( gui.Label('File Name:'), align=-1)
        input_file = gui.Input()
        t.td(input_file, align=-1)
        b = gui.Button("Browse...")
        t.td( b, align=-1)
        b.connect(gui.CLICK, open_file_browser, None)
        
        t.td(tt,colspan=1)
        t.tr()
        t.td(gui.Spacer(width=8,height=8))
        
        ##The okay button CLICK event is connected to the Dailog's 
        ##  send event method.  It will send a gui.CHANGE event.
        ##::
        t.tr()
        e = gui.Button("Okay")
        e.connect(gui.CLICK,self.send,gui.CHANGE)
        t.td(e)
        ##
        
        e = gui.Button("Cancel")
        e.connect(gui.CLICK,self.close,None)
        t.td(e)
        
        gui.Dialog.__init__(self,title,t)
        
def open_file_browser(arg):
    d = gui.FileDialog()
    d.connect(gui.CHANGE, handle_file_browser_closed, d)
    d.open()
    

def handle_file_browser_closed(dlg):
    if dlg.value:
        if ".png" in dlg.value:
            return dlg.value
        else:
            print("Nota valid PNG file")
##The dialog's CHANGE event is connected to this function that will display the form values.
##::
def settings_onchange(value):
    print('-----------')
    for k,v in value.value.items():
        print(k,v)
    value.close()
        
if __name__ in '__main__':

    app = gui.Desktop()
    app.connect(gui.QUIT,app.quit,None)
    
    c = gui.Table(width=800,height=640)
    
    dialog = ColorDialog("#ffffff")
            
    e = gui.Button("Color")
    e.connect(gui.CLICK,dialog.open,None)
    c.tr()
    c.td(e)
    
    ##The button CLICK event is connected to the dialog.open method.
    ##::
    dialog = AboutDialog()
    
    about_btn = gui.Button("About")
    about_btn.connect(gui.CLICK,dialog.open,None)
    ##
    c.tr()
    c.td(about_btn)
    
    dialog = SettingsDialog()
    
    dialog.connect(gui.CHANGE,settings_onchange,dialog)
    ##
            
    new_btn = gui.Button("Settings")
    new_btn.connect(gui.CLICK,dialog.open,None)
    c.tr()
    c.td(new_btn)
    app.run(c)
    