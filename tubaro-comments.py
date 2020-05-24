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
import sqlite3

COMMENT_DB_SCHEMA = """
create table if not exists comment (
 video text not null,
 num integer not null,
 message_id integer not null,
 primary key (video, num)
)
"""

class SendMessageException(Exception):
    pass

def send_message(args):
    try:
        req = urllib.request.Request(send_message_url,
                                     json.dumps(args).encode('utf-8'))
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        rep = json.load(io.TextIOWrapper(urllib.request.urlopen(req), 'utf-8'))
    except (urllib.error.URLError,
            urllib.error.HTTPError,
            json.JSONDecodeError) as e:
        raise SendMessageException(e)

    try:
        if rep['ok'] is not True:
            raise SendMessageException("Unexpected response from "
                                       "sendMessage request")
        return rep['result']['message_id']
    except KeyError as e:
        raise SendMessageException(e)

def get_feed():
        req = urllib.request.Request("https://tubaro.aperu.net/comments/feed/")
        return ET.parse(io.TextIOWrapper(urllib.request.urlopen(req), 'utf-8'))

def get_comment_db():
    global comment_db
    global comment_db_cursor
    global comment_db_filename

    if comment_db is None:
        comment_db = sqlite3.connect(comment_db_filename)

    if comment_db_cursor is None:
        comment_db_cursor = comment_db.cursor()
        comment_db_cursor.execute(COMMENT_DB_SCHEMA)
        comment_db.commit()

    return comment_db_cursor

def split_comment_url(comment_url):
    m = re.match(r'https?://[a-z\.]+/v/([^/]+)/#comment-(\d+)$', comment_url)

    if m is None:
        return None

    return m.group(1), int(m.group(2))

def add_comment_id(comment_url, comment_id):
    parts = split_comment_url(comment_url)
    if parts is None:
        return

    c = get_comment_db()
    c.execute("insert or ignore "
              "into comment(video, num, message_id) "
              "values (?, ?, ?)",
              (parts[0], parts[1], comment_id))
    comment_db.commit()

def get_comment_parent(comment_url):
    parts = split_comment_url(comment_url)
    if parts is None:
        return None

    if re.search(r"['\"\]]", comment_url):
        return None

    try:
        req = urllib.request.Request(comment_url)
        lines = list(io.TextIOWrapper(urllib.request.urlopen(req), 'utf-8'))
    except Exception(e):
        return None

    stack = []
    start_re = re.compile(r'\s*<li\s+id="comment-(\d+)"')
    end_re = re.compile(r'\s*</li>\s*<!--\s*#comment-##\s*-->')

    for line in lines:
        md = start_re.match(line)
        if md:
            id = int(md.group(1))
            if id == parts[1]:
                if len(stack) > 0:
                    return stack[-1]
                else:
                    return None
            stack.append(id)
            continue
        md = end_re.match(line)
        if md:
            if len(stack) <= 0:
                return None
            stack.pop()
            continue

def get_reply_id(comment_url):
    parts = split_comment_url(comment_url)
    if parts is None:
        return

    parent_id = get_comment_parent(comment_url)
    if parent_id is None:
        return

    c = get_comment_db()
    c.execute("select message_id from comment where video=? and num=?",
              (parts[0], parent_id))

    res = c.fetchone()
    if res is None:
        return None

    return int(res[0])

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
messages = []

comment_db = None
comment_db_cursor = None
comment_db_filename = os.path.join(conf_dir, "tubaro-comments.db")

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
        no_reply = re.sub(r'^\s*Responde al .*\n*', '', no_ents)
        parts.append(html.escape(no_reply.strip()))

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
    link_url = None

    if link is not None:
        link_url = link.text

        parts.append("<a href=\"{}\">{}</a>".
                     format(html.escape(link_url, quote=True),
                            title_text))
    elif title_element:
        parts.append("<b>{}</b>".format(title_text))

    messages.append((pub_date, "\n\n".join(parts), link_url))

messages.sort()

for pub_date, message, link_url in messages:
    args = {
        'chat_id' : channel_name,
        'text': message,
        'parse_mode' : 'HTML'
    }

    if link_url is not None:
        reply_id = get_reply_id(link_url)
        if reply_id is not None:
            args['reply_to_message_id'] = reply_id

    while True:
        try:
            message_id = send_message(args)
        except SendMessageException as e:
            try:
                args.pop('reply_to_message_id')
                continue
            except KeyError:
                raise e
        break

    if link_url is not None:
        add_comment_id(link_url, message_id)

with open(comment_date_file, "w") as f:
    print(max(last_comment_date, best_date), file=f)
