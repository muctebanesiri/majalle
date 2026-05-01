#!/usr/bin/env python3
import os
import glob
import json
import re
from jinja2 import Environment, FileSystemLoader

def clean_html_text(html_path):
    """Extract plain text from a generated HTML file."""
    with open(html_path, 'r', encoding='utf-8') as f:
        data = f.read()
    # Remove script and style blocks
    data = re.sub(r'<script.*?</script>', '', data, flags=re.DOTALL)
    data = re.sub(r'<style.*?</style>', '', data, flags=re.DOTALL)
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', ' ', data)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Keep Persian letters, numbers, and common punctuation
    return text

def build_index(html_dir, output_index_path, template_dir):
    # Collect all law HTML files (exclude index.html)
    all_files = glob.glob(os.path.join(html_dir, '*.html'))
    law_files = [f for f in all_files if not f.endswith('index.html')]

    entries = []
    for path in law_files:
        title = os.path.basename(path).replace('.html', '').replace('-', ' ')
        entries.append({'title': title, 'file': os.path.basename(path)})
    entries.sort(key=lambda x: x['title'])

    # Render index.html from template
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('index_template.html')
    with open(output_index_path, 'w', encoding='utf-8') as f:
        f.write(template.render(entries=entries))

    # Build search index JSON
    search_index = []
    for path in law_files:
        title = os.path.basename(path).replace('.html', '').replace('-', ' ')
        url = os.path.basename(path)
        content = clean_html_text(path)
        search_index.append({
            'title': title,
            'url': url,
            'content': content
        })
    search_json_path = os.path.join(html_dir, 'search_index.json')
    with open(search_json_path, 'w', encoding='utf-8') as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--html-dir', default='src/html')
    parser.add_argument('--output', default='src/html/index.html')
    parser.add_argument('--template-dir', default='src/templates')
    args = parser.parse_args()
    build_index(args.html_dir, args.output, args.template_dir)
