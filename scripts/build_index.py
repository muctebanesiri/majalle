#!/usr/bin/env python3
import os
import glob
import json
import re
from shutil import copyfile
from jinja2 import Environment, FileSystemLoader

def clean_html_text(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        data = f.read()
    data = re.sub(r'<script.*?</script>', '', data, flags=re.DOTALL)
    data = re.sub(r'<style.*?</style>', '', data, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', data)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_index(html_dir, template_dir):
    # 1. copy or render index.html from template (no variables needed)
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('index_template.html')
    with open(os.path.join(html_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(template.render())   # no variables

    # 2. generate search_index.json
    law_files = glob.glob(os.path.join(html_dir, '*.html'))
    law_files = [f for f in law_files if not f.endswith('index.html')]

    search_index = []
    for path in law_files:
        title = os.path.basename(path).replace('.html', '').replace('-', ' ')
        url = os.path.basename(path)
        content = clean_html_text(path)
        search_index.append({'title': title, 'url': url, 'content': content})

    with open(os.path.join(html_dir, 'search_index.json'), 'w', encoding='utf-8') as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--html-dir', default='src/html')
    parser.add_argument('--template-dir', default='src/templates')
    args = parser.parse_args()
    build_index(args.html_dir, args.template_dir)
