#!/usr/bin/python3

# Author: Dany Vohl (vohl (at) astron.nl)
# Written in 2020

import requests
import time
import datetime
import copy
import os
import json
import sys
import pickle
import numpy as np
from slack import WebClient
from slack.errors import SlackApiError


SOURCE_PARAMS = ["last_burst_date", "dm", "ne2001", "ymw16", "localized", "ra", "dec", "gl", "gb", "publication"]
CHANNEL = '#chime-observer'
WAIT_MINUTES = 10

def send_message_to_slack(blocks, debug=False):
    if debug:
        print (json.dumps(blocks))
        print ()
    else:
        print ('Sending:', blocks)
        print ()
        client = WebClient(token=os.environ["SLACK_API_TOKEN"])
        try:
            response = client.chat_postMessage(
                channel=CHANNEL,
                mrkdwn=True,
                blocks=json.dumps(blocks)
            )
        except SlackApiError as e:
            assert e.response["ok"] is False
            assert e.response["error"]
            print("Got an error: %s" % (e.response["error"]))
            print(blocks)
            print()

            if e.response["error"] == "not_in_channel":
                resp = client.conversations_list(types="public_channel")['channels']
                print(resp)
                channel_id = [channel['id'] for channel in resp if channel['name'] == CHANNEL[1:]][0]
                client.conversations_join(channel=channel_id)
    return []


def send_message(source, source_dict, date=None, debug=False):
    blocks = []
    # Case 1. New FRB source
    if date is None:
        text = "New FRB source: *%s*\n" % (source)
        # Skipping latest_burst_date as all instances are empty.
        for param in SOURCE_PARAMS[1:]:
            try:
                text += "*%s*: %s\n" % (
                    source_dict[param]["display_name"],
                    source_dict[param]["value"]
                )
            except:
                text += "*%s*: %s\n" % (
                    param,
                    source_dict[param]["value"]
                )
        message = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }

        blocks.append(message)
        blocks.append({"type": "divider"})

        for date in source_dict.keys():
            text = ""
            if date not in SOURCE_PARAMS:
                text += "*%s* (%s)\n" % (source_dict[date]['timestamp']["value"], source)
                for var in np.sort(list(source_dict[date].keys())):
                    if var not in ["value", "timestamp"]:
                        if True not in [True if "error" in k else False for k in list(source_dict[date][var].keys())]:
                            try:
                                text += "*%s*: %.1f\n" % (
                                    source_dict[date][var]["display_name"],
                                    source_dict[date][var]["value"]
                                )
                            except TypeError:
                                text += "*%s*: %s\n" % (
                                    source_dict[date][var]["display_name"],
                                    'n/a'
                                )
                        else:
                            try:
                                text += "*%s*: %.1f (%.2f)\n" % (
                                    source_dict[date][var]["display_name"],
                                    source_dict[date][var]["value"],
                                    source_dict[date][var]["error_high"],
                                )
                            except TypeError:
                                text += "*%s*: %s\n" % (
                                    source_dict[date][var]["display_name"],
                                    'n/a'
                                )

                        message = {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": text
                            }
                        }
                    else:
                        if var == "value":
                            text += "*%s*: %s\n" % (
                                var,
                                source_dict[date][var]["value"]
                            )
                text += "\n"

            if text != '':
                message = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text
                    }
                }
                blocks.append(message)
                blocks.append({"type": "divider"})
                blocks = send_message_to_slack(blocks, debug=debug)
                time.sleep(1)
    # Case 2. New detection from known source
    else:
        text = "New detection from *%s* on %s\n" % (source, date)
        # Skipping latest_burst_date as all instances are empty.
        for param in SOURCE_PARAMS[1:]:
            try:
                text += "*%s*: %s\n" % (
                    source_dict[param]["display_name"],
                    source_dict[param]["value"]
                )
            except:
                text += "*%s*: %s\n" % (
                    param,
                    source_dict[param]["value"]
                )
        message = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
        blocks.append(message)
        blocks.append({"type": "divider"})

        text = "*%s*\n" % source_dict[date]['timestamp']["value"]
        for var in np.sort(list(source_dict[date].keys())):
            if var not in ["value", "timestamp"]:
                if True not in [True if "error" in k else False for k in list(source_dict[date][var].keys())]:
                    try:
                        text += "*%s*: %.1f\n" % (
                            source_dict[date][var]["display_name"],
                            source_dict[date][var]["value"]
                        )
                    except TypeError:
                        text += "*%s*: %s\n" % (
                            source_dict[date][var]["display_name"],
                            'n/a'
                        )
                else:
                    try:
                        text += "*%s*: %.1f (%.2f)\n" % (
                            source_dict[date][var]["display_name"],
                            source_dict[date][var]["value"],
                            source_dict[date][var]["error_high"],
                        )
                    except TypeError:
                        text += "*%s*: %s\n" % (
                            source_dict[date][var]["display_name"],
                            'n/a'
                        )
            else:
                if var == "value":
                    text += "**%s**: %s\n" % (
                        var,
                        source_dict[date][var]["value"]
                    )
        if text != '':
            message = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            }
            blocks.append(message)
            blocks.append({"type": "divider"})
            blocks = send_message_to_slack(blocks, debug=debug)

def check_underscore(string):
    if string != '':
        if string[-1] != '_':
            string += '_'
    return string

def check_slash(string):
    if string != '':
        if string[-1] != '/':
            string += '/'
    return string

def save(variable, data, protocol=pickle.HIGHEST_PROTOCOL, state_prefix='', folder='states/'):
    if not os.path.exists(folder):
        os.makedirs(folder)

    if state_prefix != '':
        with open(check_slash(folder) + check_underscore(state_prefix) + variable + '.pickle', 'wb') as f:
            pickle.dump(data, f, protocol)
    else:
        with open(check_slash(folder) + variable + '.pickle', 'wb') as f:
            pickle.dump(data, f, protocol)

def load(variable, state_prefix='', folder='states/'):
    if state_prefix != '':
        if os.path.exists(folder + check_underscore(state_prefix) + variable + '.pickle'):
            with open(folder + check_underscore(state_prefix) + variable + '.pickle', 'rb') as f:
                loaded = pickle.load(f)
            return loaded
        else:
            return None
    else:
        if os.path.exists(folder + variable + '.pickle'):
            with open(folder + variable + '.pickle', 'rb') as f:
                loaded = pickle.load(f)
            return loaded
        else:
            return None

# debug=False
debug=True

# Main
last = load('latest', state_prefix='repeaters')
if last is None:
    last = {}

# loop forever
while True:
    try:
        latest = requests.post("https://catalog.chime-frb.ca/repeaters", data={}).json()

        if not last == latest:
            for source in latest.keys():
                # New FRB
                if source not in last.keys():
                    if debug:
                        print (source)
                        print ()
                    send_message(source, latest[source], debug=debug)
                else:
                    for date in latest[source].keys():
                        # New repeat burst
                        if date not in last[source].keys():
                            if debug:
                                print (date, source)
                                print ()
                            send_message(source, latest[source], date, debug=debug)

        last = latest
        if not debug:
            save('latest', state_prefix='repeaters', data=latest)
    except ValueError:
        print (datetime.datetime.utcnow().strftime("%A, %d. %B %Y %I:%M%p") + ' - Problem decoding JSON from query')
    if debug:
        print ('waiting for %d minutes' % WAIT_MINUTES)
    time.sleep(WAIT_MINUTES*60)
