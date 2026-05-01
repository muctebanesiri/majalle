#!/usr/bin/env python3
import os
import sys
import markdown
from jinja2 import Environment, FileSystemLoader
import argparse

def convert_md_to_html(md_path, html_path, template_dir):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    html_body = markdown.markdown(md_content, extensions=['extra', 'codehilite'])
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('law_template.html')
    title = os.path.basename(md_path).replace('.md', '').replace('-', ' ')
    output = template.render(title=title, content=html_body)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--md', required=True)
    parser.add_argument('--html', required=True)
    parser.add_argument('--template-dir', default='src/templates')
    args = parser.parse_args()
    convert_md_to_html(args.md, args.html, args.template_dir)
