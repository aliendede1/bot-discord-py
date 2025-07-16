#!/usr/bin/env python
# -*- coding: utf-8 -*-


import argparse
import os
import time
import json
import subprocess
import logging
import re
import inspect

import urwid
import yaml
import requests

from ytsearch import youtube, ui, settings


CONF_DIR = settings.CONF_DIR
CACHE_LOCATION = settings.CACHE_LOCATION

LOG = settings.SETTINGS.get('LOG', False)
logging.basicConfig(filename='{}/output.log'.format(CONF_DIR),
                    level=logging.DEBUG)
logger = logging.getLogger()
logger.disabled = not LOG


def mkdir_recursive(directory):
    """Iterates through the directories and makes them if they don't exist.
    The same as mkdir -p
    
    :directory: The fullpath to make.
    :returns: None

    """
    split = directory.split('/')
    for index, item in enumerate(split):
        path = '/'.join(split[:index])
        if path == '':
            continue
        if not os.path.exists(path):
            os.mkdir(path)
    return None


def command_cache(_, *args):
    """
    Displays the videos you have cached.
    """
    with ui.Interface() as interface:
        interface.main('cache')
    return None


def command_search(_, *params):
    """
    Searches youtube for a specified video.
    """
    if len(params) == 0:
        print('You must specify a search term.')
        return None
    video_name = ' '.join(params)
    results = youtube.search(video_name)
    with ui.Interface() as interface:
        widget = ui.search_results.Interface(interface)
        widget.description = video_name
        widget.results = results
        interface.saved_pages['search'] = widget
        interface.current_page = widget
        interface.main('search', widget.load_page())
    return None


def command_import(_, url, *args):
    """
    Imports a youtube playlist.

    :url: str: The url to load.
    :params: tuple: Unused.
    :return: None
    """
    print('Retrieving playlist')
    videos, info = youtube.get_playlist(url)
    playlist_name = info['snippet']['title']
    channel_name = info['snippet']['channelTitle']
    title = '{} - {}'.format(channel_name, playlist_name)
    playlist = {title: []}
    print('Parsing videos from {}'.format(title))
    for video in videos:
        data = {'name': video['snippet']['title'], 
                'location': video['contentDetails']['videoId'],
                'resource': 'youtube', 'cache': None}
        playlist[title].append(data)
    playlist_file = '{}/playlists.json'.format(CONF_DIR)
    if os.path.exists(playlist_file):
        with open(playlist_file, 'r') as f:
            playlists = json.loads(f.read())
    else:
        playlists = {}
    playlists.update(playlist)
    with open(playlist_file, 'w') as f:
        f.write(json.dumps(playlists))
    print('Saved playlist {}'.format(title))
    return None


def command_channel(_, *username):
    """
    Loads videos from a youtube channel.
    """
    username = ' '.join(username)
    results = youtube.raw_search(username)
    videos = results['items']
    channel_id = videos[0]['snippet']['channelId']
    channel_name = videos[0]['snippet']['channelTitle']
    proceed = input('Load videos from "{}" [y/n] '.format(channel_name))
    if proceed.lower() not in ['yes', 'y']:
        return None

    channel_info = youtube.request('channels', part='contentDetails',
                                   id=channel_id, key=youtube.KEY)
    upload_playlist = channel_info['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    data, name = youtube.get_playlist(upload_playlist)
    videos = []
    for info in data:
        video = ui.Video(info['snippet']['title'],
                         info['contentDetails']['videoId'],
                         'youtube', None)
        videos.append(video)

    with ui.Interface() as interface:
        widget = ui.search_results.Interface(interface)
        widget.description = channel_name
        widget.results = videos
        interface.saved_pages['search'] = widget
        interface.current_page = widget
        interface.main('search', widget.load_page())
    return None


def command_url(_, *urls):
    """
    Loads a list of videos passed to the script.
    """
    videos = []
    for url in urls:
        match = re.search('watch\?v=(.*?)$', url)
        if match is None:
            continue
        info = youtube.request('videos', part='snippet', id=match.group(1),
                               key=youtube.KEY)
        video_info = info['items'][0]['snippet']
        video = ui.Video(video_info['title'], match.group(1), 'youtube', None)
        videos.append(video)

    with ui.Interface() as interface:
        widget = ui.search_results.Interface(interface)
        widget.description = '{} videos'.format(len(videos))
        widget.results = videos
        interface.saved_pages['search'] = widget
        interface.current_page = widget
        interface.main('search', widget.load_page())
    return None


def check_default_files():
    if not os.path.exists(CACHE_LOCATION):
        mkdir_recursive(CACHE_LOCATION)
    return None


def get_epilog():
    commands = {
        c[8:]: globals()[c] for c in globals()
        if c.startswith('command_')}
    output = 'commands:\n'
    longest = 0
    for name in commands:
        if len(name) > longest:
            longest = len(name)
    for name, function in commands.items():
        doc = inspect.getdoc(function) or 'No documentation'
        doc = doc.split('\n')[0]
        output += '  {:<{}}{}\n'.format(name, longest + 3, doc)
    return output


def main():
    check_default_files()
    epilog = get_epilog()
    parser = argparse.ArgumentParser(
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', help='The command to run.', nargs='?')
    parser.add_argument('args', nargs='*',
                        help='The arguments to pass to the command.')
    args = parser.parse_args()
    commands = {c[8:]:globals()[c] for c in globals()
                if c.startswith('command_')}
    command = commands.get(args.command, None)
    if command is None:
        command = command_cache
        arguments = [args.command] + args.args
    else:
        if args.args is None:
            arguments = []
        else:
            arguments = args.args
    command(args, *arguments) 
    return None


if __name__ == "__main__":
    main()
