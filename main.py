import pygetwindow as gw
import json
from pywinauto.application import Application
import tkinter as tk
from tkinter import ttk
import re
import threading
import socket
import pandas as pd
from time import sleep
from PIL import Image
from glob import glob


# from https://github.com/rokkuran/twitchbot
class Bot(object):
    def __init__(self, channel, n_msg_per_sec=100):
        super(Bot, self).__init__()
        self._nickname = NICK
        self.channel = channel
        self.connect(channel)
        print("{} {}\n{}".format(NICK, channel, '-' * (len(NICK + channel) + 1)))

        self._msg_count = 0
        self.n_msg_per_sec = n_msg_per_sec
        self.running = True  # Flag to control the bot's running state

    def connect(self, channel):
        self._socket = socket.socket()
        self._socket.connect((HOST, PORT))
        self._socket.send("PASS {}\r\n".format(PASS).encode("utf-8"))
        self._socket.send("NICK {}\r\n".format(NICK).encode("utf-8"))
        self._socket.send("JOIN {}\r\n".format(channel).encode("utf-8"))

    def _ping_pong(self, response):
        if response == "PING :tmi.twitch.tv\r\n":
            # send pong back to prevent timeout
            self._socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            return True
        else:
            return False

    def _get_response(self):
        try:
            response = self._socket.recv(1024).decode("utf-8")
        except UnicodeDecodeError as e:
            print('\n\n%s\n\n' % e)
            return False

        if self._ping_pong(response):
            return False
        elif ':tmi.twitch.tv' in response:
            return False
        elif '.tmi.twitch.tv JOIN' in response:
            return False
        else:
            return response

    def _process_msg(self, response):
        username = re.search(r"\w+", response).group(0)
        mask = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")
        message = mask.sub("", response).strip('\r\n')
        return username, message

    def chat(self, msg):
        self._socket.send("PRIVMSG {} :{}\r\n".format(self.channel, msg).encode("utf-8"))

    def action(self, username, msg):
        print(username + ": " + msg)

    def run(self):
        while self.running:
            response = self._get_response()
            if response:
                username, msg = self._process_msg(response)
                self.action(username, msg)
            sleep(1 / float(self.n_msg_per_sec))

    def stop(self):
        self.running = False
        self._socket.close()

emotes = glob('Emotes/*.png')
emotes = [emote.split('\\')[1].split('.')[0] for emote in emotes]


class ChatPlaysBot(Bot):
    def action(self, username, msg):
        global emulator_window
        global commands
        global last_user
        global last_command
        global last_command_label
        global emotes
        # check if the message is a command
        if msg in commands and (allow_multiple or username != last_user):
            # save the command to the history
            commands_history.loc[len(commands_history)] = [username, msg, commands[msg]]
            commands_history.to_csv('commands_history.csv', index=False)
            print(f'{username} -> {commands[msg]}')
            # if the command is an emote, update the image (for OBS usage)
            if msg in emotes:
                image_to_save = Image.open(f'Emotes/{msg}.png')
                image_to_save.save('last_command.png')
            last_user = username
            last_command = commands[msg]
            last_command_label.config(text=f'Last command: {last_user} -> {last_command}')
            # save the last user to a file
            with open(last_command_file, 'w') as f:
                f.write(f'{last_user} -> \n')
            # send the command to the emulator
            emulator_window.send_keystrokes(f"{"".join([commands[msg] for _ in range(num)])}")

def start_bot():
    global emulator_window
    title_re = re.compile(variable.get()[:20])
    app = Application().connect(title_re=title_re)
    emulator_window = app.window(title_re=title_re)
    global bot
    bot = ChatPlaysBot(channel=f"#{NICK}")
    bot.run()

def start():
    global bot_thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()
    status_label.config(text='Bot started')
    global button
    button.config(text='Stop', command=stop) 

def stop():
    global bot
    bot.stop()
    bot_thread.join()
    status_label.config(text='Bot stopped')
    button.config(text='Start', command=start)
bot_thread = False
def on_closing():
    if not bot_thread:
        root.destroy()
        exit()
    elif bot_thread.is_alive():
        stop()
    root.destroy()


commands_history = pd.read_csv('commands_history.csv') # user, msg, command


if __name__ == '__main__':
    emulator_window = None
    last_user = None
    last_command = None
    last_command_file = "last_command.txt"

    
    f = open('settings.json', 'r')
    settings = json.load(f)
    with open('settings.json', 'r') as f:
        NICK = settings['NICK']
        PASS = settings['PASS']
        allow_multiple = settings['allow_multiple']
        commands = settings['commands']
        num = settings['num_default_6'] # number of times to repeat the command, because sometimes it's too fast

    HOST = "irc.chat.twitch.tv"
    PORT = 6667

    root = tk.Tk()
    root.title('Chat Plays')
    root.geometry('420x300')

    style = ttk.Style()
    style.theme_use('clam')  # You can choose 'clam', 'alt', 'default', or 'classic'
    color = 'white'
    root.configure(bg=color)

    title_label = ttk.Label(root, text='Chat Plays', font=('Helvetica', 20), background=color)
    title_label.pack(pady=10)

    select_label = ttk.Label(root, text='Select the window:', font=('Helvetica', 16), background=color)
    select_label.pack(pady=10)

    options = [x for x in gw.getAllTitles() if x.strip() != '']
    variable = tk.StringVar(root)
    variable.set(options[0])
    dropdown = ttk.Combobox(root, textvariable=variable, values=options, width=50)
    dropdown.pack(pady=10)

    button = ttk.Button(root, text='Start', command=start, width=20)
    button.pack(pady=10)

    status_label = ttk.Label(root, text='Click the button to start the bot', font=('Helvetica', 12), background=color)
    status_label.pack(pady=10)

    last_command_label = ttk.Label(root, text='Last command: ', font=('Helvetica', 16), background=color)
    last_command_label.pack(pady=10)

    root.protocol("WM_DELETE_WINDOW", on_closing)  # Handle window close event
    root.mainloop()
