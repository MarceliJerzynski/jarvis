#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.parse
import ssl
import base64
import re

def jira_wiki_to_markdown(text):
    if not text:
        return ""
        
    lines = text.split("\n")
    converted_lines = []
    in_code_block = False
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        
        # 1. Handle code/noformat blocks
        code_match = re.match(r"^\{(code|noformat)(?::(\w+))?\}", stripped)
        if code_match:
            if in_code_block:
                converted_lines.append("```")
                in_code_block = False
            else:
                lang = code_match.group(2) or ""
                converted_lines.append(f"```{lang}")
                in_code_block = True
            continue
            
        if in_code_block:
            converted_lines.append(line)
            continue
            
        # 2. Handle Tables
        is_header_row = stripped.startswith("||") and stripped.endswith("||")
        is_data_row = stripped.startswith("|") and stripped.endswith("|") and not is_header_row
        
        if is_header_row:
            # Table header: e.g. ||header1||header2||
            cols = [col.strip() for col in stripped.split("||")[1:-1]]
            formatted_cols = []
            for col in cols:
                # convert wiki *bold* to markdown **bold**
                col_formatted = re.sub(r"\*([^*]+)\*", r"**\1**", col)
                formatted_cols.append(col_formatted)
                
            md_header = "| " + " | ".join(formatted_cols) + " |"
            converted_lines.append(md_header)
            
            # Generate divider line
            md_divider = "| " + " | ".join(["---"] * len(cols)) + " |"
            converted_lines.append(md_divider)
            in_table = True
            continue
            
        elif is_data_row:
            # Table row: e.g. |cell1|cell2|
            cols = [col.strip() for col in stripped.split("|")[1:-1]]
            formatted_cols = []
            for col in cols:
                # convert wiki *bold* to markdown **bold**
                col_formatted = re.sub(r"\*([^*]+)\*", r"**\1**", col)
                formatted_cols.append(col_formatted)
            md_row = "| " + " | ".join(formatted_cols) + " |"
            converted_lines.append(md_row)
            in_table = True
            continue
        else:
            if in_table:
                # Add a blank line to terminate the table in Markdown
                converted_lines.append("")
                in_table = False
                
        # 3. Handle Headers
        header_match = re.match(r"^h([1-6])\.\s+(.*)", stripped)
        if header_match:
            level = int(header_match.group(1))
            header_text = header_match.group(2)
            converted_lines.append(f"{'#' * level} {header_text}")
            continue
            
        # 4. Handle Lists
        # Bullet lists: * item, ** subitem, *** subsubitem
        list_match = re.match(r"^(\*+)\s+(.*)", stripped)
        if list_match:
            depth = len(list_match.group(1))
            list_text = list_match.group(2)
            indent = "  " * (depth - 1)
            list_text = re.sub(r"\*([^*]+)\*", r"**\1**", list_text)
            converted_lines.append(f"{indent}* {list_text}")
            continue
            
        # Numbered lists: # item, ## subitem
        num_list_match = re.match(r"^(#+)\s+(.*)", stripped)
        if num_list_match:
            depth = len(num_list_match.group(1))
            list_text = num_list_match.group(2)
            indent = "  " * (depth - 1)
            list_text = re.sub(r"\*([^*]+)\*", r"**\1**", list_text)
            converted_lines.append(f"{indent}1. {list_text}")
            continue
            
        # 5. Inline formatting (bold, monospace)
        # Bold: *text* -> **text**
        processed_line = re.sub(r"\*([^*]+)\*", r"**\1**", line)
        # Monospace: {{text}} -> `text`
        processed_line = re.sub(r"\{\{([^}]+)\}\}", r"`\1`", processed_line)
        
        converted_lines.append(processed_line)
        
    return "\n".join(converted_lines)

def adf_to_markdown(node):
    if not node:
        return ""
    if isinstance(node, str):
        return node
    
    node_type = node.get("type")
    
    if node_type == "text":
        text = node.get("text", "")
        marks = node.get("marks", [])
        for mark in marks:
            mtype = mark.get("type")
            if mtype == "strong":
                text = f"**{text}**"
            elif mtype == "em":
                text = f"*{text}*"
            elif mtype == "strike":
                text = f"~~{text}~~"
            elif mtype == "code":
                text = f"`{text}`"
            elif mtype == "link":
                href = mark.get("attrs", {}).get("href", "")
                text = f"[{text}]({href})"
        return text
        
    elif node_type == "paragraph":
        content_list = node.get("content", [])
        text = "".join(adf_to_markdown(c) for c in content_list)
        return text + "\n\n"
        
    elif node_type == "heading":
        level = node.get("attrs", {}).get("level", 1)
        content_list = node.get("content", [])
        text = "".join(adf_to_markdown(c) for c in content_list)
        return f"{'#' * level} {text}\n\n"
        
    elif node_type == "bulletList":
        content_list = node.get("content", [])
        text = "".join(adf_to_markdown(c) for c in content_list)
        return text
        
    elif node_type == "orderedList":
        content_list = node.get("content", [])
        text = "".join(adf_to_markdown(c) for c in content_list)
        return text
        
    elif node_type == "listItem":
        content_list = node.get("content", [])
        text = "".join(adf_to_markdown(c) for c in content_list)
        indented_text = text.strip().replace("\n", "\n  ")
        return f"- {indented_text}\n"
        
    elif node_type == "codeBlock":
        content_list = node.get("content", [])
        text = "".join(c.get("text", "") for c in content_list)
        lang = node.get("attrs", {}).get("language", "")
        return f"```{lang}\n{text}\n```\n\n"
        
    elif node_type == "blockquote":
        content_list = node.get("content", [])
        text = "".join(adf_to_markdown(c) for c in content_list)
        return f"> {text}\n\n"
        
    elif node_type == "hardBreak":
        return "\n"
        
    elif node_type == "rule":
        return "---\n\n"
        
    if "content" in node:
        content_list = node.get("content", [])
        return "".join(adf_to_markdown(c) for c in content_list)
        
    return ""

def main():
    if len(sys.argv) < 2:
        print("Usage: jira_fetch.py <JIRA-ID>", file=sys.stderr)
        sys.exit(1)
        
    jira_id = sys.argv[1].upper().strip()
    
    config_path = "/home/node-user/.gemini/tmp/jarvis-2/memory/jira_config.json"
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found at {config_path}", file=sys.stderr)
        sys.exit(1)
        
    with open(config_path, "r") as f:
        try:
            config = json.load(f)
        except Exception as json_err:
            print(f"Error parsing JSON from {config_path}: {json_err}", file=sys.stderr)
            sys.exit(1)
        
    jira_url = config.get("jira_url")
    cookie = config.get("cookie")
    jira_user = config.get("jira_user")
    jira_token = config.get("jira_token")
    
    if not jira_url:
        print("Error: Please set your jira_url in jira_config.json", file=sys.stderr)
        sys.exit(1)
        
    # Standardize URL
    if not jira_url.startswith("http"):
        jira_url = "https://" + jira_url
        
    api_url = urllib.parse.urljoin(jira_url, f"/rest/api/2/issue/{jira_id}")
    req = urllib.request.Request(api_url)
    req.add_header("accept", "application/json")
    
    if cookie:
        req.add_header("Cookie", cookie)
    elif jira_user and jira_token:
        auth_str = f"{jira_user}:{jira_token}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        req.add_header("Authorization", f"Basic {b64_auth}")
    else:
        print("Error: No authentication method found in jira_config.json", file=sys.stderr)
        sys.exit(1)
        
    ssl_context = ssl._create_unverified_context()
    
    print(f"Fetching Jira ticket {jira_id} from {jira_url}...")
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"Error: Jira API request failed with status {e.code}", file=sys.stderr)
        print(f"Message: {err_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error connecting to Jira API: {e}", file=sys.stderr)
        sys.exit(1)
        
    # Extract fields
    fields = data.get("fields", {})
    summary = fields.get("summary", "No Title")
    issue_type = fields.get("issuetype", {}).get("name", "Unknown")
    status = fields.get("status", {}).get("name", "Unknown")
    priority = fields.get("priority", {}).get("name", "None") if fields.get("priority") else "None"
    assignee = fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned"
    
    raw_desc = fields.get("description", "")
    
    # Render description
    if isinstance(raw_desc, dict):
        description = adf_to_markdown(raw_desc).strip()
    else:
        description = jira_wiki_to_markdown(str(raw_desc)).strip() if raw_desc else "No description provided."
        
    # Format as a beautifully structured Markdown document
    output_md = f"""# {jira_id}: {summary}

- **Type:** {issue_type}
- **Status:** {status}
- **Priority:** {priority}
- **Assignee:** {assignee}
- **Jira Link:** {urllib.parse.urljoin(jira_url, f'/browse/{jira_id}')}

---

## Description

{description}
"""

    # Save to the jiras folder
    output_dir = "/workspace/jarvis/jiras"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file_path = os.path.join(output_dir, f"{jira_id}-imported.md")
    with open(output_file_path, "w", encoding="utf-8") as out_f:
        out_f.write(output_md)
        
    print(f"✅ SUCCESS: Jira ticket {jira_id} fetched successfully!")
    print(f"Saved to: {output_file_path}")

if __name__ == "__main__":
    main()
