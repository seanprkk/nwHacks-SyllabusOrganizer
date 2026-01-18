import requests
import json

def import_to_notion(markdown_content, notion_api_key):
    """
    Import markdown content to Notion as a new page
    
    Args:
        markdown_content: The populated markdown template
        notion_api_key: User's Notion integration token
    
    Returns:
        tuple: (success, page_url, error_message)
    """
    try:
        # Create a new page in Notion
        headers = {
            "Authorization": f"Bearer {notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # First, get the user's available pages to find a parent
        search_url = "https://api.notion.com/v1/search"
        search_data = {
            "filter": {"property": "object", "value": "page"}
        }
        
        search_response = requests.post(search_url, headers=headers, json=search_data)
        
        if search_response.status_code != 200:
            return False, None, f"Failed to connect to Notion: {search_response.text}"
        
        # Parse markdown into Notion blocks (simplified)
        blocks = markdown_to_notion_blocks(markdown_content)
        
        # Get first available parent or use None for workspace root
        results = search_response.json().get('results', [])
        parent_id = results[0]['id'] if results else None
        
        # Create the page
        create_url = "https://api.notion.com/v1/pages"
        page_data = {
            "parent": {"page_id": parent_id} if parent_id else {"type": "workspace", "workspace": True},
            "properties": {
                "title": {
                    "title": [{"text": {"content": "Course Syllabus"}}]
                }
            },
            "children": blocks[:100]  # Notion limit
        }
        
        create_response = requests.post(create_url, headers=headers, json=page_data)
        
        if create_response.status_code != 200:
            return False, None, f"Failed to create page: {create_response.text}"
        
        page_url = create_response.json().get('url')
        return True, page_url, None
        
    except Exception as e:
        return False, None, str(e)
def markdown_to_notion_blocks(markdown_content):
    """Convert markdown to Notion blocks with proper table support"""
    blocks = []
    lines = markdown_content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Headers
        if line.startswith('# '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"text": {"content": line[2:]}}]}
            })
            i += 1
        elif line.startswith('## '):  # ← ADDED THIS
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": line[3:]}}]}
            })
            i += 1
        elif line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": line[4:]}}]}
            })
            i += 1
        # Detect table start
        elif line.startswith('|') and i + 1 < len(lines) and lines[i + 1].strip().startswith('| ---'):
            # Parse the entire table
            table_block = parse_markdown_table(lines, i)
            if table_block:
                blocks.append(table_block)
                # Skip past the table
                i += count_table_rows(lines, i)
            else:
                i += 1
        # Dividers
        elif line == '---':
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
            i += 1
        # Regular text
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": line}}]}
            })
            i += 1
    
    return blocks


def parse_markdown_table(lines, start_idx):
    """Parse a markdown table into a Notion table block"""
    try:
        # Get header row
        header_line = lines[start_idx].strip()
        if not header_line.startswith('|'):
            return None
        
        headers = [cell.strip() for cell in header_line.split('|')[1:-1]]
        num_cols = len(headers)
        
        # Skip separator line
        if start_idx + 1 >= len(lines):
            return None
        
        # Get data rows
        data_rows = []
        idx = start_idx + 2  # Skip header and separator
        
        while idx < len(lines):
            line = lines[idx].strip()
            if not line.startswith('|'):
                break
            
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if len(cells) == num_cols:
                data_rows.append(cells)
            idx += 1
        
        # Build Notion table block
        table_width = num_cols
        table_children = []
        
        # Add header row FIRST (as a single table_row with all headers)
        header_cells = []
        for header in headers:
            header_cells.append([{"text": {"content": header}}])
        
        table_children.append({
            "object": "block",
            "type": "table_row",
            "table_row": {"cells": header_cells}
        })
        
        # Add data rows
        for row in data_rows:
            cells = []
            for cell in row:
                cells.append([{"text": {"content": cell}}])
            
            table_children.append({
                "object": "block",
                "type": "table_row",
                "table_row": {"cells": cells}
            })
        
        return {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": table_width,
                "has_column_header": True,
                "has_row_header": False,
                "children": table_children
            }
        }
        
    except Exception as e:
        print(f"Error parsing table: {e}")
        return None


def count_table_rows(lines, start_idx):
    """Count how many lines the table spans"""
    count = 2  # Header + separator
    idx = start_idx + 2
    
    while idx < len(lines) and lines[idx].strip().startswith('|'):
        count += 1
        idx += 1
    
    return count