import youtube_dl as yt
from dearpygui.core import *
from dearpygui.simple import *
from pyautogui import size
from os import path, makedirs
from subprocess import Popen
import json

CONFIG_FILE = path.expanduser('~/Documents/PyTube/settings.json')
CONFIG_FOLDER = path.expanduser('~/Documents/PyTube')


class Ccolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def console_log(msg, msg_type='Info', btn=''):
    add_row(table='##table', row=[msg_type, msg, btn])


class Logger(object):
    def debug(self, msg):
        if '[download]' in msg and 'Destination' not in msg:
            console_log(msg.replace('[download]', ''), msg_type='Progress')
        if '[ffmpeg] Destination:' in msg:
            console_log(msg.replace('[ffmpeg] Destination: ', ''), msg_type='Finished', btn='Open')
        if 'already is in target format' in msg:
            console_log(msg.replace('[ffmpeg] Not converting video file ', '').replace(' - already is in target format mp4', ''), msg_type='Finished', btn='Open')
        print(f'{Ccolors.OKGREEN}{msg}{Ccolors.ENDC}')

    def warning(self, msg):
        console_log(msg, msg_type='Warning')
        print(f'{Ccolors.WARNING}{msg}{Ccolors.ENDC}')

    def error(self, msg):
        if 'is not a valid URL' in msg:
            console_log('Invalid URL', msg_type='Error')
            console_log('URL Format: https://www.youtube.com/...', msg_type='Warning')
        print(f'{Ccolors.FAIL}{msg}{Ccolors.ENDC}')


def progress_hook(d):
    if d['status'] == 'finished':
        console_log('Done downloading, now converting ...', msg_type='Progress')


def clear_table():
    x = get_table_selections('##table')
    for y in x:
        set_table_selection('##table', row=y[0], column=y[1], value=False)


def table_cb(s):
    n = '##table'
    x, y = get_table_selections('##table')[0]
    if get_table_item(table=n, row=x, column=y) != 'Open':
        set_table_selection(n, row=x, column=y, value=False)
    else:
        set_table_selection(n, row=x, column=y, value=False)
        destination = get_table_item(n, x, y-1)
        try:
            Popen(r'explorer /select,"{}"'.format(destination))
        except:
            console_log('Could not open Windows Explorer', msg_type='Error')


def save_conf():
    t, dest, to = get_value('##type'), get_value('##dest'), get_value('##format')
    config = {'destination': dest, 'type': t, 'format': to}
    try:
        with open(file=CONFIG_FILE, mode='w') as conf:
            json.dump(config, conf)
    except OSError:
        console_log('Could not create config file', msg_type='Error')
        console_log('Try running PyTubeDL in admin mode')


def load_conf():
    if not path.exists(CONFIG_FOLDER):
        try:
            makedirs(CONFIG_FOLDER)
        except OSError:
            console_log('Could not create config folder', msg_type='Error')
        finally:
            return
    try:
        with open(file=CONFIG_FILE) as config:
            user_conf = json.load(config)
        try:
            set_value('##dest', user_conf['destination'])
            set_value('##type', user_conf['type'])
            set_value('##format', user_conf['format'])
        except KeyError:
            console_log('Bad config file', msg_type='Error')
            console_log('Creating a new one')
            save_conf()
    except OSError:
        console_log('Could not load config file', msg_type='Error')
        console_log('Creating a new one ...')
        save_conf()
        console_log('Config file created successfully')


def start():
    t, url, dest, form = get_value('##type'), get_value('##url'), get_value('##dest'), get_value('##format')
    if not t:
        return console_log('Select the type', msg_type='Error')
    if not url:
        return console_log('Missing URL', msg_type='Error')
    if not dest:
        return console_log('Set destination folder', msg_type='Error')
    if not form:
        return console_log('Select output format', msg_type='Error')
    if t == 'Playlist' and 'list=' not in url:
        return console_log('Could not find playlist on given URL', msg_type='Error')
    save_conf()
    if form == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': dest + '/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'logger': Logger(),
            'progress_hooks': [progress_hook],
        }
    else:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': dest + '/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'logger': Logger(),
            'progress_hooks': [progress_hook],
        }
    if t == 'Video':
        ydl_opts['noplaylist'] = True
    with yt.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    clear_table()


def layout():
    with window(name='main_window', label='PyTube'):
        with menu_bar('_menu_bar'):
            with menu(name='m_devtools', label='Diagnostic Tools'):
                add_menu_item(name='mi_logger', label='Logger', callback=show_logger)
                add_menu_item(name='mi_debug', label='Debug', callback=show_debug)
                add_menu_item(name='mi_metrics', label='Metrics', callback=show_metrics)
        add_dummy()
        add_text(name='Type of input: ')
        add_combo(name='##type', items=['Video', 'Playlist'], width=100)
        add_dummy()
        add_text('URL:')
        add_input_text(name='##url', width=300, callback=None, hint='https://www.youtube.com/...')
        add_dummy()
        add_text('Output folder:')
        add_input_text(name='##dest', width=300, readonly=True)
        add_same_line()
        add_button(name='SET',
                   callback=lambda: select_directory_dialog(callback=lambda s, d: set_value('##dest', d[0])),
                   enabled=True)
        add_dummy()
        add_text(name='Format: ')
        add_combo(name='##format', items=['mp3', 'mp4'], width=100)
        add_dummy()
        add_button(name='START', callback=start, height=30, width=50)
        set_item_color(item='START', style=mvGuiCol_Button, color=[0, 200, 0, 150])
        add_dummy(height=30)
        add_table('##table', headers=['Type', 'Message', 'Open'], width=650, height=500, callback=table_cb)


def init():
    # Set layout
    layout()
    # Load config
    load_conf()
    # Center app on screen
    screen_width, screen_height = size()
    set_main_window_size(width=700, height=900)
    set_main_window_pos(x=int(screen_width / 4), y=int(screen_height / 4))
    # Render
    set_main_window_title(title='PyTube')
    start_dearpygui(primary_window='main_window')


if __name__ == '__main__':
    init()

