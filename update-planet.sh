#!/bin/bash

set -e

python2 ~/venus/planet.py ~/venus/blogoj.ini
~/venus/forward-blogs.py
