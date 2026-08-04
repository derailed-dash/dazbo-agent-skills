---
name: create-md-from-browsermcp-snapshot
description: |
  Extracts and converts BrowserMCP accessibility tree snapshots into clean, 
  high-fidelity Markdown documents with correct structures (headings, lists, 
  tables, blockquotes, formatting, and links). Use when the user asks to create a markdown document
  from a webpage; especially if they ask to do it with BrowserMCP.
metadata:
  author: Darren "Dazbo" Lester
  repository: https://github.com/derailed-dash/dazbo-agent-skills
  mcp: browsermcp
  tools:
    - browser_navigate
    - browser_snapshot
---

# Create Markdown from BrowserMCP Snapshot

This skill converts a raw accessibility tree snapshot captured by BrowserMCP (via the `browser_snapshot` tool) into a beautifully formatted, high-fidelity Markdown document.

## Prerequisites & BrowserMCP Check

> [!IMPORTANT]
> This skill strictly requires the **BrowserMCP** server to be installed and available in the environment.

Before attempting to navigate a site or capture a snapshot:

1. **Verify Tool Availability**: Check whether the `browsermcp` server and its `browser_snapshot` tool are present in your active MCP tools list.
2. **If BrowserMCP is NOT Found**:
   - Stop execution immediately and notify the user.
   - Guide the user to install BrowserMCP and configure the `browsermcp` server entry in their MCP configuration (e.g. in `~/.gemini/config/mcp_config.json` or Antigravity MCP settings).
   - Request that the user re-run the task once BrowserMCP is enabled and available.

## When to Use

Use this skill when:
- You have captured a webpage's accessibility tree YAML using the BrowserMCP `browser_snapshot` tool.
- You need to generate a structured, high-fidelity Markdown (`.md`) representation of the page content.
- You want to extract clean lists, tables, headers, blockquotes, and link destinations from the captured page layout.

Note: This skill complements browser navigation using the BrowserMCP tool. It is NOT intended to be used with other browser navigation tools, such as Playwright or the Antigravity built-in browser agent. Be sure to be explicit about what tools to use and what to avoid.

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

1. **Verify BrowserMCP**: Confirm `browsermcp` is installed as detailed in [Prerequisites & BrowserMCP Check](#prerequisites--browsermcp-check). If absent, guide the user to install it.
2. **Capture Snapshot**: Navigate to the target URL using `browser_navigate` and run `browser_snapshot` to output the accessibility tree YAML.
3. **Execute Parser**: Run the Python script `parse_snapshot.py` passing the absolute path of the captured snapshot text file as an argument and specifying the output Markdown path:

```bash
python3 ./create-md-from-browsermcp-snapshot/scripts/parse_snapshot.py --input <snapshot_path> --output <markdown_path> [--start-heading <heading_title>] [--end-marker <footer_text>]
```
