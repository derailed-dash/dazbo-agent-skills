# Skills Writing and Best Practices

- Naming:
  - Consider using verb(ing)+noun.
  - Avoid vague descriptions, like "documentation".
- Description:
  - Always write in 3rd person.
  - Be specific and include key terms.
  - Include what the skill does and context/triggers for activation.  E.g. "Use when…"
- The model is smart. Don't include stuff the model should already know.
- Progressive disclosure:
  - Keep the skill body under 500 lines.
  - Split files when the body grows large.  E.g. "to do x, read ./thing-x.md and follow its instructions"
  - Use Unix-style paths when referencing files to load, for all platforms. (This does not apply to actual code or code snippets.)
  - Structure longer mds and reference files with a ToC at the top.
- Numbered lists work well for reliability.
- For complex multi-step workflows, consider validating intermediate steps.
- Provide code snippets/commands for low-freedom tasks. 
- Avoid offering too many options for solving a single problem.
- Consider providing pre-made scripts for utilities that will be run frequently, to save the model from having to generate the code. 
  - This improves consistency, and reduces latency and token usage.
  - Add information in the skill as to what output is expected from the script call.
- When using MCP tools, fully-qualify the tool name to help avoid not finding the right tool.
  - E.g. Use the BigQuery:bigquery_schema tool to retrieve table schemas.
  - E.g. Use the GitHub:create_issue tool to create issues.
- Don't assume all pre-reqs and packages are installed. If packages are required, provide instructions for how to install them.

## Patterns

### Complex Workflows

~~~
Research synthesis workflow

Copy this checklist and track your progress:

```
Research Progress:
- [ ] Step 1: Read all source documents
- [ ] Step 2: Identify key themes
- [ ] Step 3: Cross-reference claims
- [ ] Step 4: Create structured summary
- [ ] Step 5: Verify citations
```

**Step 1: Read all source documents**

Review each document in the `sources/` directory. Note the main arguments and supporting evidence.

**Step 2: Identify key themes**

Look for patterns across sources. What themes appear repeatedly? Where do sources agree or disagree?

**Step 3: Cross-reference claims**

For each major claim, verify it appears in the source material. Note which source supports each point.

**Step 4: Create structured summary**

Organize findings by theme. Include:
- Main claim
- Supporting evidence from sources
- Conflicting viewpoints (if any)

**Step 5: Verify citations**

Check that every claim references the correct source document. 
If citations are incomplete, return to Step 3.
~~~

### Conditional Workflows

~~~ 
Document modification

1. Determine the modification type:

   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow:
   - Use docx-js library
   - Build document from scratch
   - Export to .docx format

3. Editing workflow:
   - Unpack existing document
   - Modify XML directly
   - Validate after each change
   - Repack when complete
~~~

### Validation Loops

~~~
Content review process

1. Draft your content following the guidelines in STYLE_GUIDE.md
2. Review against the checklist:
   - Check terminology consistency
   - Verify examples follow the standard format
   - Confirm all required sections are present
3. If issues found:
   - Note each issue with specific section reference
   - Revise the content
   - Review the checklist again
4. Only proceed when all requirements are met
5. Finalize and save the document
~~~

