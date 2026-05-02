#!/usr/bin/env python3
import os
import sys
import re
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader
import argparse

# ----------------------------------------------------------------------
# Law formatting functions (enhanced)
# ----------------------------------------------------------------------

HEADING_PATTERNS = [
    (r'^(باب\s+[۰-۹0-9]+)', '##'),
    (r'^(فصل\s+[۰-۹0-9]+)', '##'),
    (r'^(مبحث\s+[۰-۹0-9]+)', '###'),
    (r'^(گفتار\s+[۰-۹0-9]+)', '###'),
    (r'^(ماده\s+[۰-۹0-9]+)', '###'),
    (r'^(تبصره\s+[۰-۹0-9]+)', '####'),
    (r'^(جزء\s+[۰-۹0-9]+)', '####'),
    (r'^(بند\s+[۰-۹0-9]+)', '####'),
    (r'^(ماده\s+\d+)', '###'),
    (r'^(تبصره\s+\d+)', '####'),
]

LIST_ITEM_MARKER = re.compile(r'^\s*[۰-۹0-9]+[\)\.]\s+')

def split_heading_and_rest(line):
    for pattern, _ in HEADING_PATTERNS:
        match = re.match(pattern, line)
        if match:
            heading_end = match.end()
            heading = line[:heading_end].strip()
            rest = line[heading_end:].strip()
            return heading, rest
    return None, line

def split_inline_list(line):
    if '\n' in line:
        return [line]
    parts = re.split(r'(?<=[\)\.])\s+(?=[۰-۹0-9]+[\)\.])', line)
    result = []
    for part in parts:
        part = part.strip()
        if part:
            part = re.sub(r'([۰-۹0-9]+[\)\.])([^\s])', r'\1 \2', part)
            result.append(part)
    return result if len(result) > 1 else [line]

def merge_heading_with_next(lines, idx):
    """
    If the current line is a heading (e.g., "### ماده ۹۵") and the next line exists
    and is not another heading, merge them with a dash.
    Returns (new_lines, next_index_to_skip)
    """
    current = lines[idx]
    if idx + 1 >= len(lines):
        return lines, idx
    next_line = lines[idx + 1]
    # If current starts with markdown heading and next is not a heading (starts with '#')
    if current.startswith('#') and not next_line.startswith('#'):
        # Remove the heading marker and combine
        heading_marker = re.match(r'^(#+)\s+', current).group(1)
        heading_text = re.sub(r'^#+\s+', '', current).strip()
        # Merge with next line: format as "heading - next_text"
        merged = f"{heading_marker} {heading_text} - {next_line}"
        new_lines = lines[:idx] + [merged] + lines[idx+2:]
        return new_lines, idx  # stay at same index
    return lines, idx

def process_text_block(block):
    lines = block.splitlines()
    output = []
    for line in lines:
        line = line.strip()
        if not line:
            output.append('')
            continue
        heading, rest = split_heading_and_rest(line)
        if heading is not None:
            for pattern, prefix in HEADING_PATTERNS:
                if re.match(pattern, heading):
                    output.append(f'{prefix} {heading}')
                    break
            if rest:
                items = split_inline_list(rest)
                output.extend(items)
        else:
            items = split_inline_list(line)
            output.extend(items)
    # Merge headings with following text (creates "### ماده X - متن")
    i = 0
    while i < len(output):
        output, i = merge_heading_with_next(output, i)
        i += 1
    return output

def format_law_text(content: str) -> str:
    blocks = re.split(r'\n\s*\n', content)
    all_lines = []
    for block in blocks:
        if not block.strip():
            continue
        formatted = process_text_block(block)
        all_lines.extend(formatted)
        all_lines.append('')
    # Remove excessive blank lines
    result = []
    last_empty = False
    for line in all_lines:
        if line == '':
            if not last_empty:
                result.append('')
                last_empty = True
        else:
            result.append(line)
            last_empty = False
    return '\n'.join(result).strip()

# ----------------------------------------------------------------------
# Original conversion functions
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
