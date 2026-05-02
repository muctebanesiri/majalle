#!/usr/bin/env python3
import os
import re
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader
import argparse

# ----------------------------------------------------------------------
# Date conversion: "14ˏ08ˏ1370" -> "۱۳۷۰/۰۸/۱۴"
# ----------------------------------------------------------------------

def convert_date(date_str):
    """
    Convert a date string like "14ˏ08ˏ1370" (day-month-year) to "۱۳۷۰/۰۸/۱۴"
    Handles both Latin and Persian digits, and normalizes separators.
    """
    # Replace the weird separator (ˏ) with a standard slash
    normalized = re.sub(r'[ˏ\-/]', '/', date_str)
    parts = normalized.split('/')
    if len(parts) != 3:
        return date_str  # not a date, return unchanged
    day, month, year = parts
    # Convert each part to Persian digits
    def to_persian(s):
        persian_map = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
        return s.translate(persian_map)
    # Swap day and year to get YYYY/MM/DD
    return f"{to_persian(year)}/{to_persian(month)}/{to_persian(day)}"

def format_date_in_text(text):
    """
    Find patterns like (اصلاحی 14ˏ08ˏ1370) or (14ˏ08ˏ1370) and convert the date.
    """
    # Pattern: optional Persian word "اصلاحی" followed by date pattern
    # We look for a sequence: optional spaces, digits, separator, digits, separator, digits
    date_pattern = r'(\d+)[ˏ\-/](\d+)[ˏ\-/](\d+)'
    def replacer(match):
        day, month, year = match.group(1), match.group(2), match.group(3)
        persian_year = year.translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))
        persian_month = month.translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))
        persian_day = day.translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))
        return f"{persian_year}/{persian_month}/{persian_day}"
    return re.sub(date_pattern, replacer, text)

# ----------------------------------------------------------------------
# Law formatting engine (heading detection + merging)
# ----------------------------------------------------------------------

HEADING_PATTERNS = [
    (r'^باب\s+[۰-۹0-9]+', '##'),
    (r'^فصل\s+[۰-۹0-9]+', '##'),
    (r'^مبحث\s+[۰-۹0-9]+', '###'),
    (r'^گفتار\s+[۰-۹0-9]+', '###'),
    (r'^ماده\s+[۰-۹0-9]+', '###'),
    (r'^تبصره\s+[۰-۹0-9]+', '####'),
    (r'^جزء\s+[۰-۹0-9]+', '####'),
    (r'^بند\s+[۰-۹0-9]+', '####'),
    (r'^مقدمه', '##'),   # changed to level 2 heading
]

def is_heading(line):
    for pattern, prefix in HEADING_PATTERNS:
        match = re.match(pattern, line.strip())
        if match:
            # The heading text (everything from start to end of line? Actually we capture the matched part)
            heading_text = match.group(0).strip()
            return True, prefix, heading_text
    return False, None, None

def merge_heading_with_content(lines):
    """
    Process a list of lines. When a heading line is found, collect subsequent lines
    until next heading and merge them into the heading line with a dash.
    Returns a new list of lines where each heading is followed immediately by its content.
    """
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        is_h, prefix, heading_text = is_heading(line)
        if is_h:
            # Collect content lines until next heading
            content_parts = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j].rstrip()
                if not next_line.strip():
                    j += 1
                    continue
                if is_heading(next_line)[0]:
                    break
                content_parts.append(next_line)
                j += 1
            # Merge heading and content
            full_text = heading_text
            if content_parts:
                content = ' '.join(content_parts)
                # Normalize dash: if heading already ends with dash or colon, keep it; else add " - "
                if not re.search(r'[-–:]$', full_text):
                    full_text += ' - ' + content
                else:
                    full_text += ' ' + content
            # Apply date conversion to the entire merged line (including heading)
            full_text = format_date_in_text(full_text)
            result.append(f'{prefix} {full_text}')
            i = j
        else:
            # Non‑heading line: apply date conversion to any dates inside
            result.append(format_date_in_text(line))
            i += 1
    return result

def format_law_text(content):
    lines = content.splitlines()
    merged = merge_heading_with_content(lines)
    return '\n'.join(merged)

# ----------------------------------------------------------------------
# Standard frontmatter and conversion
# ----------------------------------------------------------------------

def extract_frontmatter(content):
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
        raw_content = f.read()
    
    frontmatter, body = extract_frontmatter(raw_content)
    formatted_body = format_law_text(body)
    
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
