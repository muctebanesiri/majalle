#!/usr/bin/env python3
import os
import glob
import json
import re
from jinja2 import Environment, FileSystemLoader

def extract_title_from_html(html_path):
    """Extract title from <title> tag, fallback to filename."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    base = os.path.basename(html_path).replace('.html', '').replace('-', ' ')
    return base

def build_index(html_dir, template_dir):
    # Find all law HTML files (exclude index.html)
    all_files = glob.glob(os.path.join(html_dir, '*.html'))
    law_files = [f for f in all_files if not f.endswith('index.html')]

    laws = []
    for f in law_files:
        title = extract_title_from_html(f)
        url = os.path.basename(f)
        laws.append({'title': title, 'url': url})
    laws.sort(key=lambda x: x['title'])

    # Load template and replace placeholder
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('index_template.html')
    html_content = template.render()

    # Convert laws to JavaScript array
    laws_js = json.dumps(laws, ensure_ascii=False, indent=2)
    laws_var = f'var laws = {laws_js};'
    html_content = html_content.replace('LAWS_ARRAY_PLACEHOLDER', laws_var)

    output_path = os.path.join(html_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--html-dir', default='src/html')
    parser.add_argument('--template-dir', default='src/templates')
    args = parser.parse_args()
    build_index(args.html_dir, args.template_dir)
