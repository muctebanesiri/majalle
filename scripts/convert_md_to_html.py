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

# Match a list item number followed by a separator (e.g., "۱)" or "۱.")
LIST_ITEM_MARKER = re.compile(r'^\s*[۰-۹0-9]+[\)\.]\s+')

def split_heading_and_rest(line):
    """
    If line starts with a heading pattern, extract heading part (up to and including the number)
    and the rest of the line (everything after the number & optional characters).
    Returns (heading_line, rest_line). If not a heading, returns (None, line).
    """
    for pattern, _ in HEADING_PATTERNS:
        match = re.match(pattern, line)
        if match:
            heading_end = match.end()
            # Find where the heading part ends (usually after the number and any following dash/space)
            # But keep the heading as the matched part.
            heading = line[:heading_end].strip()
            rest = line[heading_end:].strip()
            # If rest is empty, return heading only
            if rest:
                return heading, rest
            else:
                return heading, None
    return None, line

def split_inline_list(line):
    """
    Split a line that contains multiple numbered list items like "۱) text ۲) text"
    into separate lines, each with one list item.
    Returns a list of lines (each with one list item).
    """
    if '\n' in line:
        return [line]
    # Use a regex that splits BEFORE a new number+separator, but keep the number with its text.
    # Pattern: look for a space that is followed by a number+separator, but not preceded by a number+separator? Actually simpler:
    parts = re.split(r'(?<=[\)\.])\s+(?=[۰-۹0-9]+[\)\.])', line)
    # Each part should start with a list marker. Clean and return.
    result = []
    for part in parts:
        part = part.strip()
        if part:
            # Ensure space after marker
            part = re.sub(r'([۰-۹0-9]+[\)\.])([^\s])', r'\1 \2', part)
            result.append(part)
    return result if len(result) > 1 else [line]  # Only split if there are multiple items

def process_text_block(block):
    """
    Process a block of text (may contain multiple lines) and return formatted lines.
    Handles headings and list splitting recursively.
    """
    lines = block.splitlines()
    output = []
    for line in lines:
        line = line.strip()
        if not line:
            output.append('')
            continue
        # Check if line contains a heading prefix
        heading, rest = split_heading_and_rest(line)
        if heading is not None:
            # Add heading line with markdown prefix
            for pattern, prefix in HEADING_PATTERNS:
                if re.match(pattern, heading):
                    output.append(f'{prefix} {heading}')
                    break
            # Process the rest (which may contain inline lists)
            if rest:
                # Split rest into list items if needed
                items = split_inline_list(rest)
                for item in items:
                    output.append(item)
        else:
            # No heading – split into list items if needed, otherwise keep as is
            items = split_inline_list(line)
            for item in items:
                output.append(item)
    return output

def format_law_text(content: str) -> str:
    """Main entry point: format the entire law text."""
    # Split into blocks separated by blank lines (to preserve structure)
    blocks = re.split(r'\n\s*\n', content)
    all_lines = []
    for block in blocks:
        if not block.strip():
            continue
        formatted = process_text_block(block)
        all_lines.extend(formatted)
        all_lines.append('')  # Add blank line between blocks
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
    
    frontmatter, body = extract_frontmatter(raw_content)
    
    # Format the body (apply law formatting)
    formatted_body = format_law_text(body)
    
    # Extract metadata
    title = frontmatter.get('title', os.path.basename(md_path).replace('.md', '').replace('-', ' '))
    date = frontmatter.get('date', 'نامشخص')
    organ = frontmatter.get('organ', 'نامشخص')
    
    # Convert formatted markdown to HTML
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
