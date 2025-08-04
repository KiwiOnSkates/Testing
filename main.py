import os
import re
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser

# === CONFIGURATION ===
FEED_FILE = "feed.atom"
OUTPUT_DIR = "site"
POSTS_DIR = os.path.join(OUTPUT_DIR, "posts")
BASE_URL = "https://yourblog.blogspot.com"  # Change to your blog's domain

# === Ensure output directories exist ===
os.makedirs(POSTS_DIR, exist_ok=True)

# === Link extractor from <a href="..."> ===
class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for key, value in attrs:
                if key == "href" and value.startswith("/"):
                    self.links.append(value)

# === Replace relative links in post content to local post filenames ===
def replace_relative_links(content_html):
    # Replace href="/some/path/post.html" with href="post.html" (same folder)
    def repl(match):
        href = match.group(1)
        filename = os.path.basename(href)
        return f'href="{filename}"'
    
    return re.sub(r'href="(/[^"]+)"', repl, content_html)

# === Load Atom feed ===
tree = ET.parse(FEED_FILE)
root = tree.getroot()
ns = {'atom': 'http://www.w3.org/2005/Atom'}

index_entries = []
untitled_count = 0
used_slugs = set()

# === Process each entry ===
for entry in root.findall("atom:entry", ns):
    title_elem = entry.find("atom:title", ns)
    content_elem = entry.find("atom:content", ns)

    if content_elem is None:
        continue

    if title_elem is not None and title_elem.text:
        raw_title = title_elem.text.strip()
        slug = re.sub(r"[^\w\-]+", "-", raw_title.lower()).strip("-") or "untitled"
    else:
        untitled_count += 1
        raw_title = f"Untitled {untitled_count}"
        slug = f"untitled-{untitled_count}"

    orig_slug = slug
    i = 1
    while slug in used_slugs:
        slug = f"{orig_slug}-{i}"
        i += 1
    used_slugs.add(slug)

    filename = f"{slug}.html"
    post_path = os.path.join(POSTS_DIR, filename)

    content_html = unescape(content_elem.text or "")
    content_html = replace_relative_links(content_html)

    with open(post_path, "w", encoding="utf-8") as f:
        f.write(f"<h1>{raw_title}</h1>\n{content_html}")

    index_entries.append(f'<li><a href="posts/{filename}">{raw_title}</a></li>')

# === Build index.html ===
index_html = (
    "<html><body><h1>Blog Index</h1><ul>\n"
    + "\n".join(index_entries)
    + "\n</ul></body></html>"
)
with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)

print(f"✅ Finished. Posts saved to '{POSTS_DIR}', index at '{OUTPUT_DIR}/index.html'")
