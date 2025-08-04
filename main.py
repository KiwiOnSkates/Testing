import os
import re
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser

FEED_FILE = "feed.atom"
OUTPUT_DIR = "site"
POSTS_DIR = os.path.join(OUTPUT_DIR, "posts")

os.makedirs(POSTS_DIR, exist_ok=True)

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for key, value in attrs:
                if key == "href" and value.startswith("/"):
                    self.links.append(value)

def make_slug(title):
    slug = re.sub(r"[^\w\-]+", "-", title.lower()).strip("-")
    return slug or "untitled"

def replace_relative_links(content_html, link_map):
    def repl(m):
        href = m.group(1)  # e.g. "/2025/05/original-post.html"
        fname = os.path.basename(href)
        if fname in link_map:
            # Replace with local filename only, because all posts in same folder
            return f'href="{link_map[fname]}"'
        else:
            # fallback: remove leading slash (relative to posts folder)
            return f'href="{href.lstrip("/")}"'
    return re.sub(r'href="(/[^"]+)"', repl, content_html)

tree = ET.parse(FEED_FILE)
root = tree.getroot()
ns = {'atom': 'http://www.w3.org/2005/Atom'}

link_map = {}  # key: original Blogger filename, value: local slug filename
index_entries = []
untitled_count = 0
used_slugs = set()

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

    # Ensure unique slug
    orig_slug = slug
    i = 1
    while slug in used_slugs:
        slug = f"{orig_slug}-{i}"
        i += 1
    used_slugs.add(slug)

    filename = f"{slug}.html"

    content_html = unescape(content_elem.text or "")
    parser = LinkExtractor()
    parser.feed(content_html)

    # Map all found href filenames to their slugs as placeholders
    for link in parser.links:
        fname = os.path.basename(link)
        if fname not in link_map:
            # We don't yet know the slug for these links, set None for now
            link_map[fname] = None

    # Also add current post's main slug filename to link_map
    # For this you need to know the original Blogger filename (from URL or id)
    # Let's get it from the entry id element, which usually ends with post-<number>
    id_elem = entry.find("atom:id", ns)
    if id_elem is not None and id_elem.text:
        # Extract possible filename from id (if present)
        # Sometimes id is like: tag:blogger.com,1999:blog-...post-12617885354179380
        # We don't get filename from here directly, so as fallback, map slug.html to itself
        link_map[f"{slug}.html"] = filename
    else:
        link_map[f"{slug}.html"] = filename

# At this point, some entries in link_map have None values (unknown slug)
# We want to fill those None values if possible, but if not, just leave them as is.

# Now rewrite the links in content_html to replace Blogger URLs with local filenames:
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

    filename = f"{slug}.html"
    content_html = unescape(content_elem.text or "")
    content_html = replace_relative_links(content_html, link_map)

    # Write the post file inside site/posts
    with open(os.path.join(POSTS_DIR, filename), "w", encoding="utf-8") as f:
        f.write(f"<h1>{raw_title}</h1>\n{content_html}")

    # Add entry to index (index is in script root)
    index_entries.append(f'<li><a href="site/posts/{filename}">{raw_title}</a></li>')

# Write index.html in script root
index_html = (
    "<html><body><h1>Blog Index</h1><ul>\n"
    + "\n".join(index_entries)
    + "\n</ul></body></html>"
)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

print("✅ Done. Posts saved in 'site/posts/', index.html in script root.")
