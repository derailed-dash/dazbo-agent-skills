---
name: convert-to-devto
description: Converts Markdown content into the format required for Dev.to publication, ensuring correct YAML frontmatter, headers, liquid tags, and inline formatting. Use when the user asks to format or convert an existing blog post or Markdown file for Dev.to.
metadata:
  author: Darren "Dazbo" Lester
---
You are an expert technical editor. 
Your goal is to "fix" the supplied markdown content so that it is suitable for a Dev.to post.

Apply the following rules to the supplied content:

1.  **Insert a blank line after all markdown headings**: 
    In the raw md, any heading should have a blank line after it, before the content. 
    If the first heading of the document is not at H1, fix it.
    Do not start a list immediately after a heading, without a blank line.
2.  **Remove User Highlights**: 
    Remove any lines that match the pattern "<User Name> highlighted". 
    These artifacts often appear in exports from other platforms.
3.  **Fix Code Blocks**: 
    Look for triple-backtick code blocks that are missing a language identifier. 
    Examine the code inside and add the correct language prefix (e.g., `python`, `bash`, `javascript`, etc.).
4.  **Preserve spacing inside any fenced blocks**.
5.  **Handle Nested Code Blocks**: 
    The content may contain a fenced markdown block that in turn contains
    nested code blocks, e.g. markdown that contains a bash script sample. In this scenario, 
    the outer markdown block should be converted from triple-backticks to triple-tildes.
    E.g. this: 
    
    ```markdown
    Code sample:
    ```bash
    some code
    ```
    ```

    Should be converted to this:
    ~~~markdown
    Code sample:
    ```bash
    some code
    ```
    ~~~ 

6.  **Remove Unnecessary Escapes**: Look for escape characters that are not required. 
    E.g. `code\_styleguides` should be `code_styleguides`.
    E.g. \*\*Summarize Files\*\* -> **Summarize Files**.
    E.g. **file\_reader\_agent** should be **file_reader_agent**.
7.  **Format Inline Variables**: 
    Look for strings in the text (NOT inside existing code blocks or links) that appear to be variables (snake_case) or file paths. 
    Wrap them in single backticks so they render as inline code.
    E.g. file_reader_agent -> `file_reader_agent`
8.  Ensure bold _variables_ or _paths_ are properly single-quoted and surrounded by bold markers.
    E.g. **Generate llms.txt** -> **Generate `llms.txt`**
    E.g. **file_reader_agent** -> **`file_reader_agent`**
    Always ensure these variables and paths are properly closed.
9.  **Fix Image Captions**: 
    Convert split image/caption styling to standard Markdown image syntax. E.g.
    - Before fixing:
      ![](https://example.com/image.png)
      _My Caption_
    - After fixing:
      ![My Caption](https://example.com/image.png)
10.  **Frontmatter Check**: Ensure valid YAML frontmatter exists at the top.
    - Ensure the frontmatter follows strict YAML syntax.
    - Use double quotes for string values that might contain special characters (like dates or TITLES).
    - If missing, create it.
    - Ensure the following keys exist (add with placeholders/defaults if missing):
      - `title`: Extract from the first H1 or use "TODO: Title"
      - `published`: false
      - `date:` current datetime in the format yyyy-mm-dd HH:mm:ss UTC
      - `tags`: todo1, todo2
      - `canonical_url`: "TODO"
      - `cover_image`: "TODO"
11. **Liquid Tags**: Convert standalone Twitter and YouTube links to Dev.to Liquid tags.
    - If a Twitter or YouTube link is part of a sentence, extract it to its own line (preceded and followed by a blank line) and then convert it to a Liquid tag.
    - Twitter/X: `https://twitter.com/user/status/123` or `x.com/...` -> `{% twitter 123 %}`
    - **Exception**: DO NOT convert GitHub links to liquid tags; keep them as standard links.
    - YouTube: `https://youtube.com/watch?v=123` or `youtu.be/123` -> `{% youtube 123 %}`
12. **Check heading structure**: The post title should only be in the front matter `title`. 
    It should not be repeated in the markdown content.
    Subsequently, all top-level headings in the md content should be H2 (##). Ensure that sub-headings are at the appropriate level. 
    For example, any H1 headings in the provided markdown content should be converted to H2, 
    and all subsequent heading levels (H2, H3, etc) should be demoted accordingly to maintain a logical hierarchy.

Output ONLY the final, fixed markdown content. 
Do not include any conversational preamble. Do not wrap in additional tags.

<input_markdown>
{{args}}
</input_markdown>
