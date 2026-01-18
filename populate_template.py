# populate_template.py - Populate markdown template with JSON data
import json
import os
from datetime import datetime

def format_datetime(dt_string):
    """Convert ISO datetime to readable format"""
    if not dt_string:
        return "TBA"
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %I:%M %p")
    except:
        return dt_string

def format_meeting_time(start_time, end_time):
    """Format meeting time range"""
    if not start_time or not end_time:
        return "TBA"
    try:
        # Handle time strings like "15:30:00"
        start = datetime.strptime(start_time, "%H:%M:%S").strftime("%I:%M %p")
        end = datetime.strptime(end_time, "%H:%M:%S").strftime("%I:%M %p")
        return f"{start} - {end}"
    except:
        return f"{start_time} - {end_time}"

def populate_markdown_template(json_file_path, template_path, output_path):
    """
    Populate markdown template with data from JSON
    
    Args:
        json_file_path: Path to the JSON file with course data
        template_path: Path to the markdown template file
        output_path: Path where the populated markdown will be saved
    """
    
    # Read JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    course_info = data.get('course-info', {})
    
    # Extract course information
    course_code = course_info.get('code', 'N/A')
    course_title = course_info.get('title', 'N/A')
    
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Replace course header
    result = template.replace('<placeholder-course-code>', course_code)
    result = result.replace('<placeholder-course-name>', course_title)
    
    # Populate Class Times (meetings)
    meetings = course_info.get('meetings', [])
    if meetings:
        meeting_rows = []
        for meeting in meetings:
            meeting_type = meeting.get('type') or 'N/A'
            lead = meeting.get('lead') or 'N/A'
            day = meeting.get('day')
            day = day.capitalize() if day else 'N/A'
            time_range = format_meeting_time(meeting.get('start_time'), meeting.get('end_time'))
            location = meeting.get('location') or 'N/A'
            
            meeting_rows.append(
                f"| {meeting_type} | {lead} | {day} | {time_range} | {location} |"
            )
        
        # Replace the placeholder row with all meeting rows
        meeting_table_row = "| <placeholder-class-time-type> | <placeholder-class-time-lead> | <placeholder-class-time-date> | <placeholder-class-time-time> | <placeholder-class-time-location> |"
        result = result.replace(meeting_table_row, '\n'.join(meeting_rows))
    
    # Populate Assignments (homework)
    homework = course_info.get('homework', [])
    if homework:
        assignment_rows = []
        for hw in homework:
            name = hw.get('name') or 'N/A'
            due_date = format_datetime(hw.get('due-date', ''))
            link = hw.get('links') or 'N/A'
            
            assignment_rows.append(
                f"| {name} | {due_date} | {link} |"
            )
        
        # Replace the placeholder row with all assignment rows
        assignment_table_row = "| <placeholder-assignment-name> | <placeholder-assignment-due-date> | <placeholder-assignment-due-link> |"
        result = result.replace(assignment_table_row, '\n'.join(assignment_rows))
    
    # Populate Important Dates
    important_dates = course_info.get('Important-dates', [])
    if important_dates:
        date_rows = []
        for date_entry in important_dates:
            name = date_entry.get('name') or 'N/A'
            # Try 'date' field first, then fall back to 'day'
            date_val = date_entry.get('date') or date_entry.get('day')
            # Format the date if it's in ISO format
            if date_val and 'T' in str(date_val):
                date_val = format_datetime(date_val)
            elif date_val:
                date_val = str(date_val)
            else:
                date_val = 'N/A'
            # Try 'location' field first, then fall back to 'notes'
            location = date_entry.get('location') or date_entry.get('notes') or 'N/A'
            
            date_rows.append(
                f"| {name} | {date_val} | {location} |"
            )
        
        # Replace the placeholder row
        date_table_row = "| <placeholder-important-dates-name> | <placeholder-important-dates-date> | <placeholder-important-dates-location> |"
        result = result.replace(date_table_row, '\n'.join(date_rows))
    
    # Populate Contacts
    contacts = course_info.get('contacts', [])
    if contacts:
        contact_rows = []
        for contact in contacts:
            name = contact.get('name') or 'N/A'
            position = contact.get('position') or 'N/A'
            email = contact.get('email') or 'N/A'
            
            contact_rows.append(
                f"| {name} | {position} | {email} |"
            )
        
        # Replace the placeholder row
        contact_table_row = "| <placeholder-contacts-name> | <placeholder-contacts-position> | <placeholder-contacts-email> |"
        result = result.replace(contact_table_row, '\n'.join(contact_rows))
    
    # Populate Resources
    resources = course_info.get('resources', [])
    if resources:
        resource_rows = []
        for resource in resources:
            name = resource.get('name') or 'N/A'
            link = resource.get('link') or 'N/A'
            
            resource_rows.append(
                f"| {name} | {link} |"
            )
        
        # Replace the placeholder row
        resource_table_row = "| <placeholder-link-name> | <placeholder-link-link> |"
        result = result.replace(resource_table_row, '\n'.join(resource_rows))
    
    # Save the populated markdown
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"✓ Markdown populated successfully!")
    print(f"  Output saved to: {output_path}")
    return result

if __name__ == '__main__':
    # Example usage
    json_file = 'data/cpsc330-syllabus-info.json'
    template_file = 'notion_templates/modern-template.md'  # Your template file
    output_file = 'output/populated-syllabus.md'
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    if os.path.exists(json_file) and os.path.exists(template_file):
        populate_markdown_template(json_file, template_file, output_file)
    else:
        print("Error: JSON or template file not found")
        print(f"  Looking for JSON at: {json_file}")
        print(f"  Looking for template at: {template_file}")