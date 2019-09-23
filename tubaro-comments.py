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
import email.utils

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

def get_feed():
        req = urllib.request.Request("https://tubaro.aperu.net/comments/feed/")
        return ET.parse(io.TextIOWrapper(urllib.request.urlopen(req), 'utf-8'))

conf_dir = os.path.expanduser("~/.esperantose")

apikey_file = os.path.join(conf_dir, "apikey")
with open(apikey_file, 'r', encoding='utf-8') as f:
    apikey = f.read().rstrip()

comment_date_file = os.path.join(conf_dir, "tubaro-comments-date")
try:
    with open(comment_date_file, 'r', encoding='utf-8') as f:
        last_comment_date = int(f.read())
except FileNotFoundError:
    last_comment_date = 0

urlbase = "https://api.telegram.org/bot" + apikey + "/"
send_message_url = urlbase + "sendMessage"
channel_name = "@tubarokomentoj"

root = get_feed().getroot()

best_date = 0

for item in root.findall("./channel/item"):
    pub_date_element = item.find("./pubDate")
    if pub_date_element is None:
        continue

    pub_date_tuple = email.utils.parsedate_tz(pub_date_element.text)
    pub_date = email.utils.mktime_tz(pub_date_tuple)

    if pub_date <= last_comment_date:
        continue

    best_date = max(best_date, pub_date)
    
    parts = []

    creator = item.find("./{http://purl.org/dc/elements/1.1/}creator")
    if creator is not None:
        parts.append("<b>{}</b>".format(html.escape(creator.text)))

    description = item.find("./{http://purl.org/rss/1.0/modules/content/}"
                            "encoded")
    if description is not None:
        no_p = re.sub('</p>', "\n\n", description.text)
        no_tags = re.sub(r'<[^>]+>', '', no_p)
        no_ents = html.unescape(no_tags)
        parts.append(html.escape(no_ents.strip()))

    title_element = item.find("./title")
    if title_element is not None:
        title_text = title_element.text.strip()
        md = re.match(r'Komentoj +pri +(.*)', title_text)
        if md:
            title_text = md.group(1)
        title_text = html.escape(title_text)

        if creator is not None:
            md = re.search(r'(.*?) de {}$'.format(re.escape(creator.text)),
                           title_text)
            if md:
                title_text = md.group(1)
    else:
        title_text = "Ligilo"

    link = item.find("./link")
    if link is not None:
        parts.append("<a href=\"{}\">{}</a>".
                     format(html.escape(link.text, quote=True),
                            title_text))
    elif title_element:
        parts.append("<b>{}</b>".format(title_text))

    args = {
        'chat_id' : channel_name,
        'text': "\n\n".join(parts),
        'parse_mode' : 'HTML'
    }

    send_message(args)

with open(comment_date_file, "w") as f:
    print(max(last_comment_date, best_date), file=f)
