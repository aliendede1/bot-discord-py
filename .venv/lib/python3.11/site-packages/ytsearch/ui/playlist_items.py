#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

import urwid

from ytsearch import ui, settings, threads
from ytsearch.ui import page


LOOP = asyncio.get_event_loop()


class Interface(page.Page):

    """
    The interface for the playlist items.

    :page.Page: The base page to load.
    """
    mode = 'playlist_items'
    playlist_name = None
    videos = []

    def load_page(self):
        """
        Load the widgets of this page.

        :return: urwid.Pile: The pile with all of the widgets in there.
        """
        if self.description != '':
            description = " - '{}'".format(self.description)
        else:
            description = ''
        title = urwid.Filler(urwid.Text([('title', 'Playlist'),
                             '{}'.format(description)]), 'top')
        header = urwid.Columns([(title)])
        self.walker = urwid.SimpleListWalker([])
        self.video_list = ui.ItemList(self.parent, self.walker, 'playlist_items')
        pile = urwid.Pile([(2, header), ('weight', 1, self.video_list)])
        self.widgets = pile

        LOOP.call_later(0, self.load_videos)
        return pile

    @threads.AsThread()
    def load_videos(self):
        """
        Load all of the videos from the playlist storage.

        :return: urwid.ItemList: The list of widgets to load.
        """
        self.results = []
        for data in self.playlist_items:
            video = ui.Video(data['name'], data['location'],
                          data['resource'], data['cache'])
            widget = self.parent.create_video_widget(video)
            self.results.append(video)
            self.walker.append(widget)
            self.parent.loop.draw_screen()
        self.parent.status = 'Loaded {} videos'.format(len(self.results))
        return None

    def event_REMOVE_PLAYLIST_ITEM(self, index, size):
        if self.video_list is None:
            return None
        video = self.results[index]
        name = self.playlist_name
        data = {'name': video.name, 'location': video.location,
                'resource': video._resource, 'cache': video.cache}
        if data in list(self.parent.playlists[name]):
            playlist_index = self.parent.playlists[name].index(data)
            del self.parent.playlists[name][playlist_index]
            self.parent.load_playlist(name)
        return None
