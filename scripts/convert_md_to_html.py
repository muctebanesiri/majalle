#!/usr/bin/env python3
import os
import sys
import re
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader
import argparse

# ----------------------------------------------------------------------
# Law formatting functions (embedded)
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

LIST_ITEM_SPLIT = re.compile(r'(?<=[)\.])\s+(?=[۰-۹0-9]+[\)\.])')

def is_heading(line: str) -> tuple[bool, str]:
    line_stripped = line.strip()
    for pattern, prefix in HEADING_PATTERNS:
        if re.match(pattern, line_stripped):
            return True, prefix
    return False, None

def split_list_line(line: str) -> list[str]:
    line = line.strip()
    if not line:
        return []
    if '\n' in line:
        return [line]
    parts = LIST_ITEM_SPLIT.split(line)
    result = []
    for part in parts:
        if re.match(r'^\s*[۰-۹0-9]+[\)\.]', part):
            result.append(part)
        elif result:
            result[-1] += ' ' + part
        else:
            result.append(part)
    cleaned = []
    for item in result:
        item = re.sub(r'([۰-۹0-9]+[\)\.])([^\s])', r'\1 \2', item)
        cleaned.append(item.strip())
    return cleaned

def clean_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r'([۰-۹0-9]+[\)\.])([^\s])', r'\1 \2', line)
    line = re.sub(r'([\-\*•])([^\s])', r'\1 \2', line)
    return line

def format_law_text(content: str) -> str:
    lines = content.splitlines()
    output_lines = []
    for line in lines:
        line = line.rstrip()
        if not line.strip():
            output_lines.append('')
            continue
        split_items = split_list_line(line)
        for item in split_items:
            item = clean_line(item)
            if not item:
                continue
            is_h, prefix = is_heading(item)
            if is_h:
                output_lines.append(f'{prefix} {item}')
            else:
                output_lines.append(item)
    # Collapse multiple blank lines to at most two
    final_lines = []
    blank_count = 0
    for line in output_lines:
        if line.strip() == '':
            blank_count += 1
            if blank_count <= 2:
                final_lines.append('')
        else:
            blank_count = 0
            final_lines.append(line)
    return '\n'.join(final_lines)

# ----------------------------------------------------------------------
# Original conversion functions (modified to format before processing)
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
    
    # 1. Extract YAML frontmatter (if any)
    frontmatter, body = extract_frontmatter(raw_content)
    
    # 2. Format the body (apply law formatting)
    formatted_body = format_law_text(body)
    
    # 3. Reassemble with frontmatter (if present)
    if frontmatter:
        # Re-create YAML frontmatter block
        yaml_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
        formatted_content = f"---\n{yaml_str}---\n{formatted_body}"
    else:
        formatted_content = formatted_body
    
    # Extract metadata for the HTML template
    title = frontmatter.get('title', os.path.basename(md_path).replace('.md', '').replace('-', ' '))
    date = frontmatter.get('date', 'نامشخص')
    organ = frontmatter.get('organ', 'نامشخص')
    
    # 4. Convert the **formatted** markdown body to HTML
    #    (We use the formatted_body, not the reassembled content, because the frontmatter is for metadata only)
    html_body = markdown.markdown(formatted_body, extensions=['extra', 'codehilite'])
    
    # 5. Render with template
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
