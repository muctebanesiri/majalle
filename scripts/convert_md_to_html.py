#!/usr/bin/env python3
import os
import re
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader
import argparse

# ------------------------------------------------------------
# date conversion: 14ˏ08ˏ1370 -> ۱۳۷۰/۰۸/۱۴
def fix_date(text):
    def repl(m):
        d, mth, y = m.groups()
        # swap day and year
        return f"{y.translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))}/{mth.translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))}/{d.translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))}"
    return re.sub(r'(\d+)[ˏ\-/](\d+)[ˏ\-/](\d+)', repl, text)

# ------------------------------------------------------------
# heading patterns: (regex, markdown level)
HEADINGS = [
    (r'^مقدمه\b',               '##'),
    (r'^باب\s+[۰-۹0-9]+',       '##'),
    (r'^فصل\s+[۰-۹0-9]+',       '##'),
    (r'^مبحث\s+[۰-۹0-9]+',      '###'),
    (r'^ماده\s+[۰-۹0-9]+',      '###'),
    (r'^تبصره\s+[۰-۹0-9]+',     '####'),
    (r'^جزء\s+[۰-۹0-9]+',       '####'),
    (r'^بند\s+[۰-۹0-9]+',       '####'),
]

def convert_md_to_html(md_path, html_path, template_dir):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # separate frontmatter and body
    frontmatter = {}
    body = text
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', body, re.DOTALL)
    if fm_match:
        frontmatter = yaml.safe_load(fm_match.group(1))
        body = body[fm_match.end():]

    # process line by line
    lines = body.splitlines()
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue

        # check if line starts with a heading
        heading_md = None
        heading_text = None
        for pat, md in HEADINGS:
            if re.match(pat, line):
                heading_md = md
                heading_text = line.strip()
                break

        if heading_md:
            # collect next non‑empty lines until next heading
            content = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j].rstrip()
                if not nxt:
                    j += 1
                    continue
                # stop if next line is also a heading
                is_next_heading = any(re.match(p, nxt) for p, _ in HEADINGS)
                if is_next_heading:
                    break
                content.append(nxt)
                j += 1
            full = heading_text
            if content:
                full += ' - ' + ' '.join(content)
            full = fix_date(full)
            out_lines.append(f'{heading_md} {full}')
            i = j
        else:
            # normal line – just fix dates
            out_lines.append(fix_date(line))
            i += 1

    formatted_body = '\n'.join(out_lines)

    # metadata for template
    title = frontmatter.get('title', os.path.basename(md_path).replace('.md', '').replace('-', ' '))
    date = frontmatter.get('date', 'نامشخص')
    organ = frontmatter.get('organ', 'نامشخص')

    html_body = markdown.markdown(formatted_body, extensions=['extra', 'codehilite'])

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
