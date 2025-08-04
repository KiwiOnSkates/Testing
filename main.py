import os
import re
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser

# === CONFIGURATION ===
FEED_FILE = "feed.atom"
OUTPUT_DIR = "site"
POSTS_DIR = os.path.join(OUTPUT_DIR, "posts")
INDEX_PATH = "index.html"  # index.html in script root (current working dir)
BASE_URL = "https://yourblog.blogspot.com"  # Change to your blog's domain

# === Ensure output directories exist ===
os.makedirs(POSTS_DIR, exist_ok=True)

# === Helper to generate slug from title ===
def make_slug(title):
    slug = re.sub(r"[^\w\-]+", "-", title.lower()).strip("-")
    return slug or "untitled"

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
# The function uses the map of all known slugs to filenames to rewrite links properly
def replace_relative_links(content_html, slug_map):
    # slug_map: dict mapping original href path → slug filename
    # We'll replace href="/some/path.html" with href="slug.html" if it matches

    def repl(match):
        href = match.group(1)  # original href, like /2025/05/something.html
        filename = os.path.basename(href)
        # Look for matching slug in slug_map by filename (basename)
        # If we find a slug mapping, replace by slug.html, else fallback to filename
        replacement = slug_map.get(filename, filename)
        return f'href="{replacement}"'

    return re.sub(r'href="(/[^"]+)"', repl, content_html)

# === Load Atom feed ===
tree = ET.parse(FEED_FILE)
root = tree.getroot()
ns = {'atom': 'http://www.w3.org/2005/Atom'}

index_entries = []
untitled_count = 0
used_slugs = set()
filename_to_slug = {}  # map original filename (basename) to slug.html filename for link replacement

# === First pass: gather entries and generate slugs ===
entries = []
for entry in root.findall("atom:entry", ns):
    title_elem = entry.find("atom:title", ns)
    content_elem = entry.find("atom:content", ns)

    if content_elem is None:
        continue

    if title_elem is not None and title_elem.text:
        raw_title = title_elem.text.strip()
        slug = make_slug(raw_title)
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
    entries.append((raw_title, content_elem.text or "", filename))

    # We want to map original link filenames to slug filenames, so:
    # The original filenames appear as basenames from links, so map them accordingly.
    # We'll do this by assuming original links' basenames == slugs.
    # So the key is slug + ".html"
    # We'll map slug+".html" → slug+".html" (identity)
    filename_to_slug[filename] = filename

# === Second pass: write posts, replacing links ===
for raw_title, content_raw, filename in entries:
    post_path = os.path.join(POSTS_DIR, filename)

    content_html = unescape(content_raw)
    # Replace links inside content to correct local filenames
    content_html = replace_relative_links(content_html, filename_to_slug)

    with open(post_path, "w", encoding="utf-8") as f:
        f.write(f"<h1>{raw_title}</h1>\n{content_html}")

    # Add entry to index (index is outside 'site' so posts links must include 'site/posts/')
    index_entries.append(f'<li><a href="site/posts/{filename}">{raw_title}</a></li>')

# === Write index.html in script root ===
index_html = (
    "<html><body><h1>Blog Index</h1><ul>\n"
    + "\n".join(index_entries)
    + "\n</ul></body></html>"
)
with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(index_html)

print(f"✅ Finished. Posts saved to '{POSTS_DIR}', index at '{INDEX_PATH}'")
