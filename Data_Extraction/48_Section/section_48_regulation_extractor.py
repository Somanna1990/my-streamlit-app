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

def extract_regulation_text(text, reg_num, next_reg_num=None):
    """Extract the text of a regulation"""
    # Pattern to find the regulation number and capture everything until the next regulation
    # We need to be careful with the regex to properly capture all text
    if next_reg_num:
        pattern = fr'\b{reg_num}\.\s+(.*?)\b{next_reg_num}\.'
    else:
        pattern = fr'\b{reg_num}\.\s+(.*)'
        
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        reg_text = match.group(1).strip()
        # Clean the text
        reg_text = clean_text(reg_text)
        return reg_text
    
    # If the regex didn't work, try a simpler approach
    lines = text.split('\n')
    found_start = False
    reg_text_lines = []
    
    for line in lines:
        if not found_start:
            if re.match(fr'^\s*{reg_num}\.\s+', line):
                # Found the start of our regulation
                found_start = True
                # Extract text after the regulation number
                content = re.sub(fr'^\s*{reg_num}\.\s+', '', line)
                if content.strip():
                    reg_text_lines.append(content.strip())
        elif next_reg_num and re.match(fr'^\s*{next_reg_num}\.\s+', line):
            # Found the next regulation, stop collecting
            break
        elif not next_reg_num and re.match(r'^\s*\d+\.\s+', line) and not re.match(fr'^\s*{reg_num}\.\s+', line):
            # Found another regulation, stop collecting
            break
        else:
            # Continue collecting text for the current regulation
            reg_text_lines.append(line.strip())
    
    if reg_text_lines:
        combined_text = ' '.join(reg_text_lines)
        return clean_text(combined_text)
    
    return ""

def extract_regulations_and_structure(pdf_path, output_path):
    """Extract both structure and text content from a Section 48 document"""
    
    # Extract text from PDF
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    
    # Source name is fixed for this document
    source_name = "CENTRAL BANK (SUPERVISION AND ENFORCEMENT) ACT 2013 (SECTION 48) (CONSUMER PROTECTION) REGULATIONS 2025"
    
    # Initialize variables to store current context
    current_part_num = ""
    current_part_name = ""
    current_chapter_num = ""
    current_chapter_name = ""
    
    # Process the text line by line
    lines = text.split('\n')
    
    # The result will be a list of regulation entries with both structure and text
    result = []
    
    # First pass: identify parts, chapters, and regulations directly
    i = 0
    regulations = []
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for part
        part_match = re.match(r"PART (\d+)[^\n]*", line, re.IGNORECASE)
        if part_match and i+1 < len(lines):
            current_part_num = part_match.group(1)
            current_part_name = lines[i+1].strip()
            current_part_name = clean_text(current_part_name)
            i += 2
            continue
        
        # Check for chapter
        chapter_match = re.match(r"Chapter (\d+)[^\n]*", line)
        if chapter_match and i+1 < len(lines):
            current_chapter_num = f"Chapter {chapter_match.group(1)}"
            current_chapter_name = lines[i+1].strip()
            current_chapter_name = clean_text(current_chapter_name)
            i += 2
            continue
        
        # Check for regulation number directly in the text
        reg_num_match = re.match(r"^(\d+)\.\s+(.*?)$", line)
        if reg_num_match:
            reg_num = int(reg_num_match.group(1))
            reg_text_start = line  # Start with the line containing the regulation number
            
            # Find the title by looking at previous non-empty line if it doesn't match a pattern
            title = ""
            j = i - 1
            while j >= 0:
                prev_line = lines[j].strip()
                if prev_line and not re.match(r"^\d+\.\s+", prev_line) and \
                   not re.match(r"PART \d+", prev_line, re.IGNORECASE) and \
                   not re.match(r"Chapter \d+", prev_line) and \
                   not re.match(r"^\([a-z]\)", prev_line):
                    title = prev_line
                    break
                j -= 1
            
            # Mark the start position for text extraction
            start_pos = i
            
            # Find where this regulation ends (next regulation or end of document)
            end_pos = len(lines)
            for j in range(i + 1, len(lines)):
                if re.match(r"^\d+\.\s+", lines[j].strip()) or \
                   re.match(r"PART \d+", lines[j].strip(), re.IGNORECASE) or \
                   re.match(r"Chapter \d+", lines[j].strip()):
                    end_pos = j
                    break
            
            # Extract all text for this regulation
            reg_text_lines = lines[start_pos:end_pos]
            reg_text = "\n".join(reg_text_lines)
            
            # Store the regulation with its context
            regulations.append({
                "number": reg_num,
                "title": title,
                "text": reg_text,
                "part_num": current_part_num,
                "part_name": current_part_name,
                "chapter_num": current_chapter_num,
                "chapter_name": current_chapter_name
            })
            
            # Skip to the end of this regulation
            i = end_pos - 1  # -1 because the loop will increment i
        
        i += 1
    
    # Create the result entries from the regulations
    for reg in regulations:
        # Clean the text
        reg_text = clean_text(reg["text"])
        
        # Create the complete entry
        entry = {
            "Source Name": source_name,
            "Part Number": reg["part_num"],
            "Part Name": reg["part_name"],
            "Chapter Number": reg["chapter_num"],
            "Chapter Name": reg["chapter_name"],
            "Regulation Number": reg["number"],
            "Regulation Title": reg["title"],
            "Regulation Text": reg_text
        }
        
        result.append(entry)
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Structure and text data saved to {output_path}")
    return result

def main():
    # Define paths using raw strings to avoid issues with special characters
    base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
    
    # Process Section 48 document with explicit paths
    input_48 = base_dir / "Input" / "Section-48" / "central-bank-supervision-and-enforcement-act-2013-section-48 (1).pdf"
    output_48 = base_dir / "output" / "section_48_regulations.json"
    
    # Convert to string to avoid path issues
    input_path = str(input_48)
    output_path = str(output_48)
    
    print(f"Extracting structure and text from: {input_path}")
    print(f"Output will be saved to: {output_path}")
    
    extract_regulations_and_structure(input_path, output_path)

if __name__ == "__main__":
    main()