---
name: convert-to-devto
description: |
  Converts Markdown content into the format required for Dev.to publication, ensuring valid YAML frontmatter, clean heading hierarchy, Forem-safe code fences, Liquid tags, and inline formatting. Use when preparing or converting a blog post or Markdown file for publishing on Dev.to.
metadata:
  author: Darren "Dazbo" Lester
  repository: https://github.com/derailed-dash/dazbo-agent-skills
---

# Convert Markdown to Dev.to

Prepares standard or Medium-exported Markdown articles for clean rendering on **Dev.to (Forem)**. Because Forem runs a custom Liquid pre-processor and the `Redcarpet` Markdown parser before rendering HTML, naive Markdown exports frequently break code blocks, leak raw backslashes, reset numbered lists, or lose embedded tables.

## Table of Contents

- [1. Frontmatter & Heading Structure](#1-frontmatter--heading-structure)
- [2. Inline Formatting & Escape Cleanup](#2-inline-formatting--escape-cleanup)
- [3. Code Fences & Forem Parser Quirks](#3-code-fences--forem-parser-quirks)
- [4. Lists, Tables, Images & Liquid Embeds](#4-lists-tables-images--liquid-embeds)
- [5. Dev.to Call-to-Action & Output Delivery](#5-devto-call-to-action--output-delivery)

---

## 1. Frontmatter & Heading Structure

1. **YAML Frontmatter**: Ensure valid, strict YAML frontmatter exists at the very top of the file. Wrap string values containing colons or special characters (such as dates or titles) in double quotes. Add any missing keys with placeholders/defaults:
   - `title`: Extract from the first H1 heading, or set `"TODO: Title"`
   - `published`: `false`
   - `date`: Current datetime in `yyyy-mm-dd HH:mm:ss UTC` format
   - `tags`: `todo1, todo2`
   - `canonical_url`: `"TODO"`
   - `cover_image`: `"TODO"`
2. **Heading Hierarchy (No Body H1)**: The article title lives strictly in the frontmatter `title` — never repeat it inside the Markdown body. Convert any top-level body `#` (`H1`) heading to `##` (`H2`), and demote all nested sub-headings (`H2` -> `H3`, etc.) so the outline stays logical.
3. **Blank Lines After Headings**: Ensure every Markdown heading (`#`, `##`, `###`, `####`) has a blank line immediately after it before any paragraph, list, or code fence.
4. **Remove Export Artefacts**: Strip platform export noise such as `"<User Name> highlighted"` lines.

---

## 2. Inline Formatting & Escape Cleanup

1. **Remove Unnecessary Escapes**: Strip redundant Markdown backslashes:
   - `code\_styleguides` -> `code_styleguides`
   - `\*\*Summarise Files\*\*` -> `**Summarise Files**`
   - `**file\_reader\_agent**` -> `**file_reader_agent**`
   - **Dollar signs (`\$` -> `$`)**: Dev.to's `Redcarpet` parser does **not** treat `$` as an escapable Markdown character (unlike KaTeX/LaTeX environments). Writing `\$0.02` in prose renders literally with the backslash (`\$0.02`). Strip all `\$` escapes in prose so currency amounts appear cleanly as `$0.02`.
2. **Format Inline Identifiers & Paths**: Scan prose (outside existing code blocks and links) for `snake_case` variable names or file paths and wrap them in balanced single backticks (e.g. `file_reader_agent` -> `` `file_reader_agent` ``).
3. **Bold + Code Markers**: Ensure bold variables or paths wrap single backticks cleanly inside the bold markers and are properly closed (e.g. **Generate `llms.txt`**, `` **`file_reader_agent`** ``).

---

## 3. Code Fences & Forem Parser Quirks

1. **Language Tags & Inner Spacing**: Add the appropriate language identifier (`python`, `bash`, `javascript`, etc.) to any bare ```` ``` ```` code fence, and preserve all indentation/spacing inside fenced blocks.
2. **Nested Code Blocks (Use Tildes)**: When an outer Markdown fenced block contains nested fenced code blocks, convert the outer fence from triple-backticks to triple-tildes (`~~~markdown` ... `~~~`).

   Before (broken triple-backtick nesting):

   ~~~~markdown
   ```markdown
   Code sample:
   ```bash
   some code
   ```
   ```
   ~~~~

   After (outer fence converted to triple-tildes):

   ~~~markdown
   Code sample:
   ```bash
   some code
   ```
   ~~~

3. **Highlighter Label Glitch (`toml` / `ini`)**: If a backtick block such as ```` ```toml ```` or ```` ```ini ```` renders with the language name displayed literally at the top, convert it to a tilde block (`~~~toml` or `~~~~toml`).
4. **Liquid/Jekyll Escaping**:
   - **NEVER use `{% raw %}` or `{% endraw %}` tags** around or inside code blocks. Dev.to blocks the `raw` Liquid tag in user posts and crashes page rendering with `Liquid syntax error: Unknown tag 'endraw'`.
   - Inside fenced code blocks (```` ``` ```` or `~~~`), Dev.to automatically disables Liquid compilation. Keep YAML or GitHub Actions expressions containing double curly braces (such as `${{ secrets.GEMINI_API_KEY }}`) completely unchanged.

> [!CAUTION]
> **CRITICAL — Never Put Multiple Backticks Inside Inline Code Spans (Forem `CODE_BLOCKS_REGEX` Bug)**
>
> Before passing Markdown to `Redcarpet::Markdown`, Forem's [`MarkdownProcessor::Parser`](https://github.com/forem/forem/blob/main/app/services/markdown_processor/parser.rb) pre-processes all code spans and fenced blocks with a lazy multiline regex:
>
> ```ruby
> # From forem/app/services/markdown_processor/parser.rb:
> CODE_BLOCKS_REGEX = /(~{3}|`{3}|`{2}|`)[\s\S]*?\1/
>
> def escape_liquid_tags_in_codeblock(code_tag_content)
>   code_tag_content.gsub(CODE_BLOCKS_REGEX) do |code|
>     "{% raw %}#{code}{% endraw %}"
>   end
> end
> ```
>
> Because `CODE_BLOCKS_REGEX` only has branches for `~{3}`, `` `{3} ``, `` `{2} ``, and `` ` `` (with **no ` `{4} ` branch** and `[\s\S]*?` matching across newlines), any inline code span containing triple backticks or mismatched backticks corrupts the rest of the post:
> - **Failure Example**: Writing `` ` ```suggestion ` `` (5 backticks: `1 + 3 + 1`) matches the 1st backtick against the 1st backtick of `` ``` ``, leaving two backticks (`` `` ``) that open a **2-backtick (` `{2} `) multiline match** scanning dozens of lines down until it eats the opening two backticks of your next `` ```yaml `` block.
> - **Symptom on Dev.to**: Every subsequent code block breaks — rendering `` ```yaml `` as a stray backtick, an empty grey code pill, and plain text leaking YAML/bash into body paragraphs.
> - **Mandatory Fixes**:
>   1. **NEVER** write triple backticks inside an inline code span (never write `` ` ```suggestion ` ``, `` `` ```suggestion `` ``, or ```` ```` ```suggestion ```` ````). Refer to fence identifiers cleanly in prose as `` `suggestion` `` blocks or `` `yaml` `` blocks.
>   2. Ensure every inline code span uses strictly balanced single backticks (`` `code` ``) with no nested or stray backticks.
>   3. Always place a blank line immediately before an opening code fence (```` ```lang ````) and immediately after a closing code fence (```` ``` ````).

---

## 4. Lists, Tables, Images & Liquid Embeds

1. **Prevent Ordered-List Resets in `Redcarpet`**: `Redcarpet` breaks an `<ol>` list and restarts numbering at `1.` if a list item contains a blank line followed by an unindented or 3-space-indented paragraph. Keep each numbered item (`1. **Heading:** Text...`) as a single contiguous paragraph, **or** indent continuation paragraphs/blocks by strictly **4 spaces** to preserve `1.`, `2.`, `3.`, `4.`.
2. **Replace Datawrapper `<iframe>` Blocks with Markdown Tables**: Medium exports tables as `<iframe src="https://cdn.embedly.com/widgets/media.html?...datawrapper...">`, which Dev.to strips. Whenever converting a Medium export containing a Datawrapper `<iframe>`, replace it with the original native Markdown table from the source `.md` draft.
3. **Fix Split Image Captions**: Merge split image/caption lines into standard Markdown alt-text syntax:
   - Before:
     ```markdown
     ![](https://example.com/image.png)
     _My Caption_
     ```
   - After:
     ```markdown
     ![My Caption](https://example.com/image.png)
     ```
4. **Optional Image Hosting Conversion (jsDelivr CDN / Raw GitHub)**: If the user or repository specifies a public GitHub repo for media assets (e.g. `--repo user/repo --branch main`), rewrite relative local image paths (e.g. `![Alt](media/foo.png)`) to public URLs:
   - CDN format (recommended): `https://cdn.jsdelivr.net/gh/<user>/<repo>@<branch>/<path/to/media/foo.png>`
   - Raw GitHub format: `https://raw.githubusercontent.com/<user>/<repo>/<branch>/<path/to/media/foo.png>`
   - Otherwise, keep existing URLs intact or leave relative paths for review.
5. **Convert Standalone Twitter/X & YouTube Links to Liquid Tags**: Extract inline Twitter/X or YouTube links onto their own paragraph (preceded and followed by a blank line) and convert them:
   - Twitter/X (`https://twitter.com/user/status/123` or `x.com/...`) -> `{% twitter 123 %}`
   - YouTube (`https://youtube.com/watch?v=123` or `youtu.be/123`) -> `{% youtube 123 %}`
   - **Exceptions**:
     - Do **not** convert GitHub links to Liquid tags; leave them as standard Markdown links.
     - Do **not** convert YouTube links inside bulleted URL/reference sections (such as *"Useful Links and References"* or *"Project Demo & Portfolio"*); keep them as standard Markdown links (e.g. `- [FinSavant YouTube Demo](https://www.youtube.com/watch?v=zs_IRUxIx4E)`) so large video players do not break up link lists.

---

## 5. Dev.to Call-to-Action & Output Delivery

1. **Adapt the "Before You Go" Section**: Dev.to uses multi-reactions (❤️ 🦄 🤯 🙌 🔥) and bookmarks (🔖) rather than Medium claps (👏) and email subscribe bells (🔔). Whenever the draft includes a Medium "Before You Go" section, replace it with:

   ```markdown
   ## Before You Go

   - **Please share** 📢 this with anyone that you think will be interested. It might help them, and it really helps me!
   - Please **drop some reactions** ❤️ 🦄 🔥 (you can pick more than one!) and **bookmark** 🔖 this post!
   - Please **leave a comment** 💬. Interaction is good!
   - **Add a star** ⭐ on my repos!
   - **Follow** 👉 me here on Dev.to, so you don’t miss my content.
   ```

2. **Output Delivery**: When converting a file on disk, write the converted Markdown directly to the requested output path (e.g. `<slug>-devto.md`) without modifying the original source draft unless asked. When converting inline text, output only the final Dev.to-ready Markdown without conversational preamble or wrapper tags.
