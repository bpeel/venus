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
import datetime
import dateutil.parser
import subprocess

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

if len(sys.argv) != 2:
    exit_code = 0

    for mode in ['telegram', 'mastodon']:
        rc = subprocess.run([sys.argv[0], mode])
        if rc != 0:
            exit_code = 1

    sys.exit(exit_code)
    assert(False)

mode = sys.argv[1]
send_entry = globals()['send_to_{}'.format(mode)]
sent_links_file = os.path.expanduser("~/.sent-links-" + mode)

conf_dir = os.path.expanduser("~/.esperantose")

apikey_file = os.path.join(conf_dir, "apikey")
with open(apikey_file, 'r', encoding='utf-8') as f:
    apikey = f.read().rstrip()

mastokey_file = os.path.join(conf_dir, "mastokey")
with open(mastokey_file, 'r', encoding='utf-8') as f:
    mastokey = f.read().rstrip()

urlbase = "https://api.telegram.org/bot" + apikey + "/"
send_message_url = urlbase + "sendMessage"
channel_name = "@blogaro"

masto_url = "https://tvitero.com/api/v1/statuses"

try:
    with open(sent_links_file) as f:
        sent_links = set(line.rstrip() for line in f)
except FileNotFoundError:
    sent_links = set()

now = datetime.datetime.now(datetime.timezone.utc)
max_date_diff = datetime.timedelta(days=1)

for fn in glob.glob(os.path.expanduser("~/planet/pscache/*")):
    if not os.path.isfile(fn):
        continue

    try:
        tree = ET.parse(fn)
    except ET.ParseError as e:
        print(f"Error parsing {fn}: {e}", file=sys.stderr)
        continue

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
    if not re.search(r'\S', title):
        continue

    updated = root.find("./{http://www.w3.org/2005/Atom}updated")
    if updated is None:
        continue

    updated = "".join(updated.itertext())
    try:
        updated = dateutil.parser.parse(updated)
    except ValueError:
        continue

    if now - updated <= max_date_diff:
        send_entry(title, link)

    sent_links.add(link)

    with open(sent_links_file, 'a') as f:
        print(link, file=f)
