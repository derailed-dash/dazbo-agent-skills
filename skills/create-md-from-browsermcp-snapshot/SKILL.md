---
name: create-md-from-browsermcp-snapshot
description: |
  Extracts and converts BrowserMCP accessibility tree snapshots into clean,
  high-fidelity Markdown documents with correct structures (headings, lists,
  tables, blockquotes, code blocks, formatting, and links). Use when the user
  asks to create a Markdown document from a webpage; especially if they ask to
  do it with BrowserMCP.
metadata:
  author: Darren "Dazbo" Lester
  repository: https://github.com/derailed-dash/dazbo-agent-skills
  mcp: browsermcp
  tools:
    - browser
---

# Create Markdown from BrowserMCP Snapshot

This skill converts a raw accessibility tree snapshot captured by BrowserMCP (via the `browser` tool's `snapshot` command in BrowserMCP 2.0+, or the legacy `browser_snapshot` tool in 1.x) into a cleanly formatted, high-fidelity Markdown document.

## Prerequisites & BrowserMCP Check

> [!IMPORTANT]
> This skill strictly requires the **BrowserMCP** server (2.0+ recommended) and Chrome extension to be installed and available in the environment.

Before attempting to navigate a site or capture a snapshot:

1. **Verify Tool Availability**: Check whether the `browsermcp` server and its `browser` tool (or legacy `browser_snapshot` tool) are present in your active MCP tools list.
2. **If BrowserMCP is NOT Found**:
   - Stop execution immediately and notify the user.
   - Guide the user to install BrowserMCP 2.0+ (`@browsermcp/mcp@latest`) and configure the `browsermcp` server entry in their MCP configuration (e.g. in `config/mcp_config.json` or Antigravity MCP settings):
     ```json
     {
       "mcpServers": {
         "browsermcp": {
           "command": "npx",
           "args": ["-y", "@browsermcp/mcp@latest"]
         }
       }
     }
     ```
   - Request that the user re-run the task once BrowserMCP is enabled and connected.

## When to Use

Use this skill when:
- You have captured a webpage's accessibility tree YAML using the BrowserMCP `browser` tool (`snapshot --max 50000`).
- You need to generate a structured, high-fidelity Markdown (`.md`) representation of the page content.
- You want to extract clean headings, lists, tables (including `columnheader` rows), fenced code blocks, blockquotes, inline formatting, and link destinations from the captured page layout.

Note: This skill complements browser navigation using the BrowserMCP tool. It is NOT intended to be used with other browser navigation tools, such as Playwright or the Antigravity built-in browser agent. Be sure to be explicit about what tools to use and what to avoid.

## How it Works

The skill runs a Python parser (`parse_snapshot.py`) that reads the captured accessibility tree YAML snapshot, reconstructs character-indexed `undefined` inline text nodes emitted by BrowserMCP 2.0, builds a parent-child node hierarchy, unwraps nested structural containers (`main`, `article`, `generic`), and recursively converts the tags and attributes into Markdown text.

### Folder Structure

```
create-md-from-browsermcp-snapshot/
├── SKILL.md
└── scripts/
    └── parse_snapshot.py
```

### Execution Procedure

1. **Verify BrowserMCP**: Confirm `browsermcp` (`browser` tool) is installed as detailed in [Prerequisites & BrowserMCP Check](#prerequisites--browsermcp-check). If absent, guide the user to install it.
2. **Capture Snapshot**: Call the `browsermcp` `browser` tool with newline-separated commands to navigate to the target URL and capture a full accessibility tree snapshot using `--max 50000` (so output is not truncated at the default 10,000-character cap):
   ```text
   goto <url>
   snapshot --max 50000
   ```
   *(Tip: To avoid disturbing the user's active tab, you can open a temporary background tab with `tab new <url>`, run `snapshot --max 50000`, and close it with `tab close`. For very large pages, you can also scope the snapshot to the main content element, e.g. `snapshot main --max 50000` or `snapshot article --max 50000`.)*
3. **Save Snapshot Text**: If the MCP response is not already saved to a step output file on disk, write the raw snapshot output to a temporary file.
4. **Execute Parser**: Run `parse_snapshot.py`, passing the path of the captured snapshot text file and specifying the output Markdown path:

```bash
uv run python ~/.gemini/config/skills/create-md-from-browsermcp-snapshot/scripts/parse_snapshot.py \
  --input <snapshot_path> \
  --output <markdown_path> \
  [--start-heading "<heading_title>"] \
  [--end-marker "<footer_text>"]
```
