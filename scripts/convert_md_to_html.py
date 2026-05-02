#!/usr/bin/env python3
import os
import re
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader
import argparse

# ------------------------------------------------------------
# Date conversion: 14ˏ08ˏ1370 -> ۱۳۷۰/۰۸/۱۴
def fix_date(text):
    def repl(m):
        d, mth, y = m.groups()
        return f"{y.translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))}/{mth.translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))}/{d.translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))}"
    return re.sub(r'(\d+)[ˏ\-/](\d+)[ˏ\-/](\d+)', repl, text)

# ------------------------------------------------------------
# Clean and convert bold headings from qavanin.ir style
def convert_qavanin_markdown(body):
    lines = body.splitlines()
    out = []
    for line in lines:
        line = line.rstrip()
        # Remove lines that are just **** (horizontal rule)
        if re.match(r'^\*\*\*\*$', line):
            continue
        # Convert **فصل ...** to ## فصل ...
        m = re.match(r'^\*\*(فصل)\s+(.*?)\*\*$', line)
        if m:
            out.append(f"## {m.group(1)} {m.group(2)}")
            continue
        # Convert **باب ...** to ## باب ...
        m = re.match(r'^\*\*(باب)\s+(.*?)\*\*$', line)
        if m:
            out.append(f"## {m.group(1)} {m.group(2)}")
            continue
        # Convert **مبحث ...** to ### مبحث ...
        m = re.match(r'^\*\*(مبحث)\s+(.*?)\*\*$', line)
        if m:
            out.append(f"### {m.group(1)} {m.group(2)}")
            continue
        # Convert **ماده ...** to ### ماده ...
        m = re.match(r'^\*\*(ماده)\s+(.*?)\*\*$', line)
        if m:
            out.append(f"### {m.group(1)} {m.group(2)}")
            continue
        # Convert **اصل ...** to ### اصل ...
        m = re.match(r'^\*\*(اصل)\s+(.*?)\*\*$', line)
        if m:
            out.append(f"### {m.group(1)} {m.group(2)}")
            continue
        # Convert **تبصره ...** to #### تبصره ...
        m = re.match(r'^\*\*(تبصره)\s+(.*?)\*\*$', line)
        if m:
            out.append(f"#### {m.group(1)} {m.group(2)}")
            continue
        # Convert **مقدمه** to ## مقدمه
        if line.strip() == '**مقدمه**':
            out.append("## مقدمه")
            continue
        # Keep other lines as they are
        out.append(line)
    return '\n'.join(out)

# ------------------------------------------------------------
# Fallback: CSV mode (raw text with inline headings)
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

def process_csv_mode(body):
    lines = body.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        heading_md = None
        heading_text = None
        for pat, md in HEADINGS:
            if re.match(pat, line):
                heading_md = md
                heading_text = line.strip()
                break
        if heading_md:
            content = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j].rstrip()
                if not nxt:
                    j += 1
                    continue
                is_next_heading = any(re.match(p, nxt) for p, _ in HEADINGS)
                if is_next_heading:
                    break
                content.append(nxt)
                j += 1
            full = heading_text
            if content:
                full += ' - ' + ' '.join(content)
            full = fix_date(full)
            out.append(f'{heading_md} {full}')
            i = j
        else:
            out.append(fix_date(line))
            i += 1
    return '\n'.join(out)

# ------------------------------------------------------------
def convert_md_to_html(md_path, html_path, template_dir):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Extract YAML frontmatter
    frontmatter = {}
    body = text
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', body, re.DOTALL)
    if fm_match:
        frontmatter = yaml.safe_load(fm_match.group(1))
        body = body[fm_match.end():]

    # Auto-detect mode
    if '**فصل' in body or '**اصل' in body:
        print("[INFO] Qavanin mode detected – converting bold headings.", file=sys.stderr)
        formatted_body = convert_qavanin_markdown(body)
        formatted_body = fix_date(formatted_body)
    else:
        print("[INFO] CSV mode detected – processing raw text.", file=sys.stderr)
        formatted_body = process_csv_mode(body)

    # Metadata
    title = frontmatter.get('title', os.path.basename(md_path).replace('.md', '').replace('-', ' '))
    date = frontmatter.get('date', 'نامشخص')
    organ = frontmatter.get('organ', 'نامشخص')

    # Convert to HTML
    html_body = markdown.markdown(formatted_body, extensions=['extra', 'codehilite'])

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('law_template.html')
    output = template.render(title=title, date=date, organ=organ, content=html_body)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(output)

if __name__ == "__main__":
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument('--md', required=True)
    parser.add_argument('--html', required=True)
    parser.add_argument('--template-dir', default='src/templates')
    args = parser.parse_args()
    convert_md_to_html(args.md, args.html, args.template_dir)
