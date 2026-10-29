#!/usr/bin/env python3
"""Convert BrowserMCP accessibility tree YAML snapshots into clean Markdown.

Supports both BrowserMCP 2.0 (single `browser` tool with `snapshot` command,
character-indexed `undefined` inline text nodes, `[url=...]` attributes,
`columnheader` cells, and `figure`/`code` blocks) and legacy BrowserMCP 1.x
(`browser_snapshot` tool) outputs.
"""

import argparse
import re
import sys

NO_SPACE_BEFORE = tuple(".,;:!?)]}")
NO_SPACE_AFTER = tuple("([{\"'/")
BLOCK_TAGS = frozenset(
    {
        "heading",
        "paragraph",
        "blockquote",
        "list",
        "table",
        "figure",
        "article",
        "section",
        "main",
        "document",
        "root",
    }
)
FLATTENABLE_CONTAINERS = frozenset({"main", "article", "section", "generic", "document", "root"})


def find_value_separator(s: str) -> int:
    """Return index of the first colon outside quotes and square brackets, or -1."""
    in_quotes = False
    quote_char: str | None = None
    in_brackets = False

    for i, char in enumerate(s):
        if char in ('"', "'"):
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
        elif char == "[" and not in_quotes:
            in_brackets = True
        elif char == "]" and not in_quotes:
            in_brackets = False
        elif char == ":" and not in_quotes and not in_brackets:
            return i
    return -1


def parse_line(line: str) -> tuple[int, bool, str]:
    """Extract indentation level, list-item flag, and stripped content from a YAML line."""
    indent = len(line) - len(line.lstrip(" "))
    content = line.strip()
    is_list_item = False
    if content.startswith("- "):
        content = content[2:]
        is_list_item = True
    return indent, is_list_item, content


def clean_value(val: str) -> str:
    """Strip surrounding whitespace and matching single/double quotes."""
    val = val.strip()
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
        val = val[1:-1]
    return val


def parse_content(content: str) -> tuple[str, str | None, dict[str, str | bool], str | None]:
    """Parse a node's tag, quoted label, bracketed attributes, and colon value."""
    content = content.strip()

    sep_idx = find_value_separator(content)
    value: str | None = None
    if sep_idx != -1:
        left = content[:sep_idx].strip()
        right = content[sep_idx + 1 :].strip()
        value = clean_value(right) if right else None
        content = left
    elif content.endswith(":"):
        content = content[:-1].strip()

    attrs: dict[str, str | bool] = {}
    attr_matches = re.findall(r"\[(\d+=.|[^\]]+)\]", content)
    for m in attr_matches:
        if "=" in m:
            k, v = m.split("=", 1)
            k_clean = k.strip()
            # Preserve exact single-character values (including spaces) for numeric indices
            attrs[k_clean] = v if k_clean.isdigit() else v.strip()
        else:
            attrs[m.strip()] = True

    rest_content = re.sub(r"\s*\[(?:\d+=.|[^\]]+)\]\s*", " ", content).strip()

    parts = rest_content.split(" ", 1)
    tag = parts[0].strip()
    rest = parts[1].strip() if len(parts) > 1 else ""
    quoted_text: str | None = None
    if rest:
        quoted_text = clean_value(rest)

    # Reconstruct character-indexed text emitted by BrowserMCP 2.0 (`- undefined [0=B] [1=r]...`)
    char_indices = sorted(int(k) for k in attrs if k.isdigit())
    if char_indices and value is None and quoted_text is None:
        value = "".join(str(attrs[str(idx)]) for idx in char_indices)

    return tag, quoted_text, attrs, value


class Node:
    """Represents a single node in the BrowserMCP accessibility tree."""

    def __init__(self, indent: int, is_list: bool, content: str) -> None:
        self.indent = indent
        self.is_list = is_list
        self.content = content
        self.tag, self.quoted_text, self.attrs, self.value = parse_content(content)
        self.children: list[Node] = []


def build_tree(parsed_nodes: list[Node]) -> Node:
    """Build a parent-child tree from indentation-ordered nodes."""
    root = Node(-2, False, "root")
    stack = [root]
    for node in parsed_nodes:
        while stack[-1].indent >= node.indent:
            stack.pop()
        stack[-1].children.append(node)
        stack.append(node)
    return root


def join_inline_parts(parts: list[str]) -> str:
    """Join rendered inline fragments, inserting spaces where needed around inline tags."""
    result = ""
    for part in parts:
        if not part:
            continue
        if not result:
            result = part
            continue
        if (
            result[-1].isspace()
            or part[0].isspace()
            or result.endswith(NO_SPACE_AFTER)
            or part.startswith(NO_SPACE_BEFORE)
        ):
            result += part
        else:
            result += f" {part}"
    return result


def join_inline(children: list[Node], depth: int = 0) -> str:
    """Render and join a sequence of inline child nodes."""
    return join_inline_parts([render_node(c, depth) for c in children])


def extract_heading_title(node: Node, depth: int = 0) -> str:
    """Extract clean heading text, unwrapping self-anchor links and ignoring buttons."""
    if node.quoted_text or node.value:
        return node.quoted_text or node.value or ""

    parts: list[str] = []
    for child in node.children:
        if child.tag == "button":
            continue
        if child.tag == "link" and str(child.attrs.get("url", "")).startswith("#"):
            text = (
                child.quoted_text
                or child.value
                or join_inline(child.children, depth).strip()
            )
            if text:
                parts.append(text)
        else:
            rendered = render_node(child, depth).strip()
            if rendered:
                parts.append(rendered)
    return join_inline_parts(parts).strip()


def is_multiline_code_node(node: Node) -> bool:
    """Return True if a `code` node represents a fenced multi-line code block."""
    if node.tag != "code" or not node.children:
        return False
    return any(c.tag == "generic" for c in node.children) or len(node.children) > 1


def render_node(node: Node, depth: int = 0) -> str:
    """Recursively render a parsed accessibility tree Node into Markdown."""
    tag = node.tag
    children = node.children

    if tag in ("text", "undefined"):
        return node.value or node.quoted_text or ""
    if tag in ("button", "status", "navigation", "complementary", "/url"):
        return ""
    if tag == "strong":
        inner = join_inline(children, depth).strip()
        if not inner:
            inner = node.value or node.quoted_text or ""
        return f"**{inner}**" if inner else ""
    if tag == "emphasis":
        inner = join_inline(children, depth).strip()
        if not inner:
            inner = node.value or node.quoted_text or ""
        return f"*{inner}*" if inner else ""
    if tag == "code":
        if is_multiline_code_node(node):
            lines = [render_node(c, depth) for c in children]
            block = "\n".join(lines)
            return f"\n\n```\n{block}\n```\n\n"
        inner = join_inline(children, depth).strip()
        if not inner:
            inner = node.value or node.quoted_text or ""
        return f"`{inner}`" if inner else ""
    if tag == "paragraph":
        inner = join_inline(children, depth) if children else ""
        if not inner:
            inner = node.value or node.quoted_text or ""
        return f"\n\n{inner.strip()}\n\n" if inner.strip() else ""
    if tag == "heading":
        level = int(str(node.attrs.get("level", 1)))
        title = extract_heading_title(node, depth)
        return f"\n\n{'#' * level} {title}\n\n" if title else ""
    if tag == "blockquote":
        parts = [render_node(c, depth).strip() for c in children]
        parts = [p for p in parts if p]
        inner = "\n\n".join(parts)
        lines = inner.split("\n")
        quoted_lines: list[str] = []
        last_was_empty = False
        for line in lines:
            cleaned = line.strip()
            if cleaned:
                quoted_lines.append(f"> {cleaned}")
                last_was_empty = False
            elif not last_was_empty:
                quoted_lines.append(">")
                last_was_empty = True
        return "\n\n" + "\n".join(quoted_lines) + "\n\n"
    if tag == "list":
        return "".join(render_node(c, depth) for c in children)
    if tag == "listitem":
        inline_parts: list[str] = []
        subblocks: list[str] = []
        for c in children:
            if c.tag == "list":
                subblocks.append(render_node(c, depth + 1).rstrip())
            else:
                inline_parts.append(render_node(c, depth + 1).strip())
        inner = join_inline_parts(inline_parts).strip()
        if not inner:
            inner = node.value or node.quoted_text or ""
        if subblocks:
            inner = "\n".join([inner, *subblocks]).strip()
        inner = inner.replace("\n\n", "\n").strip()
        indent_str = "  " * depth
        lines = inner.split("\n")
        result_lines = [f"{indent_str}- {lines[0]}"]
        for line in lines[1:]:
            result_lines.append(f"{indent_str}{line}" if line.startswith("  ") else f"{indent_str}  {line}")
        return "\n" + "\n".join(result_lines)
    if tag == "link":
        url = str(node.attrs.get("url", "")) if "url" in node.attrs else ""
        if not url:
            for c in children:
                if c.tag == "/url":
                    url = c.value or c.quoted_text or ""
                    break
        content_children = [c for c in children if c.tag != "/url"]
        text = node.quoted_text or node.value or ""
        if not text and content_children:
            if all(c.tag == "paragraph" for c in content_children):
                p_parts = [render_node(c, depth).strip() for c in content_children]
                text = " — ".join(p for p in p_parts if p)
            else:
                text = join_inline(content_children, depth).strip()
        if not text:
            text = url
        if not url and text.startswith("http"):
            url = text
        return f"[{text}]({url})" if url else text
    if tag == "table":
        rows: list[list[str]] = []
        row_containers = [
            rg for rg in children if rg.tag == "rowgroup"
        ] or [node]
        for container in row_containers:
            for r in container.children:
                if r.tag == "row":
                    cells: list[str] = []
                    for cell in r.children:
                        if cell.tag in ("cell", "columnheader", "rowheader", "gridcell"):
                            cell_content = join_inline(cell.children, 0).strip()
                            cell_content = cell_content.replace("\n", " ").strip()
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
        col_widths = [
            max(len(str(rows[j][i])) for j in range(len(rows)))
            for i in range(num_cols)
        ]

        md_table: list[str] = []
        header = (
            "| "
            + " | ".join(rows[0][i].ljust(col_widths[i]) for i in range(num_cols))
            + " |"
        )
        md_table.append(header)
        separator = (
            "| " + " | ".join("-" * max(col_widths[i], 3) for i in range(num_cols)) + " |"
        )
        md_table.append(separator)
        for row in rows[1:]:
            row_str = (
                "| "
                + " | ".join(row[i].ljust(col_widths[i]) for i in range(num_cols))
                + " |"
            )
            md_table.append(row_str)
        return "\n\n" + "\n".join(md_table) + "\n\n"
    if tag in ("tab", "img", "document", "main", "root", "article", "section", "figure", "region"):
        parts = [render_node(c, depth).strip() for c in children]
        parts = [p for p in parts if p]
        return "\n\n".join(parts)
    if tag == "generic":
        if not children:
            return node.value or node.quoted_text or ""
        parts = [render_node(c, depth).strip() for c in children]
        parts = [p for p in parts if p]
        return "\n\n".join(parts)

    inner = join_inline(children, depth).strip()
    if not inner:
        inner = node.value or node.quoted_text or ""
    return inner


def flatten_block_containers(nodes: list[Node]) -> list[Node]:
    """Unwrap nested structural containers (main, article, generic) into block nodes."""
    flattened: list[Node] = []
    for node in nodes:
        if node.tag in FLATTENABLE_CONTAINERS and node.children and any(
            c.tag in BLOCK_TAGS or c.tag == "generic" for c in node.children
        ):
            flattened.extend(flatten_block_containers(node.children))
        else:
            flattened.append(node)
    return flattened


def clean_markdown(md: str) -> str:
    """Collapse excessive blank lines and strip trailing spaces on each line."""
    md = re.sub(r"\n{3,}", "\n\n", md)
    lines = md.split("\n")
    cleaned_lines = [line.rstrip() for line in lines]
    return "\n".join(cleaned_lines)


def extract_snapshot_lines(lines: list[str]) -> list[str]:
    """Filter raw file lines down to accessibility tree YAML list lines."""
    yaml_start = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped in ("Page Snapshot", "```yaml") or stripped.startswith("✓ snapshot"):
            yaml_start = idx + 1
            break

    tree_lines: list[str] = []
    for line in lines[yaml_start:]:
        stripped = line.strip()
        if not stripped or stripped == "```":
            continue
        # Stop if trailing BrowserMCP 2.0 command output or truncation notice is reached
        if stripped.startswith(("✓ ", "✗ ", "… cut at ", "Page: ")):
            break
        if re.match(r"^\s*-\s+", line):
            tree_lines.append(line)
    return tree_lines


def main() -> None:
    """CLI entrypoint for converting a BrowserMCP snapshot file into Markdown."""
    parser = argparse.ArgumentParser(
        description="Convert BrowserMCP accessibility tree snapshot to Markdown."
    )
    parser.add_argument(
        "--input", required=True, help="Path to the captured snapshot file"
    )
    parser.add_argument(
        "--output", required=True, help="Path to write the reconstructed Markdown"
    )
    parser.add_argument(
        "--start-heading", help="Optional heading title to start parsing from"
    )
    parser.add_argument(
        "--end-marker",
        help="Optional text marker to stop parsing (e.g. copyright footer)",
    )

    args = parser.parse_args()

    try:
        with open(args.input, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    snapshot_lines = extract_snapshot_lines(lines)

    parsed_nodes: list[Node] = []
    for line in snapshot_lines:
        indent, is_list_item, content = parse_line(line)
        parsed_nodes.append(Node(indent, is_list_item, content))

    if not parsed_nodes:
        print("No accessibility tree nodes found in input file!", file=sys.stderr)
        sys.exit(1)

    root = build_tree(parsed_nodes)

    def find_main(node: Node) -> Node | None:
        if node.tag == "main":
            return node
        for child in node.children:
            res = find_main(child)
            if res:
                return res
        return None

    main_node = find_main(root)
    base_nodes = main_node.children if main_node else root.children
    nodes_to_render = flatten_block_containers(base_nodes)

    filtered_children: list[Node] = []
    started = not bool(args.start_heading)

    for child in nodes_to_render:
        if (
            not started
            and child.tag == "heading"
            and extract_heading_title(child, 0) == args.start_heading
        ):
            started = True

        if started:
            rendered_child = render_node(child)
            if args.end_marker and (
                (child.value and args.end_marker in child.value)
                or (rendered_child and args.end_marker in rendered_child)
            ):
                break
            filtered_children.append(child)

    if not filtered_children:
        print(
            "No content matched the start/end filters. Rendering all content.",
            file=sys.stderr,
        )
        filtered_children = nodes_to_render

    parts = [render_node(child).strip() for child in filtered_children]
    parts = [p for p in parts if p]
    markdown_output = "\n\n".join(parts)
    markdown_output = clean_markdown(markdown_output)

    try:
        with open(args.output, "w", encoding="utf-8") as out:
            out.write(markdown_output)
        print(f"Markdown successfully reconstructed and saved to {args.output}")
    except OSError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
