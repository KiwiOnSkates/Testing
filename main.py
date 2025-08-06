import xml.etree.ElementTree as ET
import requests, os, re

REMOTE_FEED_URL = "https://thway.uk/feeds/posts/default"
LOCAL_FILE = "feed.atom"

namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'blogger': 'http://schemas.google.com/blogger/2018'
}

def collect_all_links():
    blog_links = set()
    content_links = set()
    posts_dict = {}      # Store posts keyed by filename with metadata
    seen_ids = set()     # To avoid duplicate entries by id
    count = 0            # Total entries processed

    def process_entries(entries):
        nonlocal count
        for entry in entries:
            id_elem = entry.find('atom:id', namespaces)
            if id_elem is None:
                continue
            entry_id = id_elem.text
            if entry_id in seen_ids:
                continue
            seen_ids.add(entry_id)
            count += 1

            filename_elem = entry.find('blogger:filename', namespaces)
            content_elem = entry.find('atom:content', namespaces)
            title_elem = entry.find('atom:title', namespaces)
            published_elem = entry.find('atom:published', namespaces)

            if filename_elem is not None and content_elem is not None:
                fname = filename_elem.text
                blog_links.add(fname)

                # Save metadata in posts_dict keyed by filename
                posts_dict[fname] = {
                    "title": title_elem.text if title_elem is not None else None,
                    "content": content_elem.text,
                    "published": published_elem.text if published_elem is not None else None,
                }

                content_html = content_elem.text
                if content_html:
                    try:
                        content_root = ET.fromstring(f"<root>{content_html}</root>")
                        for a_tag in content_root.findall('.//a'):
                            href = a_tag.get('href')
                            if href and not href.startswith("https://") and "/search" not in href:
                                # Normalize href trailing slash and extension
##                                if href.endswith('/'):
##                                    href = href[:-1] + ".html"
##                                elif not href.endswith('.html'):
           
                                content_links.add(href)
                    except ET.ParseError:
                        pass

    # --- Process local entries ---
    try:
        tree = ET.parse(LOCAL_FILE)
        local_entries = tree.getroot().findall('atom:entry', namespaces)
        process_entries(local_entries)
    except FileNotFoundError:
        print(f"Local file '{LOCAL_FILE}' not found.")

    # --- Process remote entries paginated ---
    start_index = 1
    max_results = 100

    while True:
        url = f"{REMOTE_FEED_URL}?start-index={start_index}&max-results={max_results}"
        response = requests.get(url)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        entries = root.findall('atom:entry', namespaces)
        if not entries:
            break

        process_entries(entries)
        start_index += max_results

    return {
        "blog_links": blog_links,
        "content_links": content_links,
        "posts": posts_dict,
        "count": count
    }

def correct_links(content_links, entry_links):
    link_fixes = {}
    valid_links = 0


    new_entry = []
    replacements = {}
    for c_link in entry_links:
        new_entry.append(c_link.split("/")[-1])

    for c_link in content_links:
        if c_link.split("/")[-1] in new_entry:
            replacements[c_link] = c_link.split("/")[-1]
        else:
            pass

    print("Valid Links:", valid_links)
    return replacements

def save_posts_as_html(posts, output_dir="sites", link_fixes={}):
    os.makedirs(output_dir, exist_ok=True)
 
    index_items = []
    for filename, meta in posts.items():
        fn = filename.split("/")[-1]

        content = posts[filename]["content"]
        for x in link_fixes:
            if x in content:
                content = content.replace(x, "sites/"+link_fixes[x])
            
        title = fn.replace(".html", "")
        published = meta.get("published", "")

        # Sanitize filename (strip unsafe characters)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>"
    <h1>{title}</h1>
    <p><em>Published: {published}</em></p>
    {content}
</body>
</html>
"""
        index_items.append(f'<li><a href="sites/{fn}">{title}</a></li>')
        with open("sites/"+fn, "w", encoding="utf-8") as f:
            f.write(html)
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Blog Index</title>
</head>
<body>
    <h1>Blog Index</h1>
    <ul>
        {'\n'.join(index_items)}
    </ul>
</body>
</html>
"""

    with open(os.path.join("", "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"Index page written to {output_dir}/index.html")


# === Example usage ===
if __name__ == "__main__":
    data = collect_all_links()
    print("Total entries processed:", data["count"])
    print("Blog count:", len(data["blog_links"]))
    print("Content count:", len(data["content_links"]))

    # Check corrected links
    link_fixes = correct_links(data["content_links"], data["blog_links"])



    save_posts_as_html(data["posts"], "sites", link_fixes)


