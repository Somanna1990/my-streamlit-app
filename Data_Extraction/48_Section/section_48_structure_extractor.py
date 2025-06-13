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
    
    # Remove any trailing whitespace
    text = text.strip()
    
    return text

def extract_structure(pdf_path, output_path):
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
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"Structure data saved to {output_path}")
    return result

if __name__ == "__main__":
    # Define paths
    base_dir = Path(__file__).parent.parent
    
    # Process Section 48 document
    input_48 = base_dir / "Input" / "Section-48" / "central-bank-supervision-and-enforcement-act-2013-section-48 (1).pdf"
    output_48 = base_dir / "output" / "48_structure.json"
    
    print(f"Extracting structure from: {input_48}")
    print(f"Output will be saved to: {output_48}")
    
    extract_structure(input_48, output_48)
