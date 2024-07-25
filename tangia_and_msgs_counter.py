import json
import tkinter as tk
from tkinter import ttk
import re
import threading
import socket
from time import sleep

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


class ChatReaderBot(Bot):
    def action(self, username, msg):
        global commands
        global top_users

        global tangia_count
        tangia_count = 0
        try:
            with open(tangia_count_file, 'r') as f:
                tangia_count = int(f.read())
        except FileNotFoundError:
            with open(tangia_count_file, 'w') as f:
                f.write(str(tangia_count))

        # ignore the commmands from the bot
        if msg not in commands:
            # check if tangia message
            if(username.lower() == "Tangiabot".lower()):
                tangia_count += 1
                save_tangia_count()
                tangia_label.config(text=f'Tangia: {tangia_count}')

            # add counter of the user
            if username in top_users:
                top_users[username] += 1
            else:
                top_users[username] = 1
            save_top_users()
            last_user.config(text=f'Last user: {username}')


bot = None
def start_bot():
    global bot
    bot = ChatReaderBot(channel=f"#{NICK}")
    bot.run()

def stop():
    global bot
    bot.stop()
    bot_thread.join()

bot_thread = None
def start():
    global bot_thread
    # Initialize and start the thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

def on_closing():
    global bot_thread

    if bot_thread is not None and bot_thread.is_alive():
        stop()
    
    root.destroy()


tangia_count_file = "tangia.txt"
top_users_msg_file = "top_users.json"

# top_users is a dictionary with the user as key and the number of messages as value
top_users = {}
try:
    with open(top_users_msg_file, 'r') as f:
        top_users = json.load(f)
except FileNotFoundError:
    with open(top_users_msg_file, 'w') as f:
        json.dump(top_users, f)

def save_top_users():
    with open(top_users_msg_file, 'w') as f:
        json.dump(top_users, f)

# tangia count file contains the number of tangia bits
tangia_count = 0
try:
    with open(tangia_count_file, 'r') as f:
        tangia_count = int(f.read())
except FileNotFoundError:
    with open(tangia_count_file, 'w') as f:
        f.write(str(tangia_count))

def save_tangia_count():
    with open(tangia_count_file, 'w') as f:
        f.write(str(tangia_count))


if __name__ == '__main__':
    with open('settings.json', 'r') as f:
        settings = json.load(f)
        NICK = settings['NICK']
        PASS = settings['PASS']
        commands = settings['commands']

    HOST = "irc.chat.twitch.tv"
    PORT = 6667

    root = tk.Tk()
    root.title('Chat Reader')
    root.geometry('400x150')

    style = ttk.Style()
    style.theme_use('clam')  # You can choose 'clam', 'alt', 'default', or 'classic'
    color = 'white'
    root.configure(bg=color)

    title_label = ttk.Label(root, text='Reading the chat...', font=('Helvetica', 20), background=color)
    title_label.pack(pady=10)

    last_user = ttk.Label(root, text='Last user: ', font=('Helvetica', 16), background=color)
    last_user.pack(pady=10)

    tangia_label = ttk.Label(root, text=f'Tangia: {tangia_count}', font=('Helvetica', 16), background=color)
    tangia_label.pack(pady=10)
    
    start()  # Start the bot in a separate thread
    root.protocol("WM_DELETE_WINDOW", on_closing)  # Handle window close event
    root.mainloop()
