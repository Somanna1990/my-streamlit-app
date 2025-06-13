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

def extract_regulations(pdf_path, output_path, start_page=23):
    """Extract regulations from PDF - find each regulation number and extract text until the next one"""
    
    # Extract text from PDF, starting from the specified page
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        full_text = ""
        
        # Start from page 23 (0-indexed as 22) as mentioned in the requirements
        for i in range(start_page - 1, len(reader.pages)):
            page_text = reader.pages[i].extract_text()
            if page_text:
                # Add page marker for debugging if needed
                # full_text += f"\n[PAGE {i+1}]\n" + page_text + "\n"
                full_text += page_text + "\n"
    
    # Find all regulation numbers (e.g., "1.", "2.", etc.) - be more specific to avoid false matches
    # Look for numbers at the start of a line or after a newline, followed by a period and space
    regulation_pattern = re.compile(r'(?:^|\n)(\d+)\.\s')
    matches = list(regulation_pattern.finditer(full_text))
    
    # Filter matches to include only valid regulation numbers (1-420 as mentioned)
    valid_matches = [m for m in matches if 1 <= int(m.group(1)) <= 420]
    
    regulations = []
    
    # Process each regulation
    for i, match in enumerate(valid_matches):
        reg_num = int(match.group(1))
        start_pos = match.start(1)  # Start from the number itself
        
        # Determine end position (start of next regulation or end of document)
        end_pos = len(full_text)
        if i + 1 < len(valid_matches):
            end_pos = valid_matches[i + 1].start(1)
        
        # Extract the text for this regulation
        reg_text = full_text[start_pos:end_pos].strip()
        
        # Clean the text
        reg_text = clean_text(reg_text)
        
        # Add to results
        regulations.append({
            "Regulation Number": reg_num,
            "Regulation Text": reg_text
        })
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(regulations, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted {len(regulations)} regulations to {output_path}")
    return regulations

def main():
    # Define paths
    base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
    
    # Process Section 48 document
    input_48 = base_dir / "Input" / "Section-48" / "central-bank-supervision-and-enforcement-act-2013-section-48 (1).pdf"
    output_48 = base_dir / "output" / "section_48_regulations.json"
    
    # Convert to string to avoid path issues
    input_path = str(input_48)
    output_path = str(output_48)
    
    print(f"Extracting regulations from: {input_path}")
    print(f"Output will be saved to: {output_path}")
    
    extract_regulations(input_path, output_path)

if __name__ == "__main__":
    main()
