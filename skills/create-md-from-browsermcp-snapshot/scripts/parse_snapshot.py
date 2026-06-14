#!/usr/bin/env python3
import argparse
import re
import sys

def find_value_separator(s):
    in_quotes = False
    quote_char = None
    in_brackets = False
    
    for i, char in enumerate(s):
        if char in ('"', "'"):
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
        elif char == '[' and not in_quotes:
            in_brackets = True
        elif char == ']' and not in_quotes:
            in_brackets = False
        elif char == ':' and not in_quotes and not in_brackets:
            return i
    return -1

def parse_line(line):
    indent = len(line) - len(line.lstrip(' '))
    content = line.strip()
    is_list_item = False
    if content.startswith('- '):
        content = content[2:]
        is_list_item = True
    return indent, is_list_item, content

def clean_value(val):
    val = val.strip()
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    elif val.startswith("'") and val.endswith("'"):
        val = val[1:-1]
    return val

def parse_content(content):
    content = content.strip()
    if content.endswith(':'):
        content = content[:-1].strip()
        
    sep_idx = find_value_separator(content)
    value = None
    if sep_idx != -1:
        left = content[:sep_idx].strip()
        right = content[sep_idx+1:].strip()
        value = clean_value(right)
        content = left
        
    attrs = {}
    attr_matches = re.findall(r'\[([^\]]+)\]', content)
    for m in attr_matches:
        if '=' in m:
            k, v = m.split('=', 1)
            attrs[k.strip()] = v.strip()
        else:
            attrs[m.strip()] = True
            
    rest_content = re.sub(r'\s*\[[^\]]+\]\s*', ' ', content).strip()
    
    parts = rest_content.split(' ', 1)
    tag = parts[0].strip()
    rest = parts[1].strip() if len(parts) > 1 else ""
    quoted_text = None
    if rest:
        quoted_text = clean_value(rest)
        
    return tag, quoted_text, attrs, value

class Node:
    def __init__(self, indent, is_list, content):
        self.indent = indent
        self.is_list = is_list
        self.content = content
        self.tag, self.quoted_text, self.attrs, self.value = parse_content(content)
        self.children = []

def build_tree(parsed_nodes):
    root = Node(-2, False, "root")
    stack = [root]
    for node in parsed_nodes:
        while stack[-1].indent >= node.indent:
            stack.pop()
        stack[-1].children.append(node)
        stack.append(node)
    return root

def render_node(node, depth=0):
    tag = node.tag
    children = node.children
    
    if tag == "text":
        return node.value or node.quoted_text or ""
    elif tag == "strong":
        inner = "".join(render_node(c, depth) for c in children).strip()
        if not inner:
            inner = node.value or node.quoted_text or ""
        return f"**{inner}**" if inner else ""
    elif tag == "emphasis":
        inner = "".join(render_node(c, depth) for c in children).strip()
        if not inner:
            inner = node.value or node.quoted_text or ""
        return f"*{inner}*" if inner else ""
    elif tag == "code":
        inner = "".join(render_node(c, depth) for c in children).strip()
        if not inner:
            inner = node.value or node.quoted_text or ""
        return f"`{inner}`" if inner else ""
    elif tag == "paragraph":
        inner = "".join(render_node(c, depth) for c in children)
        if not inner:
            inner = node.value or node.quoted_text or ""
        return f"\n\n{inner.strip()}\n\n"
    elif tag == "heading":
        level = int(node.attrs.get("level", 1))
        title = node.quoted_text or node.value or ""
        if not title:
            title = "".join(render_node(c, depth) for c in children).strip()
        return f"\n\n{'#' * level} {title}\n\n"
    elif tag == "blockquote":
        parts = [render_node(c, depth) for c in children]
        parts = [p.strip() for p in parts if p.strip()]
        inner = "\n\n".join(parts)
        lines = inner.split('\n')
        quoted_lines = []
        last_was_empty = False
        for line in lines:
            cleaned = line.strip()
            if cleaned:
                quoted_lines.append(f"> {cleaned}")
                last_was_empty = False
            else:
                if not last_was_empty:
                    quoted_lines.append(">")
                    last_was_empty = True
        return "\n\n" + "\n".join(quoted_lines) + "\n\n"
    elif tag == "list":
        return "".join(render_node(c, depth) for c in children)
    elif tag == "listitem":
        inner = "".join(render_node(c, depth + 1) for c in children).strip()
        if not inner:
            inner = node.value or node.quoted_text or ""
        inner = inner.replace('\n\n', '\n').strip()
        indent = "  " * depth
        lines = inner.split('\n')
        result_lines = [f"{indent}- {lines[0]}"]
        for line in lines[1:]:
            result_lines.append(f"{indent}  {line}")
        return "\n" + "\n".join(result_lines)
    elif tag == "link":
        url = ""
        for c in children:
            if c.tag == "/url":
                url = c.value or c.quoted_text or ""
                break
        text = node.quoted_text or node.value or url
        if not url and text.startswith("http"):
            url = text
        return f"[{text}]({url})" if url else text
    elif tag == "/url":
        return ""
    elif tag == "table":
        rows = []
        for rg in children:
            if rg.tag == "rowgroup":
                for r in rg.children:
                    if r.tag == "row":
                        cells = []
                        for cell in r.children:
                            if cell.tag == "cell":
                                cell_content = "".join(render_node(c, 0) for c in cell.children).strip()
                                cell_content = cell_content.replace('\n', ' ').strip()
                                if not cell_content:
                                    cell_content = cell.quoted_text or cell.value or ""
                                cells.append(cell_content)
                        if cells:
                            rows.append(cells)
        if not rows:
            return ""
        num_cols = max(len(r) for r in rows)
        for r in rows:
            while len(r) < num_cols:
                r.append("")
        col_widths = [max(len(str(rows[j][i])) for j in range(len(rows))) for i in range(num_cols)]
        
        md_table = []
        header = "| " + " | ".join(rows[0][i].ljust(col_widths[i]) for i in range(num_cols)) + " |"
        md_table.append(header)
        separator = "| " + " | ".join("-" * col_widths[i] for i in range(num_cols)) + " |"
        md_table.append(separator)
        for row in rows[1:]:
            row_str = "| " + " | ".join(row[i].ljust(col_widths[i]) for i in range(num_cols)) + " |"
            md_table.append(row_str)
        return "\n\n" + "\n".join(md_table) + "\n\n"
    elif tag in ("tab", "button", "img", "navigation", "status", "document", "main", "root"):
        parts = [render_node(c, depth) for c in children]
        parts = [p.strip() for p in parts if p.strip()]
        return "\n\n".join(parts)
    else:
        inner = "".join(render_node(c, depth) for c in children).strip()
        if not inner:
            inner = node.value or node.quoted_text or ""
        return inner

def clean_markdown(md):
    md = re.sub(r'\n{3,}', '\n\n', md)
    lines = md.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    return '\n'.join(cleaned_lines)

def main():
    parser = argparse.ArgumentParser(description="Convert BrowserMCP accessibility tree snapshot to Markdown.")
    parser.add_argument("--input", required=True, help="Path to the captured snapshot file")
    parser.add_argument("--output", required=True, help="Path to write the reconstructed Markdown")
    parser.add_argument("--start-heading", help="Optional heading title to start parsing from")
    parser.add_argument("--end-marker", help="Optional text marker to stop parsing (e.g. copyright footer)")
    
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)
        
    yaml_start = 0
    for idx, line in enumerate(lines):
        if line.strip() == 'Page Snapshot' or line.strip() == '```yaml':
            yaml_start = idx + 1
            break
            
    snapshot_lines = lines[yaml_start:]
    
    parsed_nodes = []
    for line in snapshot_lines:
        if line.strip() == '```' or not line.strip():
            continue
        indent, is_list_item, content = parse_line(line)
        parsed_nodes.append(Node(indent, is_list_item, content))
        
    if not parsed_nodes:
        print("No accessibility tree nodes found in input file!", file=sys.stderr)
        sys.exit(1)
        
    root = build_tree(parsed_nodes)
    
    main_node = None
    def find_main(node):
        if node.tag == "main":
            return node
        for child in node.children:
            res = find_main(child)
            if res:
                return res
        return None
        
    main_node = find_main(root)
    
    nodes_to_render = []
    if main_node:
        nodes_to_render = main_node.children
    else:
        nodes_to_render = root.children
        
    filtered_children = []
    started = True if not args.start_heading else False
    
    for child in nodes_to_render:
        if not started:
            if child.tag == "heading" and (child.quoted_text == args.start_heading or child.value == args.start_heading):
                started = True
        
        if started:
            if args.end_marker and child.tag == "text" and child.value and args.end_marker in child.value:
                break
            filtered_children.append(child)
            
    if not filtered_children:
        print("No content matched the start/end filters. Rendering all content.", file=sys.stderr)
        filtered_children = nodes_to_render
        
    parts = [render_node(child) for child in filtered_children]
    parts = [p.strip() for p in parts if p.strip()]
    markdown_output = "\n\n".join(parts)
    markdown_output = clean_markdown(markdown_output)
    
    try:
        with open(args.output, "w", encoding="utf-8") as out:
            out.write(markdown_output)
        print(f"Markdown successfully reconstructed and saved to {args.output}")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
