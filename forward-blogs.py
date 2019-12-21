#!/usr/bin/python3

import urllib.request
import json
import io
import html
import sys
import time
import os
import random
import re
import glob
import xml.etree.ElementTree as ET
import twitter

twitter_api = None

class SendMessageException(Exception):
    pass

def send_message(args):
    try:
        req = urllib.request.Request(send_message_url,
                                     json.dumps(args).encode('utf-8'))
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        rep = json.load(io.TextIOWrapper(urllib.request.urlopen(req), 'utf-8'))
    except urllib.error.URLError as e:
        raise SendMessageException(e)
    except json.JSONDecodeError as e:
        raise SendMessageException(e)

    try:
        if rep['ok'] is not True:
            raise SendMessageException("Unexpected response from "
                                       "sendMessage request")
    except KeyError as e:
        raise SendMessageException(e)

def send_toot(content):
    try:
        args = { 'status': content, 'language': 'eo' }
        req = urllib.request.Request(masto_url,
                                     json.dumps(args).encode('utf-8'))
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Authorization', 'Bearer ' + mastokey)
        rep = json.load(io.TextIOWrapper(urllib.request.urlopen(req), 'utf-8'))
    except urllib.error.URLError as e:
        raise SendMessageException(e)
    except json.JSONDecodeError as e:
        raise SendMessageException(e)

    try:
        if 'id' not in rep:
            raise SendMessageException("Unexpected response from "
                                       "sendMessage request")
    except KeyError as e:
        raise SendMessageException(e)

def send_to_telegram(title, link):
    args = {
        'chat_id' : channel_name,
        'text' : '<a href="{}">{}</a>'.format(html.escape(link, quote=True),
                                              html.escape(title)),
        'parse_mode' : 'HTML'
    }
    send_message(args)

def send_to_mastodon(title, link):
    send_toot("{}\n\n{}".format(title, link))

def send_to_twitter(title, link):
    global twitter_api
    if twitter_api is None:
        twitter_api = twitter.Api(twitterkeys['api_key'],
                                  twitterkeys['api_secret_key'],
                                  twitterkeys['access_token'],
                                  twitterkeys['access_token_secret'])

    twitter_api.PostUpdate("{}\n{}".format(title, link))

def send_entry(title, link):
    send_to_telegram(title, link)
    send_to_mastodon(title, link)
    send_to_twitter(title, link)

def get_link(root):
    for link in root.findall("./{http://www.w3.org/2005/Atom}link"):
        rel = link.get("rel", "alternate")
        if rel != "alternate":
            continue

        link = link.get("href")
        if link is None:
            continue

        return link
    
    return None

conf_dir = os.path.expanduser("~/.esperantose")

apikey_file = os.path.join(conf_dir, "apikey")
with open(apikey_file, 'r', encoding='utf-8') as f:
    apikey = f.read().rstrip()

mastokey_file = os.path.join(conf_dir, "mastokey")
with open(mastokey_file, 'r', encoding='utf-8') as f:
    mastokey = f.read().rstrip()

twitterkeys_file = os.path.join(conf_dir, "twitterkeys")
with open(twitterkeys_file, 'r', encoding='utf-8') as f:
    twitterkeys = json.load(f)

urlbase = "https://api.telegram.org/bot" + apikey + "/"
send_message_url = urlbase + "sendMessage"
channel_name = "@blogaro"

masto_url = "https://tvitero.com/api/v1/statuses"

try:
    with open(os.path.expanduser("~/.sent-links")) as f:
        sent_links = set(line.rstrip() for line in f)
except FileNotFoundError:
    sent_links = set()

for fn in glob.glob(os.path.expanduser("~/planet/pscache/*")):
    if not os.path.isfile(fn):
        continue

    tree = ET.parse(fn)
    root = tree.getroot()

    link = get_link(root)
    if link is None:
        continue

    if link in sent_links:
        continue

    title = root.find("./{http://www.w3.org/2005/Atom}title")
    if title is None:
        continue

    title = "".join(title.itertext())

    send_entry(title, link)

    sent_links.add(link)

with open(os.path.expanduser("~/.sent-links"), "w") as f:
    for link in sent_links:
        print(link, file=f)
