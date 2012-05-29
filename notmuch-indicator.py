#!/usr/bin/python

import indicate
import gobject
import gtk
from time import time
import logging
import notmuch
import subprocess
import os.path

desktop_file = os.path.expanduser('~/.env/notmuch-indicator/notmuch.desktop')
logging.basicConfig(level=logging.DEBUG)

poll_period = 2*60
searches = {
        'Inbox': 'tag:inbox',
        'Unseen': 'tag:unseen',
        }


def display_search_client(query):
        p = subprocess.Popen(['emacsclient', '-s', 'notmuch', '-e', '(notmuch-search "%s")' % query],)
        if p.wait() != 0:
                subprocess.Popen(['emacs', '--daemon=notmuch', '--eval', '(notmuch-search "%s")' % query])
                subprocess.Popen(['emacsclient', '-s', 'notmuch', '-e', '(notmuch-search "%s")' % query],)
        subprocess.Popen(['xdotool', 'search', 'class=emacs', 'windowactivate'])

def start_notmuch():
        subprocess.Popen(['emacs', '--eval', '(notmuch-hello)'])

def display_search_noclient(query):
        subprocess.Popen(['emacs', '--eval', '(notmuch-search "%s")' % query])
        subprocess.Popen(['xdotool', 'search', 'class=emacs', 'windowactivate'])

display_search = display_search_noclient

def display_cb(indicator, timestamp):
        name = indicator.get_property('name')
        logging.info('indicator display: %s' % name)
        display_search(searches[name])

def server_display_cb(server, timestamp):
        logging.info('server display')
        start_notmuch()

def get_counts():
        db = notmuch.Database()
        counts = {}
        for name,query in searches.items():
                q = notmuch.Query(db, query)
                counts[name] = q.count_messages()
        return counts

def update_cb(indicators):
        counts = get_counts()
        logging.debug('update')
        for name in searches.keys():
                if name not in indicators:
                        logging.debug('Creating indicator "%s"' % name)
                        indicator = indicate.Indicator()
                        indicator.set_property('name', name)
                        indicator.connect('user-display', display_cb)
                        indicators[name] = indicator

                indicator = indicators[name]
                indicator.set_property_time('time', time())
                indicator.set_property('count', str(counts[name]))
                if counts[name]:
                        logging.debug('Showing indicator "%s"' % name)
                        indicator.show()
                else:
                        logging.debug('Hiding indicator "%s"' % name)
                        indicator.hide()

        return True

if __name__ == "__main__":
        indicators = {}
        server = indicate.indicate_server_ref_default()
        server.set_type('message.mail')
        server.set_desktop_file(desktop_file)
        server.connect('server-display', server_display_cb)

        gobject.timeout_add_seconds(poll_period, update_cb, indicators)
        update_cb(indicators)
        gtk.main()

