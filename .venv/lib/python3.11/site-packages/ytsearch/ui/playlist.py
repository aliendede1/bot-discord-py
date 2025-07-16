#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import urwid

from ytsearch import ui, settings
from ytsearch.ui import page


class Interface(page.Page):

    """
    The interface for the list of playlists.

    :page.Page: The base page.
    """

    mode = 'playlist'

    def load_page(self):
        """
        Load the playlist page.

        :return: urwid.Pile: The pile widget with all of the other widgets
        """
        title = urwid.Filler(urwid.Text(('title', u'Playlists')), 'top')
        if self.parent.playlists == {}:
            keybind = settings.find_keybinding('CREATE_PLAYLIST')
            text = urwid.Text(('title', "Press '{}' to add Playlist".format(keybind)),
                              'center')
            videos = urwid.Filler(text, 'middle')
        else:
            videos = self.load_videos()
        pile = urwid.Pile([(2, title), ('weight', 1, videos)])
        self.widgets = pile
        return pile

    def load_videos(self):
        """
        Load all of the names of the playlist.

        :return: urwid.ItemList: A list of the video widgets.
        """
        videos = []
        self.results = []
        for name in dict(self.parent.playlists):
            video = ui.Video(name, None, 'playlist', None)
            self.results.append(video)
            widget = self.parent.create_video_widget(video, reuse=False)
            videos.append(widget)
        self.walker = urwid.SimpleListWalker(videos)
        self.video_list = ui.ItemList(self.parent, self.walker, 'playlist')
        return self.video_list

    def event_CREATE_PLAYLIST(self, _, size):
        self.parent.create_search_widget('Playlist: ', self.parent.add_playlist)
        return None

    def event_PLAY_AUDIO(self, index, size):
        video = self.results[index]
        playlist_name = video.name
        self.parent.load_playlist(playlist_name)
        return None

    def event_QUEUE_AUDIO(self, index, size):
        video = self.results[index]
        playlist_name = video.name
        self.parent.queue_playlist(playlist_name, audio=True)
        return None

    def event_QUEUE_VIDEO(self, index, size):
        video = self.results[index]
        playlist_name = video.name
        self.parent.queue_playlist(playlist_name, audio=False)
        return None

    def event_TOGGLE_PLAYLIST_ADD(self, index, size):
        if self.parent.playlist_add is None:
            video = self.results[index]
            name = video.name
            self.parent.status = 'Adding to playlist {}'.format(name)
            self.parent.playlist_add = name
        else:
            self.parent.playlist_add = None
            self.parent.status = ''
        return None
