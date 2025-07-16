#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os

import urwid
import yaml

from ytsearch import ui, settings
from ytsearch.ui import page


class Interface(page.Page):

    mode = 'settings'

    def load_page(self):
        self.parent.destroy_terminal_widget()
        template = settings.SETTINGS
        setting_file = '{}/template.yaml'.format(ui.CONF_DIR)
        with open(setting_file, 'w') as f:
            f.write(yaml.dump(template, default_flow_style=False))
        command = list(settings.SETTINGS['settings']['command'])
        command.append(setting_file)
        self.widgets = urwid.Terminal(command, main_loop=self.parent.loop)
        urwid.connect_signal(self.widgets, 'closed', self.finished)
        return self.widgets

    def finished(self, *_):
        setting_file = '{}/template.yaml'.format(ui.CONF_DIR)
        with open(setting_file, 'r') as f:
            data = yaml.load(f.read())
        os.remove(setting_file)
        settings.SETTINGS = settings.save_settings(data)
        ui.reload_settings()
        self.parent.load_page('cache')
        self.parent.update_state()
        self.parent.restore_terminal_widget()
        return None
