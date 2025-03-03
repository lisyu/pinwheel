# pinwheel.py

Simple reaction-based pin manager Discord bot. Built in [Python](http://python.org) 3.6.

If you would like to add the bot to your server, use [this link](https://discordapp.com/api/oauth2/authorize?client_id=609078174193680384&permissions=75776&scope=bot).

If you would like to deploy your own instance of the bot, follow the setup instructions below:

## Setup

Must have Python v.3 installed.

Pinwheel requires the following Python dependences:
- `discord.py`
- `emoji`

You can install all the required dependencies at once with `pip3` using this command:

```
pip3 install -r requirements.txt
```

### Discord Authentication

Copy the file `auth.json.example` to `auth.json`. You can do this with the following command:

```
cp auth.json.example auth.json
```

Replace the field `<AUTH TOKEN>` in `auth.json` with the authentication token from your Discord bot's portal. Check out `discord.py`'s guide on creating a bot account [here](https://discordpy.readthedocs.io/en/latest/discord.html#creating-a-bot-account) for a quick tutorial on setting up this auth token.

## Running the Bot

Launch the bot with the following command:

```
python3 pinwheel.py
```

Make sure the `package.json` and `auth.json` files are up to date. The `token` line in `auth.json` is required for Discord authentication.


If you want to run the bot in the background (i.e., bot doesn't shut down when terminal is closed), you can use the following command:

```
nohup python3 -u pinwheel.py > output.log &
```

This will launch the bot in the background and write all its output logs to the file `output.log`. 
