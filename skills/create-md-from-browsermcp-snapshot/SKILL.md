---
name: create-md-from-browsermcp-snapshot
description: |
  Extracts and converts BrowserMCP accessibility tree snapshots into clean, 
  high-fidelity Markdown documents with correct structures (headings, lists, 
  tables, blockquotes, formatting, and links).
---

# Create Markdown from BrowserMCP Snapshot

This skill converts a raw accessibility tree snapshot captured by BrowserMCP (via the `browser_snapshot` tool) into a beautifully formatted, high-fidelity Markdown document.

## When to Use

Use this skill when:
- You have captured a webpage's accessibility tree YAML using the BrowserMCP `browser_snapshot` tool.
- You need to generate a structured, high-fidelity Markdown (`.md`) representation of the page content.
- You want to extract clean lists, tables, headers, blockquotes, and link destinations from the captured page layout.

Note: this skill complements browser navigation using the BrowserMCP tool. It is NOT intended to be used with other browser navigation tools, such as Playwright or the Antigravity built-in browser agent. Be sure to be explicit about what tools to use and what to avoid.

## How it Works

The skill runs a Python parser that reads the captured accessibility tree YAML snapshot, builds a parent-child node hierarchy, and recursively converts the tags and properties into Markdown text.

### Folder Structure

```
create-md-from-browsermcp-snapshot/
├── SKILL.md
└── scripts/
    └── parse_snapshot.py
```

### Execution Procedure

1. **Capture Snapshot**: Navigate to the target URL using the BrowserMCP `browser_navigate` and run `browser_snapshot` to output the accessibility tree.
2. **Execute Parser**: Run the python script `parse_snapshot.py` passing the absolute path of the captured snapshot text file as an argument and specifying the output Markdown path.

```bash
python3 ./create-md-from-browsermcp-snapshot/scripts/parse_snapshot.py --input <snapshot_path> --output <markdown_path> [--start-heading <heading_title>] [--end-marker <footer_text>]
```
