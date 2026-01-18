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
    """Convert markdown to Notion blocks (simplified version)"""
    blocks = []
    lines = markdown_content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Headers
        if line.startswith('# '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"text": {"content": line[2:]}}]}
            })
        elif line.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": line[3:]}}]}
            })
        # Table rows (simplified - Notion tables are complex)
        elif line.startswith('|') and not line.startswith('| ---'):
            # Convert table rows to bullet points for simplicity
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if cells:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"text": {"content": " | ".join(cells)}}]}
                })
        # Regular text
        elif line and not line.startswith('| ---'):
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": line}}]}
            })
    
    return blocks