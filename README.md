# Twitch Chat Plays - very easy version

Tested with [mGBA](https://mgba.io/downloads.html).

## Setup

- Get oAuth code from [here](https://twitchapps.com/tmi/), that will go in `settings.json` as **PASS**;
- set your channel name in `settings.json` as the **NICK**;
- add the dictionary of accepted commands in `settings.json` in **commands**, multiple messages can be added as the same command;
- the values in commands can be *single letters* (like `z`) or *special keys* (like `{RETURN}`, that needs to be in curly braces);
- if a command is an emote, it needs its image in the `Emotes/` folder (eg. if there is the `"ResidentSleeper": "{RIGHT}"` in `settings.json`, there needs to be a `Emotes/ResidentSleeper.png` file);

## Usage 

Load the ROM and when it starts (so when the name already has "*mGBA - Videogame...*") start the program, select the window from the list and press Start.

Every time a command is sent, the program will:
1. press the key associated with it;
2. overrides the user that sent it in the `last_command.txt` file;
3. add the command in the `commands_history.csv` file;
4. if the command is an emote, it overrides the `last_command.png` with the emote image from the `Emotes/` folder.

If in `settings.json` the **allow_multiple** parameter is set to `false`, the program will ignore a message if it's sent from the same user that sent the last command.