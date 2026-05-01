#!/usr/bin/env python3
import os
import sys
import re
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader
import argparse

def extract_frontmatter(content):
    # Check for YAML frontmatter (--- ... ---)
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    if match:
        frontmatter_text = match.group(1)
        frontmatter = yaml.safe_load(frontmatter_text)
        body = content[match.end():]
        return frontmatter, body
    return {}, content

def convert_md_to_html(md_path, html_path, template_dir):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    frontmatter, body = extract_frontmatter(md_content)
    
    # Extract title, date, organ from frontmatter or fallback
    title = frontmatter.get('title', os.path.basename(md_path).replace('.md', '').replace('-', ' '))
    date = frontmatter.get('date', 'نامشخص')
    organ = frontmatter.get('organ', 'نامشخص')
    
    # Convert markdown body to HTML
    html_body = markdown.markdown(body, extensions=['extra', 'codehilite'])
    
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('law_template.html')
    output = template.render(title=title, date=date, organ=organ, content=html_body)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--md', required=True)
    parser.add_argument('--html', required=True)
    parser.add_argument('--template-dir', default='src/templates')
    args = parser.parse_args()
    convert_md_to_html(args.md, args.html, args.template_dir)
