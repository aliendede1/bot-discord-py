#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from ytsearch import settings

import urwid


class Page:

    """
    The base class for all of the page widget sections.
    All of the keypress actions that are the same in all of the pages
    are defined here
    """

    video_list = None
    results = []
    title = ''
    widgets = None
    keybuffer = []

    def __init__(self, parent):
        self.parent = parent

    def load_page(self):
        """
        The default action for loading the page, which returns a blank text.

        :return: urwid.Filler: The filler around the empty text
        """
        return urwid.Filler(urwid.Text(''))

    def update_video(self, video):
        """
        Find and update a certain video widget.

        :video: ytsearch.Video: The video to find and update.
        :return: None
        """
        if video not in self.results:
            return None
        index = self.results.index(video)
        self.walker[index] = self.parent.create_video_widget(video)
        return None

    def event_MOVE(self, index, count, size):
        if self.video_list is None or index is None:
            return None
        if (count == 'playing' and self.parent.playing is not None
        and self.parent.playing in self.results):
            new_position = self.results.index(self.parent.playing)
            direction = 'above' if index < new_position else 'below'
        elif count == 'bottom':
            new_position = len(self.video_list.body) - 1
            direction = 'above'
        elif count == 'top':
            new_position = 0
            direction = 'below'
        elif count == 'vmiddle':
            data = self.video_list.calculate_visible(size)
            middle, top, bottom = data
            visible_length = len(top[1]) + len(bottom[1]) + 1
            offset = middle[2] - middle[0]
            new_position = offset + (visible_length//2)
            direction = 'above' if index < new_position else 'below'
        elif count == 'vbottom':
            data = self.video_list.calculate_visible(size)
            middle, top, bottom = data
            visible_length = len(top[1]) + len(bottom[1]) + 1
            offset = middle[2] - middle[0]
            new_position = (offset + visible_length) - 1
            direction = 'above' if index < new_position else 'below'
        elif count == 'vtop':
            data = self.video_list.calculate_visible(size)
            middle, top, bottom = data
            offset = middle[2] - middle[0]
            new_position = offset
            direction = 'above' if index < new_position else 'below'
        else:
            try:
                count = int(count)
            except ValueError:
                count = 0
            new_position = index + count
            direction = 'above' if count > 0 else 'below'
        length = len(self.video_list.body)
        if direction == 'above' and new_position > length - 1:
            new_position = length - 1
        if direction == 'below' and new_position < 0:
            new_position = 0
        self.video_list.set_focus(new_position, direction)
        return None

    def event_PLAY_AUDIO(self, index, size):
        if index is None:
            return None
        video = self.results[index]
        self.parent.play(video, audio=True)
        self.event_MOVE(index, 1, size)
        return None

    def event_PLAY_VIDEO(self, index, size):
        if index is None:
            return None
        video = self.results[index]
        self.parent.play(video, audio=False)
        self.event_MOVE(index, 1, size)
        return None

    def event_QUEUE_AUDIO(self, index, size):
        if index is None:
            return None
        video = self.results[index]
        video.audio = True
        self.parent.queue_add(video)
        self.event_MOVE(index, 1, size)
        return None

    def event_QUEUE_VIDEO(self, index, size):
        if index is None:
            return None

        video = self.results[index]
        video.audio = False
        self.parent.queue_add(video)
        self.event_MOVE(index, 1, size)
        return None

    def event_PLAYLIST_ADD(self, index, size):
        if index is None or self.parent.playlist_add is None:
            return None
        video = self.results[index]
        playlist_name = self.parent.playlist_add
        data = {'name': video.name, 'location': video.location, 'resource':
                video._resource, 'cache': video.cache}
        if data in self.parent.playlists[playlist_name]:
            return None
        self.parent.playlists[playlist_name].append(data)
        self.parent.set_video_status(video, 'Added')
        return None

    def event_DOWNLOAD_VIDEO(self, index, size):
        if index is None:
            return None
        video = self.results[index]
        self.parent.download_video(video)
        return None

    def event_NEXT_VIDEO(self, _, size):
        if self.parent.playing is not None:
            self.parent.playing.stop()
        return None

    def event_QUEUE_ALL_AUDIO(self, index, size):
        for video in self.results[index:]:
            video.audio = True
            self.parent.queue_add(video, False)
        self.parent.update_queue()
        return None
    
    def event_QUEUE_ALL_VIDEO(self, index, size):
        for video in self.results[index:]:
            video.audio = False
            self.parent.queue_add(video, False)
        self.parent.update_queue()
        return None

    def event_QUEUE_NEXT(self, index, size):
        video = self.results[index]
        queue = self.parent.queue
        if self.parent.playing is None or self.parent.playing not in queue:
            return None
        new = queue.index(self.parent.playing) + 1
        if new == len(queue):
            new = 0
        if video in queue:
            queue[index], queue[new] = queue[new], queue[index]
        self.parent.update_queue()
        return None
