import discord
import pickle
import datetime as dt
import json
import asyncio
from emoji import UNICODE_EMOJI

# TODO(KYU): 
# - add console coloring ?

NAME = "Pinwheel Discord Bot"
SESSION_FILE = "server-configs.p"
AUTO_SAVE_SESSION_FILE = "server-configs-auto.p"

SAVE_DELAY = 30 # in minutes

FLAG = "p?"

GREET_MSG = "> **Howdy! I'm Pinwheel!**"
HELP_MSG = "> Available commands: `help` `status` `howdy` `setcount` `setemoji`"
DEV_MSG = "> Available dev commands: `savestate` `reset` `togglev` `lastlogin` `lastsave`"
STATUS_MSG = "> Right now I'm looking for posts with at least `{}` {} reacts."

PIN_EMOJI_DEFAULT = "📌"
MIN_COUNT_DEFAULT = 2

def log(message):
    print("[{}] {}".format(Timestamp(), message))

class Timestamp():
    def __init__(self):
        self.datetime_stamp = dt.datetime.today()

    def __str__(self):
        return "{}-{}-{} {}:{}:{}".format(
            self.datetime_stamp.year,
            self.datetime_stamp.month,
            self.datetime_stamp.day,
            self.datetime_stamp.hour,
            self.datetime_stamp.minute,
            self.datetime_stamp.second
            )


class Pinwheel():

    def __init__(self):
        ## Verbosity
        self.aggressive = False
        # Pin management variables
        self.pin_emoji = PIN_EMOJI_DEFAULT
        self.pin_count = MIN_COUNT_DEFAULT

    def get_greeting(self):
        return "{}\n{}".format(GREET_MSG, HELP_MSG)

    def get_status(self):
        return STATUS_MSG.format(self.pin_count, self.pin_emoji)

    def can_pin(self, reaction):
        return str(reaction.emoji) == self.pin_emoji and reaction.count == self.pin_count

    def set_count(self, num):
        # print("Set minimum required reaction count to {}".format(num))
        self.pin_count = num
        
    def set_emoji(self, s):
        # print("Set required reaction emoji to {}".format(s))
        self.pin_emoji = s
        
    def is_valid_emoji(self, s, guild):
        return s in UNICODE_EMOJI or s in [str(emoji) for emoji in guild.emojis]

        
class PinClient(discord.Client):

    def __init__(self):
        ## SERVER SETTINGS RETRIEVAL (CREATE NEW IF NOT FOUND)
        ## (DEFAULTS TO AUTOSAVE FILE)
        self.session_map = self.load_session(AUTO_SAVE_SESSION_FILE)

        ## For debug purposes
        self.last_login = Timestamp()
        self.last_save = "NOT SAVED"

        log("Session loaded.")
        
        super().__init__(activity=discord.Game(name="{}help".format(FLAG)))
        
    def save_session(self, filepath):
        """Save session map to file"""
        pickle.dump(self.session_map, open(filepath, "wb"))
        self.last_save = Timestamp()
    
    def load_session(self, filepath):
        """Load session map from file"""
        try:
            return pickle.load(open(filepath, "rb"))
        except EOFError:
            log("Session created.")
            return {}
        except FileNotFoundError:
            log("Session created.")
            return {}

    def get_config(self, server_id):
        """get Pinwheel session for the given server ID"""
        self.session_map[server_id] = self.session_map.get(server_id, Pinwheel())
        return self.session_map[server_id]

    def new_config(self, server_id):
        """assign fresh session to the given server"""
        self.session_map[server_id] = Pinwheel()

    async def auto_save(self):
        """Auto-saves every predetermined delay"""
        while True:
            await asyncio.sleep(60 * SAVE_DELAY)
            self.save_session(AUTO_SAVE_SESSION_FILE)
            log("Session saved to {}.".format(AUTO_SAVE_SESSION_FILE))

    ## COMMAND EXECUTION HELPERS

    async def try_admin_command(self, message, command):
        if message.author.permissions_in(message.channel).administrator:
            await command(message)
        else:
            await message.channel.send("Only admins can perform this command!")

    async def try_set_count(self, message):
        msg = message.content.split(" ")
        try:
            self.get_config(message.guild.id).set_count(int(msg[1]))
            await message.channel.send("Set reaction minimum to `{}`.".format(msg[1]))
        except IndexError:
            await message.channel.send("**Usage**: {}setcount `<new minimum count>`".format(FLAG))
        except ValueError:
            await message.channel.send("Please enter a valid number!")
    
    async def try_set_emoji(self, message):
        msg = message.content.split(" ")
        try:
            if self.get_config(message.guild.id).is_valid_emoji(msg[1], message.guild):
                self.get_config(message.guild.id).set_emoji(msg[1])
                await message.channel.send("Set reaction emoji to {}.".format(msg[1]))
            else:
                await message.channel.send("Please enter a valid emoji!")
        except IndexError:
            await message.channel.send("**Usage**: {}setemoji `<new reaction emoji>`".format(FLAG))

    async def try_pin(self, message):
        log("Pinning post #{} in {}...".format(message.id, message.guild.name))
        if self.get_config(message.guild.id).aggressive:
            await message.channel.send("`You. Come closer.`")
        await message.pin()
        
    ## EVENT LISTENERS

    async def on_connect(self):
        self.last_login = Timestamp()
        log('Successfully connected.')

    async def on_disconnect(self):
        log('Disconnected from server. Attempting reconnect...')
    
    async def on_ready(self):
        log('Successfully logged in as {0.user}.'.format(self))
        self.loop.create_task(self.auto_save())
        
    async def on_message(self, message):
        if message.author == self.user:
            return
    
        ## GENERAL COMMANDS -------------------------------------------
        # GET HELP MESSAGE
        elif message.content == "{}help".format(FLAG):
            await message.channel.send(self.get_config(message.guild.id).get_greeting())
            await message.channel.send(self.get_config(message.guild.id).get_status())

        # GET DEV HELP MESSAGE
        elif message.content == "{}:help".format(FLAG):
            await message.channel.send(self.get_config(message.guild.id).get_greeting())
            await message.channel.send(DEV_MSG)

        # GET GREETING
        elif message.content == "{}howdy".format(FLAG):
            await message.channel.send("Howdy!")

        # GET STATUS MESSAGE
        elif message.content == "{}status".format(FLAG):
            await message.channel.send(self.get_config(message.guild.id).get_status())

        # CHANGE REACTION REQ COUNT
        elif message.content.startswith("{}setcount".format(FLAG)):
            # Only allow command for admins (TODO: change?)
            await self.try_admin_command(message, self.try_set_count)
            
        # CHANGE REACTION EMOJI
        elif message.content.startswith("{}setemoji".format(FLAG)):
            # Only allow command for admins (TODO: change?)
            await self.try_admin_command(message, self.try_set_emoji)

        ## DEV COMMANDS --------------------------------------------------------            
        # SAVE SESSIONMAP
        elif message.content == "{}:savestate".format(FLAG):
            try:
                self.save_session(SESSION_FILE)
                await message.channel.send("Session saved successfully.")
            except IOError:
                await message.channel.send("Couldn't save session!")

        # RESET CONFIG
        elif message.content == "{}:reset".format(FLAG):
            self.new_config(message.guild)
            log("Reset config for server {}.".format(message.guild.name))
            await message.channel.send("Server config reset.")

        # TOGGLE AGGRESSION
        elif message.content == "{}:togglev".format(FLAG):
            this_server = self.get_config(message.guild.id)
            this_server.aggressive = not this_server.aggressive
            await message.channel.send("Set verbosity to `{}`.".format(this_server.aggressive))

        # GET LAST LOGIN
        elif message.content == "{}:lastlogin".format(FLAG):
            await message.channel.send("Last login was at time `{}`.".format(self.last_login))
            
        elif message.content == "{}:lastsave".format(FLAG):
            await message.channel.send("Last save was at time `{}`.".format(self.last_save))

    async def on_raw_reaction_add(self, payload):
        channel = await self.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.pinned == False:
            for reaction in message.reactions:
                if self.get_config(payload.guild_id).can_pin(reaction):
                    await self.try_pin(message)
                    return

            
def main():              
    token = json.load(open("auth.json"))["token"]
    module_info = json.load(open("package.json"))

    print(NAME + " ({})".format(module_info["version"]))
    client = PinClient()
    client.run(token)

main()