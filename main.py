import xml.etree.ElementTree as ET
import requests, os

REMOTE_FEED_URL = "https://thway.uk/feeds/posts/default"
LOCAL_FILE = "feed.atom"

namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'blogger': 'http://schemas.google.com/blogger/2018'
}

def collect_all_links():
    blog_links = set()
    content_links = set()
    posts_dict = {}
    seen_ids = set()
    count = 0

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
                                content_links.add(href)
                    except ET.ParseError:
                        pass

    try:
        tree = ET.parse(LOCAL_FILE)
        local_entries = tree.getroot().findall('atom:entry', namespaces)
        process_entries(local_entries)
    except FileNotFoundError:
        print(f"Local file '{LOCAL_FILE}' not found.")

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
    replacements = {}
    entry_filenames = [link.split("/")[-1] for link in entry_links]

    for c_link in content_links:
        end = c_link.split("/")[-1]
        if end in entry_filenames:
            replacements[c_link] = end

    print("Valid Links:", len(replacements))
    return replacements

def save_posts_as_html(posts, output_dir="sites", link_fixes={}):
    os.makedirs(output_dir, exist_ok=True)
    index_items = []

    for filename, meta in posts.items():
        fn = filename.split("/")[-1]
        title = fn.replace(".html", "")
        content = meta.get("content", "")
        published = meta.get("published", "")

        # Fix internal content links
        for bad_link, fixed_link in link_fixes.items():
            content = content.replace(bad_link, f"{output_dir}/{fixed_link}")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    <h1>{title}</h1>
    <p><em>Published: {published}</em></p>
    {content}
</body>
</html>
"""

        with open(os.path.join(output_dir, fn), "w", encoding="utf-8") as f:
            f.write(html)

        index_items.append(f'<li><a href="{output_dir}/{fn}">{title}</a></li>')

    # Write index.html at root
    joined_items = '\n'.join(index_items)
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Blog Index</title>
</head>
<body>
    <h1>Blog Index</h1>
    <ul>
        {joined_items}
    </ul>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"Index page written to index.html")
    print(f"Saved {len(posts)} posts to '{output_dir}/'")

# === Example usage ===
if __name__ == "__main__":
    data = collect_all_links()
    print("Total entries processed:", data["count"])
    print("Blog count:", len(data["blog_links"]))
    print("Content count:", len(data["content_links"]))

    link_fixes = correct_links(data["content_links"], data["blog_links"])
    save_posts_as_html(data["posts"], "sites", link_fixes)
