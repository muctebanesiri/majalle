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
# Qavanin mode: convert **فصل...** to ## فصل... etc.
def convert_bold_headings(text):
    """Convert **فصل ...**, **اصل ...**, etc. to proper markdown headings."""
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        # Match **فصل ...** or **باب ...** -> level 2 heading
        match = re.match(r'^\*\*(فصل|باب)\s+(.*?)\*\*$', line)
        if match:
            new_lines.append(f"## {match.group(1)} {match.group(2)}")
            continue
        # Match **مبحث ...** -> level 3 heading
        match = re.match(r'^\*\*(مبحث)\s+(.*?)\*\*$', line)
        if match:
            new_lines.append(f"### {match.group(1)} {match.group(2)}")
            continue
        # Match **ماده ...** -> level 3 heading
        match = re.match(r'^\*\*(ماده)\s+(.*?)\*\*$', line)
        if match:
            new_lines.append(f"### {match.group(1)} {match.group(2)}")
            continue
        # Match **اصل ...** -> level 3 heading
        match = re.match(r'^\*\*(اصل)\s+(.*?)\*\*$', line)
        if match:
            new_lines.append(f"### {match.group(1)} {match.group(2)}")
            continue
        # Match **تبصره ...** -> level 4 heading
        match = re.match(r'^\*\*(تبصره)\s+(.*?)\*\*$', line)
        if match:
            new_lines.append(f"#### {match.group(1)} {match.group(2)}")
            continue
        # Match **مقدمه** -> level 2 heading
        if line.strip() == '**مقدمه**':
            new_lines.append("## مقدمه")
            continue
        # Otherwise keep the line as is
        new_lines.append(line)
    return '\n'.join(new_lines)

# ------------------------------------------------------------
# CSV mode: heading patterns for raw text with inline merging
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
    """Handle raw messy text from CSV (with inline headings)."""
    lines = body.splitlines()
    out_lines = []
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
            out_lines.append(f'{heading_md} {full}')
            i = j
        else:
            out_lines.append(fix_date(line))
            i += 1
    return '\n'.join(out_lines)

# ------------------------------------------------------------
def convert_md_to_html(md_path, html_path, template_dir):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Split frontmatter and body
    frontmatter = {}
    body = text
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', body, re.DOTALL)
    if fm_match:
        frontmatter = yaml.safe_load(fm_match.group(1))
        body = body[fm_match.end():]

    # Decide which processing mode to use
    if '**فصل' in body or '**اصل' in body:
        # Already clean markdown from qavanin.ir extractor
        formatted_body = convert_bold_headings(body)
        formatted_body = fix_date(formatted_body)
    else:
        # Raw CSV‑style text
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--md', required=True)
    parser.add_argument('--html', required=True)
    parser.add_argument('--template-dir', default='src/templates')
    args = parser.parse_args()
    convert_md_to_html(args.md, args.html, args.template_dir)
