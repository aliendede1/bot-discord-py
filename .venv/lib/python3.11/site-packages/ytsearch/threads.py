#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import threading


class AsThread:
    def __init__(self, daemon=True):
        self.daemon = daemon

    def __call__(self, function):
        def run(*args, **kwargs):
            thread = threading.Thread(target=function, args=args, kwargs=kwargs)
            thread.daemon = self.daemon
            thread.start()
            return None
        return run
