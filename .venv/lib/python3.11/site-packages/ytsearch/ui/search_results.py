#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import urwid


from ytsearch import settings, ui
from ytsearch.ui import page


class Interface(page.Page):

    results = []
    title = 'Search Results'
    description = ''
    widgets = None
    video_list = None

    def __init__(self, parent):
        self.parent = parent
    
    def load_page(self):
        if self.description != '':
            description = " - '{}'".format(self.description)
        else:
            description = ''
        title = urwid.Filler(urwid.Text([('title', self.title),
                             '{}'.format(description)]), 'top')
        header = urwid.Columns([(title)])
        if self.results == []:
            keybind = settings.find_keybinding('SEARCH')
            text = urwid.Text(('title', "Press '{}' to Search".format(keybind)),
                              'center')
            body = urwid.Filler(text, 'middle')
        else:
            videos = [self.parent.create_video_widget(v) for v in self.results]
            self.walker = urwid.SimpleListWalker(videos)
            self.video_list = ui.ItemList(self.parent, self.walker, 'search')
            body = self.video_list
        pile = urwid.Pile([(2, header), body])
        self.widgets = pile
        return pile
