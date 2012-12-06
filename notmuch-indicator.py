#!/usr/bin/python

from gi.repository.MessagingMenu import App
import gi.repository.Gtk as Gtk
import gi.repository.Gio as Gio
import gi.repository.GObject as GObject
from time import time
import logging
import notmuch
import subprocess
import os.path

# Configuration:
poll_period = 2*60  # seconds
watch_file = '/tmp/notmuch.watch'
searches = {
        'Inbox': 'tag:inbox and tag:unseen',
        'Unseen': 'tag:unseen',
        }


desktop_file = os.path.expanduser('~/.env/notmuch-indicator/notmuch.desktop')
logging.basicConfig(level=logging.DEBUG)

app = None

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

def display_source_cb(app, source):
        logging.info('indicator display: %s' % source)
        display_search(searches[source])

def get_counts():
        db = notmuch.Database()
        counts = {}
        for name,query in searches.items():
                q = notmuch.Query(db, query)
                counts[name] = q.count_messages()
        return counts

def update():
        counts = get_counts()
        logging.debug('Update')
        for name in searches.keys():
                if not app.has_source(name):
                        logging.debug('Creating indicator "%s"' % name)
                        icon = None #Gio.Icon.new_for_string('message.mail')
                        app.append_source(name, icon, name)
                if counts[name] > 0:
                        logging.debug('Showing indicator "%s"' % name)
                        app.set_source_time(name, time())
                        app.set_source_count(name, counts[name])
                else:
                        logging.debug('Hiding indicator "%s"' % name)
                        app.remove_source(name)

def main():
        global app
        app = App.new('notmuch.desktop')
        app.connect('activate-source', display_source_cb)
        app.register()

        have_update_condition = False

        if poll_period is not None:
                logging.info('Polling every %d seconds' % poll_period)
                def cb():
                      update()
                      return True
                GObject.timeout_add_seconds(poll_period, cb)
                have_update_condition = True

        if watch_file is not None:
                import gio
                open(watch_file, 'w').close() # Make sure watch_file exists
                def cb(monitor, file, a, b):
                        logging.debug('Watch file changed')
                        update()
                f = Gio.File(watch_file)
                monitor = f.monitor_file()
                if monitor is None:
                        raise RuntimeError('Failed to monitor watch file')
                monitor.connect('changed', cb)
                logging.info('Watching %s' % watch_file)
                have_update_condition = True

        if not have_update_condition:
                logging.warn("You haven't configured any update condition. Set either poll_period or watch_file")
                return
        
        update()
        Gtk.main()

if __name__ == "__main__":
        main()
