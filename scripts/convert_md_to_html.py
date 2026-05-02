#!/usr/bin/env python3
import os
import re
import sys
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader
import argparse

# ------------------------------------------------------------
# 1. Date Normalization
# ------------------------------------------------------------
def fix_date(text):
    def repl(m):
        d, mth, y = m.groups()
        # swap day and year
        return f"{y.translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))}/{mth.translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))}/{d.translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))}"
    return re.sub(r'(\d+)[ˏ\-/](\d+)[ˏ\-/](\d+)', repl, text)

# ------------------------------------------------------------
# 2. Extract Date and Organ from qavanin.ir lines
# ------------------------------------------------------------
def extract_date_organ_from_line(line):
    content = re.sub(r'^\*\*Date:\*\*\s*', '', line)
    match = re.match(r'(مصوب\s+)?(\d+[ˏ\-/]\d+[ˏ\-/]\d+)\s+(.*)', content)
    if match:
        date_str = match.group(2)
        organ = match.group(3).strip()
        return date_str, organ
    return None, None

# ------------------------------------------------------------
# 3. Extract Title from the First Heading
# ------------------------------------------------------------
def extract_title_from_body(body):
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('# '):
            title = line[2:].strip()
            new_body = '\n'.join(lines[:i] + lines[i+1:])
            return title, new_body
    return None, body

# ------------------------------------------------------------
# 4. Core Cleaning Logic for qavanin.ir Markdown
# ------------------------------------------------------------
def clean_qavanin_markdown(body):
    lines = body.splitlines()
    out = []
    date_from_line = None
    organ_from_line = None
    for line in lines:
        line = line.rstrip()
        if not line:
            out.append('')
            continue
        if line.strip() == '****':
            continue
        if line.startswith('**Date:**'):
            d, o = extract_date_organ_from_line(line)
            if d:
                date_from_line = d
                organ_from_line = o
            continue  # remove this line from output
        # Convert **كتاب ...** -> ## كتاب ...
        m = re.match(r'^\*\*(كتاب)\s+(.*?)\*\*$', line)
        if m:
            out.append(f"## {m.group(1)} {m.group(2)}")
            continue
        # Convert **باب ...** -> ## باب ...
        m = re.match(r'^\*\*(باب)\s+(.*?)\*\*$', line)
        if m:
            out.append(f"## {m.group(1)} {m.group(2)}")
            continue
        # Convert **فصل ...** -> ## فصل ...
        m = re.match(r'^\*\*(فصل)\s+(.*?)\*\*$', line)
        if m:
            out.append(f"## {m.group(1)} {m.group(2)}")
            continue
        # Convert **مبحث ...** -> ### مبحث ...
        m = re.match(r'^\*\*(مبحث)\s+(.*?)\*\*$', line)
        if m:
            out.append(f"### {m.group(1)} {m.group(2)}")
            continue
        # Convert plain 'مقدمه' to ## مقدمه
        if line.strip() == 'مقدمه':
            out.append('## مقدمه')
            continue
        # Keep existing markdown headings (### ماده ...)
        if line.startswith('#'):
            out.append(line)
            continue
        out.append(line)
    return '\n'.join(out), date_from_line, organ_from_line

# ------------------------------------------------------------
# 5. Main Conversion Function
# ------------------------------------------------------------
def convert_md_to_html(md_path, html_path, template_dir):
    print(f"Processing: {md_path}", file=sys.stderr)
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Extract YAML frontmatter
    frontmatter = {}
    body = text
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', body, re.DOTALL)
    if fm_match:
        try:
            frontmatter = yaml.safe_load(fm_match.group(1))
            body = body[fm_match.end():]
        except yaml.YAMLError as e:
            print(f"Warning: YAML frontmatter could not be parsed: {e}", file=sys.stderr)

    # Clean body and extract date/organ from **Date:** line
    cleaned_body, date_from_line, organ_from_line = clean_qavanin_markdown(body)
    cleaned_body = fix_date(cleaned_body)

    # Extract title from cleaned body (first level-1 heading) and remove it
    extracted_title, cleaned_body = extract_title_from_body(cleaned_body)

    # Priority: frontmatter > extracted > filename
    title = frontmatter.get('title') or extracted_title or os.path.basename(md_path).replace('.md', '').replace('-', ' ')
    date = frontmatter.get('date') or date_from_line or 'نامشخص'
    organ = frontmatter.get('organ') or organ_from_line or 'نامشخص'

    # Convert date to Persian digits for display
    if date != 'نامشخص' and date:
        date = fix_date(date)

    # Convert markdown to HTML
    html_body = markdown.markdown(cleaned_body, extensions=['extra', 'codehilite'])

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('law_template.html')
    output = template.render(title=title, date=date, organ=organ, content=html_body)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"Successfully created: {html_path}", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--md', required=True)
    parser.add_argument('--html', required=True)
    parser.add_argument('--template-dir', default='src/templates')
    args = parser.parse_args()
    convert_md_to_html(args.md, args.html, args.template_dir)
