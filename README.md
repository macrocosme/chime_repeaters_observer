# CHIME repeaters observer

Python script to query the CHIME repeaters page \([http://chime-frb.ca/repeaters](http://chime-frb.ca/repeaters)\) repetitively. Upon (a) new burst(s) announcement, the script will send a message with burst(s) details to a slack channel.

## Before we start

1) Create a new app for your [Slack workspaces](https://api.slack.com/apps), providing the following scopes rights to allow you to modify previous message programmatically if required:  \[channels:history,
chat:write,
files:write,
groups:history,
im:write\].

2) Generate a "Bot User OAuth Access Token" and store it somewhere safe, to be loaded as an environement variable called `SLACK_API_TOKEN`, which will be used by the script.

3) Create a dedicated channel (if desired). You then need to set the `CHANNEL` variable with this channel name; e.g. `CHANNEL = '#chime-repeaters-observer'`.

## Prerequisites and execution

Install required packages included in requirements.txt. I suggest to run the following in a virtual environment. Example:

```shell
cd /home/<user>/<path_to_chime_repeaters_observer>

# (Install virtualenv if necessary)
pip3 install virtualenv

# Create a virtual environment coined `topology-env` for the project
virtualenv env

# Activate the environment
source env/bin/activate

# Install required packages
pip3 install -r requirements.txt

# Make script executable
chmod +x chime_repeaters_observer.py

# Start the script
run_path=/home/<user>/<path_to_chime_repeaters_observer>
/usr/bin/nohup $run_path/chime_repeaters_observer.py 2>&1 >> $run_path/chime_repeaters_observer.log &

# Deactivate when done working on this project to return to global settings
deactivate
```

## Notes on current version
No main has been written so far, as it seemed unnecessary. Also, note that I have set a variable called `debug` to `True` by default. It would simply print what would be sent to slack. If `debug = False`, it will start sending messages. By default, a query to CHIME's server is done every 10 minutes. This can be changed by modifying the variable `WAIT_MINUTES` near the beginning of the script. `nohup`'s tip came from Leon Oostrum. `requests.post("https://catalog.chime-frb.ca/repeaters", data={}).json()` came from David Gardenier. Hence, kudos to them. 

----
Copyright (c) Dany Vohl / macrocosme, 2020.
