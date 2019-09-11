#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import sys
import re

FILTER_RE = re.compile(r'^(?:https?://)?teokajlibroj.wordpress.com/')

content = sys.stdin.read()

def skip():
    sys.stdout.write(content)
    sys.exit(0)

try:
    root = ET.fromstring(content)
except ET.ParseError:
    skip()

link = root.find("./{http://www.w3.org/2005/Atom}link[@rel='alternate']")
if link is None:
    skip()

href = link.get("href")

if not FILTER_RE.search(href):
    skip()

summary = root.find("./{http://www.w3.org/2005/Atom}summary")
summary.text = None
for child in list(summary):
    summary.remove(child)

pnode = ET.SubElement(summary, 'p')
anode = ET.SubElement(pnode, 'a')
anode.set("href", href)
anode.text = "Legu pli"

print('<?xml version="1.0"?>')
ET.dump(root)
