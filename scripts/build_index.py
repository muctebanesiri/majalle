#!/usr/bin/env python3
import os
from jinja2 import Environment, FileSystemLoader
import glob

def build_index(html_dir, output_path, template_dir):
    html_files = glob.glob(os.path.join(html_dir, '*.html'))
    entries = []
    for f in html_files:
        if os.path.basename(f) == 'index.html':
            continue
        title = os.path.basename(f).replace('.html', '').replace('-', ' ')
        entries.append({'title': title, 'file': os.path.basename(f)})
    entries.sort(key=lambda x: x['title'])
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('index_template.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template.render(entries=entries))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--html-dir', default='src/html')
    parser.add_argument('--output', default='src/html/index.html')
    parser.add_argument('--template-dir', default='src/templates')
    args = parser.parse_args()
    build_index(args.html_dir, args.output, args.template_dir)
