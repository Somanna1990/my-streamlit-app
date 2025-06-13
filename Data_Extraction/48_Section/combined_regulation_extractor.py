import os
import re
import json
import PyPDF2
from pathlib import Path

def clean_text(text):
    """Clean text by replacing Unicode characters and removing page numbers"""
    # Replace Unicode dashes with regular dashes
    text = text.replace('–', '-')
    text = text.replace('—', '-')
    
    # Replace Unicode apostrophes and quotes
    text = text.replace(''', "'")
    text = text.replace(''', "'")
    text = text.replace('\u2019', "'")
    text = text.replace('\u201C', '"')
    text = text.replace('\u201D', '"')
    
    # Remove page numbers like "[80] 3"
    text = re.sub(r'\[\d+\]\s+\d+', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove any trailing whitespace
    text = text.strip()
    
    return text

def extract_structure(pdf_path):
    """Extract just the structure from a Section 48 document without the text content"""
    
    # Extract text from PDF
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    
    # Find where the actual regulations end (after regulation 420)
    end_match = re.search(r"420\.[^\n]*Failure to comply with these Regulations[^\n]*", text)
    if end_match:
        # Truncate the text at this point to avoid picking up duplicate content
        text = text[:end_match.end() + 1000]  # Add a buffer to include regulation 420's text
    
    # Source name is fixed for this document
    source_name = "CENTRAL BANK (SUPERVISION AND ENFORCEMENT) ACT 2013 (SECTION 48) (CONSUMER PROTECTION) REGULATIONS 2025"
    
    # Initialize variables to store current context
    current_part_num = ""
    current_part_name = ""
    current_chapter_num = ""
    current_chapter_name = ""
    
    # Process the text line by line
    lines = text.split('\n')
    
    # The result will be a list of regulation entries (structure only)
    result = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for part
        part_match = re.match(r"PART (\d+)[^\n]*", line, re.IGNORECASE)
        if part_match and i+1 < len(lines):
            current_part_num = part_match.group(1)
            current_part_name = lines[i+1].strip()
            
            # Clean up part name
            current_part_name = clean_text(current_part_name)
            
            i += 2
            continue
        
        # Check for chapter
        chapter_match = re.match(r"Chapter (\d+)[^\n]*", line)
        if chapter_match and i+1 < len(lines):
            current_chapter_num = f"Chapter {chapter_match.group(1)}"
            current_chapter_name = lines[i+1].strip()
            
            # Clean up chapter name
            current_chapter_name = clean_text(current_chapter_name)
            
            i += 2
            continue
        
        # Check for regulation number and title
        regulation_match = re.match(r"^(\d+)\.\s*(.*)$", line)
        if regulation_match:
            regulation_num = int(regulation_match.group(1))
            regulation_title = regulation_match.group(2)
            
            # Check if the title continues on the next line(s)
            j = i + 1
            while j < len(lines) and not re.match(r"^\d+\.\s*", lines[j].strip()) and \
                  not re.match(r"PART \d+", lines[j].strip(), re.IGNORECASE) and \
                  not re.match(r"Chapter \d+", lines[j].strip()) and \
                  not lines[j].strip() == "" and \
                  not re.match(r"^\([a-z]\)", lines[j].strip()):
                # This looks like a continuation of the title
                regulation_title += " " + lines[j].strip()
                j += 1
            
            # Clean up the regulation title
            regulation_title = clean_text(regulation_title)
            
            # Create the structure entry
            entry = {
                "Source Name": source_name,
                "Part Number": current_part_num,
                "Part Name": current_part_name,
                "Chapter Number": current_chapter_num,
                "Chapter Name": current_chapter_name,
                "Regulation Number": regulation_num,
                "Regulation Title": regulation_title
            }
            
            result.append(entry)
            
            # Skip the lines we've already processed
            if j > i + 1:
                i = j - 1  # -1 because the loop will increment i
        
        i += 1
    
    return result

def extract_regulation_text(pdf_path, start_page=23):
    """Extract regulation text from PDF"""
    
    # Extract text from PDF, starting from the specified page
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        full_text = ""
        
        # Start from page 23 (0-indexed as 22) as mentioned in the requirements
        for i in range(start_page - 1, len(reader.pages)):
            page_text = reader.pages[i].extract_text()
            if page_text:
                full_text += page_text + "\n"
    
    # Find all regulation numbers (e.g., "1.", "2.", etc.)
    regulation_pattern = re.compile(r'(?:^|\n)(\d+)\.\s')
    matches = list(regulation_pattern.finditer(full_text))
    
    # Filter matches to include only valid regulation numbers (1-420 as mentioned)
    valid_matches = [m for m in matches if 1 <= int(m.group(1)) <= 420]
    
    regulations_text = {}
    
    # Process each regulation
    for i, match in enumerate(valid_matches):
        reg_num = int(match.group(1))
        start_pos = match.start()  # Start from the beginning of the match
        
        # Determine end position (start of next regulation or end of document)
        end_pos = len(full_text)
        if i + 1 < len(valid_matches):
            end_pos = valid_matches[i + 1].start()
        else:
            # For the last regulation (420), we need to make sure it doesn't include schedules
            schedule_match = re.search(r'SCHEDULE\s+\d+', full_text[start_pos:])
            if schedule_match:
                end_pos = start_pos + schedule_match.start()
        
        # Extract the text for this regulation
        reg_text = full_text[start_pos:end_pos].strip()
        
        # Clean the text
        reg_text = clean_text(reg_text)
        regulations_text[reg_num] = reg_text
    
    return regulations_text

def clean_regulation_text(reg_text, next_reg_title=None, reg_num=None, next_reg_num=None):
    """Clean regulation text by removing next regulation title that appears at the end"""
    # First, check for exact title match at the end
    if next_reg_title and reg_text.endswith(next_reg_title):
        # Remove the next regulation's title if it appears at the end of this regulation's text
        reg_text = reg_text[:-len(next_reg_title)].strip()
    
    # Look for common patterns that indicate a title at the end
    # Titles are often capitalized words or phrases
    title_patterns = [
        # Multiple capitalized words at the end that look like a title
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,7})$',
        
        # Common title phrases
        r'((?:Restricted|Application|Scope|Interpretation|Citation|Warning|Prior|Where|Information|Disclosure|Advertising|Marketing|Statements|Guarantees|Lifetime|Mortgage|Credit|Provision)\s+(?:of|and|where|to|on|for|about|regarding|concerning|by|with)\s+[\w\s]+)$',
        
        # Page numbers and section markers that might appear at the end
        r'\d+\s+\[\d+\]\s*$',
        
        # Look for the next regulation number pattern at the end
        r'\b(?:' + str(next_reg_num) + r')\.\s*$' if next_reg_num else r'',
    ]
    
    # Filter out empty patterns
    title_patterns = [p for p in title_patterns if p]
    
    for pattern in title_patterns:
        title_match = re.search(pattern, reg_text)
        if title_match:
            potential_title = title_match.group(1) if title_match.groups() else title_match.group(0)
            # Only remove if it looks like a title (not too long, contains specific words)
            title_words = ['application', 'scope', 'interpretation', 'citation', 'restricted', 'compliance', 
                          'warning', 'prior', 'where', 'information', 'disclosure', 'advertising', 'marketing',
                          'statements', 'guarantees', 'lifetime', 'mortgage', 'credit', 'provision']
            
            if (len(potential_title.split()) <= 10 and 
                any(word in potential_title.lower() for word in title_words)):
                reg_text = reg_text[:title_match.start()].strip()
                break
    
    # Handle special cases like warnings and formatted text
    # Look for page numbers and section markers that might break the text
    page_markers = re.finditer(r'(\d+)\s+\[(\d+)\]', reg_text)
    for marker in page_markers:
        # Check if this is in the middle of a paragraph or list
        if marker.start() > 0 and marker.end() < len(reg_text) - 1:
            # Check if it's not at the beginning of a line or after a period
            prev_char = reg_text[marker.start()-1]
            next_char = reg_text[marker.end()] if marker.end() < len(reg_text) else ''
            
            if prev_char not in ['.', '\n', '\r'] and next_char not in ['.', '\n', '\r']:
                # This is likely a page marker in the middle of text - remove it
                reg_text = reg_text[:marker.start()] + ' ' + reg_text[marker.end():]
    
    # Clean up any double spaces
    reg_text = re.sub(r'\s+', ' ', reg_text)
    
    return reg_text.strip()

def combine_structure_and_text(structure_data, text_data, output_path):
    """Combine structure and text data, ensuring regulation text starts with the regulation number"""
    combined_result = []
    
    # Create a dictionary of regulation titles for easy lookup
    reg_titles = {entry["Regulation Number"]: entry["Regulation Title"] for entry in structure_data}
    
    # Sort structure data by regulation number to process in order
    sorted_structure = sorted(structure_data, key=lambda x: x["Regulation Number"])
    
    for i, entry in enumerate(sorted_structure):
        reg_num = entry["Regulation Number"]
        reg_title = entry["Regulation Title"]
        
        if reg_num in text_data:
            # Get the original text
            original_text = text_data[reg_num]
            
            # Check if the next regulation's title appears at the end of this regulation's text
            next_reg_title = None
            next_reg_num = None
            if i < len(sorted_structure) - 1:
                next_reg_title = sorted_structure[i + 1]["Regulation Title"]
                next_reg_num = sorted_structure[i + 1]["Regulation Number"]
            
            # Clean the regulation text to remove any title at the end
            cleaned_text = clean_regulation_text(original_text, next_reg_title, reg_num, next_reg_num)
            
            # Ensure the text starts with the regulation number
            # First check if it already starts with the regulation number
            if not cleaned_text.startswith(f"{reg_num}."):
                # If not, add the regulation number at the beginning
                reg_text = f"{reg_num}. {cleaned_text}"
            else:
                reg_text = cleaned_text
            
            # Create the combined entry
            combined_entry = {
                "Source Name": entry["Source Name"],
                "Part Number": entry["Part Number"],
                "Part Name": entry["Part Name"],
                "Chapter Number": entry["Chapter Number"],
                "Chapter Name": entry["Chapter Name"],
                "Regulation Number": reg_num,
                "Regulation Title": reg_title,
                "Regulation Text": reg_text
            }
            
            combined_result.append(combined_entry)
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_result, f, indent=2, ensure_ascii=False)
    
    print(f"Combined structure and text data saved to {output_path}")
    return combined_result

def main():
    # Define paths
    base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
    
    # Process Section 48 document
    # Check all possible file paths
    possible_paths = [
        base_dir / "Input" / "Section-48" / r"central-bank-supervision-and-enforcement-act-2013-section-48 (1).pdf",
        base_dir / "Input" / "Section-48" / r"central-bank-supervision-and-enforcement-act-2013-section-48(1).pdf",
        base_dir / "Input" / "Section-48" / r"central-bank-supervision-and-enforcement-act-2013-section-48.pdf"
    ]
    
    input_48 = None
    for path in possible_paths:
        if path.exists():
            input_48 = path
            break
    
    if not input_48:
        print("Error: Could not find the PDF file. Please check the path.")
        print("Searching in: {}".format(base_dir / "Input" / "Section-48"))
        print("Available files:")
        try:
            for file in (base_dir / "Input" / "Section-48").glob("*.pdf"):
                print(f"  - {file.name}")
            # If no PDF files found
            if not list((base_dir / "Input" / "Section-48").glob("*.pdf")):
                print("  No PDF files found in this directory.")
        except Exception as e:
            print(f"Error listing directory: {e}")
        return
    
    output_48 = base_dir / "output" / "section_48_combined.json"
    
    # Convert to string to avoid path issues
    input_path = str(input_48)
    output_path = str(output_48)
    
    print(f"Processing document: {input_path}")
    
    # Step 1: Extract structure (titles)
    print("Step 1: Extracting structure...")
    structure_data = extract_structure(input_path)
    print(f"Extracted structure for {len(structure_data)} regulations")
    
    # Step 2: Extract regulation text
    print("Step 2: Extracting regulation text...")
    text_data = extract_regulation_text(input_path)
    print(f"Extracted text for {len(text_data)} regulations")
    
    # Step 3: Combine structure and text
    print("Step 3: Combining structure and text...")
    combine_structure_and_text(structure_data, text_data, output_path)

if __name__ == "__main__":
    main()
