#!/usr/bin/env python3
import time
from datetime import datetime

import os
import re
import time
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

# === CONFIGURATION ===
FEED_FILE = "feed.atom"
OUTPUT_DIR = "site"
PAGES_DIR = os.path.join(OUTPUT_DIR, "pages")
BASE_URL = "https://yourblog.blogspot.com"  # Change this to your blog's domain

# === Ensure output directories exist ===
os.makedirs(PAGES_DIR, exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

# === Process each entry ===
for entry in root.findall("atom:entry", ns):
    title_elem = entry.find("atom:title", ns)
    
    if title_elem is not None and title_elem.text:
        raw_title = title_elem.text.strip()
        print(raw_title)

def main():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"[{now}] Logger action ran.")


if __name__ == "__main__":
    main()
