import os
import re
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser

# === CONFIGURATION ===
FEED_FILE = "feed.atom"
OUTPUT_DIR = "site"
PAGES_DIR = os.path.join(OUTPUT_DIR, "pages")
POSTS_DIR = os.path.join(OUTPUT_DIR, "posts")
BASE_URL = "https://yourblog.blogspot.com"  # Change this to your blog's domain

# === Ensure output directories exist ===
os.makedirs(PAGES_DIR, exist_ok=True)
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
        continue  # skip if no content

    # Safely get title or fallback to auto-numbered
    if title_elem is not None and title_elem.text:
        raw_title = title_elem.text.strip()
        slug = re.sub(r"[^\w\-]+", "-", raw_title.lower()).strip("-") or "untitled"
    else:
        untitled_count += 1
        raw_title = f"Untitled {untitled_count}"
        slug = f"untitled-{untitled_count}"

    # Ensure unique slug (in case of repeated titles)
    orig_slug = slug
    i = 1
    while slug in used_slugs:
        slug = f"{orig_slug}-{i}"
        i += 1
    used_slugs.add(slug)

    filename = f"{slug}.html"
    post_path = os.path.join(POSTS_DIR, filename)

    # Extract and decode HTML content
    content_html = unescape(content_elem.text or "")

    # Try to extract a relative link
    parser = LinkExtractor()
    parser.feed(content_html)
    relative_link = parser.links[0] if parser.links else None
    full_url = BASE_URL + relative_link if relative_link else "#"

    # Write the post HTML file
    with open(post_path, "w", encoding="utf-8") as f:
        f.write(f"<h1>{raw_title}</h1>\n{content_html}")

    # Add to index
    index_entries.append(f'<li><a href="site/posts/{filename}">{raw_title}</a></li>')

# === Build index.html in repo root (overwrites if exists) ===
index_html = (
    "<html><body><h1>Blog Index</h1><ul>\n"
    + "\n".join(index_entries)
    + "\n</ul></body></html>"
)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

print(f"✅ Finished. Posts saved to '{POSTS_DIR}', index at 'index.html'")
