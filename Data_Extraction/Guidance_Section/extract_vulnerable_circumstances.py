import os
import fitz  # PyMuPDF
import json
import re
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import io

# Set up paths
BASE_DIR = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
INPUT_DIR = BASE_DIR / "Input" / "Guidance Document"
OUTPUT_DIR = BASE_DIR / "output" / "Guidance"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# PDF file to process
PDF_PATH = str(INPUT_DIR / "guidance-on-protecting-consumers-in-vulnerable-circumstances.pdf")
DOC_NAME = "Guidance on Protecting Consumers in Vulnerable Circumstances"
JSON_OUT = str(OUTPUT_DIR / "guidance-on-protecting-consumers-in-vulnerable-circumstances.json")
TEXT_OUT = str(OUTPUT_DIR / "guidance-on-protecting-consumers-in-vulnerable-circumstances.txt")

# Map regulation numbers to their names for this specific document
REGULATION_NAMES = {
    "1.1": "Background",
    "1.2": "G20/OECD High-Level Principles on Financial Consumer Protection",
    "1.3": "Securing Customers' Interests",
    "1.4": "MiFID and Crowdfunding Services",
    "1.5": "Reasonableness, Proportionality and Appropriate Levels of Care",
    "1.6": "Structure of Guidance",
    "2.1": "Defining Consumers in Vulnerable Circumstances",
    "2.2": "Implementing a Broader Concept of Consumers in Vulnerable Circumstances",
    "2.3": "Implementing Specific Requirements",
    "3.1": "Assisted Decision-Making (Capacity) Act",
    "3.2": "European Accessibility Act",
    "3.3": "Data Protection"
}

# Map section numbers to their names
SECTION_NAMES = {
    "1": "Introduction",
    "2": "Guidance",
    "3": "Broader Domestic and EU frameworks"
}

# Map regulation numbers to their correct sections
REGULATION_TO_SECTION = {
    "1.1": "1",
    "1.2": "1",
    "1.3": "1",
    "2.1": "2",
    "2.2": "2",
    "2.3": "2",
    "3.1": "3",
    "3.2": "3",
    "3.3": "3",
    "3.4": "3",
    "3.5": "3",
    "3.6": "3",
    "3.7": "3",
    "3.8": "3"
}

def extract_text_and_images(pdf_path):
    """Extract text and image information from PDF using PyMuPDF"""
    print(f"Extracting text and images from {os.path.basename(pdf_path)}")
    doc = fitz.open(pdf_path)
    
    all_page_content = []
    
    for page_num in tqdm(range(doc.page_count), desc="Processing pages"):
        page = doc.load_page(page_num)
        
        # Extract text using multiple methods for best results
        text_dict = page.get_text("dict")
        text_html = page.get_text("html")
        text_json = page.get_text("json")
        text_plain = page.get_text("text")
        
        # Process text dictionary to extract all text content
        processed_text = process_text_dict(text_dict)
        
        # Get image information
        image_info = []
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                
                if base_image:
                    image_info.append({
                        "index": img_index,
                        "width": img[2],
                        "height": img[3]
                    })
            except Exception as e:
                print(f"Error extracting image {img_index} on page {page_num+1}: {e}")
        
        # Combine all content for this page
        page_content = {
            "page_number": page_num + 1,
            "text": processed_text if processed_text else text_plain,
            "image_count": len(image_list),
            "image_info": image_info
        }
        
        all_page_content.append(page_content)
    
    doc.close()
    return all_page_content

def process_text_dict(text_dict):
    """Process the text dictionary from PyMuPDF to extract all text content"""
    if not text_dict or "blocks" not in text_dict:
        return ""
    
    all_text = []
    
    # Process each block
    for block in text_dict["blocks"]:
        # Check if it's a text block
        if "lines" in block:
            block_text = []
            
            # Process each line in the block
            for line in block["lines"]:
                line_text = []
                
                # Process each span in the line
                if "spans" in line:
                    for span in line["spans"]:
                        if "text" in span:
                            line_text.append(span["text"])
                
                # Join spans into a line
                if line_text:
                    block_text.append(" ".join(line_text))
            
            # Join lines into a block
            if block_text:
                all_text.append("\n".join(block_text))
        
        # Check if it's an image block
        elif "image" in block:
            all_text.append("[IMAGE BLOCK]")
    
    # Join blocks into full text
    return "\n\n".join(all_text)

def create_full_text(page_contents):
    """Create a full text document from page contents"""
    full_text = []
    
    for page in page_contents:
        page_text = f"[Page {page['page_number']}]\n"
        page_text += page['text']
        
        if page['image_count'] > 0:
            page_text += f"\n[Contains {page['image_count']} images/figures]\n"
        
        full_text.append(page_text)
    
    return "\n\n".join(full_text)

def get_regulation_name(reg_num):
    """Get the name of a regulation based on regulation number"""
    if reg_num in REGULATION_NAMES:
        return REGULATION_NAMES[reg_num]
    
    # If not found in the map, use a generic name
    return f"Regulation {reg_num}"

def get_page_for_line(line_index, lines):
    """Determine which page a line is on based on page markers"""
    page = 1
    # lines is now a list of strings (lines of text)
    for i in range(line_index, -1, -1):
        if i < len(lines):
            page_match = re.match(r'\[Page (\d+)\]', lines[i])
            if page_match:
                page = int(page_match.group(1))
                break
    return page

def get_section_name(section_num):
    """Get the name of a section based on section number"""
    if section_num in SECTION_NAMES:
        return SECTION_NAMES[section_num]
    
    # If not found in the map, use a generic name
    return f"Section {section_num}"

def parse_regulations(page_contents):
    """Parse the regulations from the extracted text."""
    # Extract the full text from the page contents
    full_text = create_full_text(page_contents)
    
    # Initialize data structures
    regulations = []
    regulation_info = {}
    main_section = "1"  # Default to section 1
    
    # Pattern to identify section headings
    section_pattern = re.compile(r'Section\s*[-–]\s*(\d+)\s*(.*)', re.IGNORECASE)
    
    # Pattern to match regulation numbers like 1.1.1
    reg_pattern = re.compile(r'^(\d+)\.(\d+)\.(\d+)\s*$')
    
    # Pattern to match regulation numbers with text on the same line
    reg_text_pattern = re.compile(r'^(\d+)\.(\d+)\.(\d+)\s+(.+)$')
    
    # Pattern to match the start of a new regulation or section
    new_reg_pattern = re.compile(r'^\d+\.\d+\.\d+|^\d+\.\d+\s+[A-Z]|^Section\s*[-–]')

    lines = full_text.splitlines()
    current_section_num = None
    current_section_name = None
    
    # First pass: identify all main sections and 2-digit regulation numbers
    for i, line in enumerate(lines):
        # Check for section headers
        section_match = section_pattern.match(line)
        if section_match:
            current_section_num = section_match.group(1)
            current_section_name = section_match.group(2).strip()
            main_section = current_section_num
        
        # Check for regulation numbers (2-digit like 1.1, 2.3)
        if re.match(r'^\d+\.\d+\.?\s+[A-Z]', line):
            parts = line.split(maxsplit=1)
            if len(parts) >= 2:
                reg_num = parts[0].rstrip('.')
                if len(reg_num.split('.')) == 2:  # Only 2-digit regulation numbers
                    regulation_info[reg_num] = {
                        "name": get_regulation_name(reg_num),
                        "subsections": []
                    }
    
    # Second pass: extract 3-digit regulation numbers (subsections)
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for regulation with text on the same line
        reg_text_match = reg_text_pattern.match(line)
        if reg_text_match:
            main_section = reg_text_match.group(1)
            sub_section = reg_text_match.group(2)
            sub_sub_section = reg_text_match.group(3)
            reg_text = reg_text_match.group(4).strip()
            
            # Collect all text until the next regulation or section
            j = i + 1
            while j < len(lines) and not new_reg_pattern.match(lines[j].strip()):
                line_text = lines[j].strip()
                # Skip page markers, headers, footers, and image blocks
                if line_text and not re.match(r'\[Page \d+\]|Page \d+$|^Central Bank of Ireland|^\[IMAGE BLOCK\]|^\[Contains|^Guidance on', line_text):
                    reg_text += " " + line_text
                j += 1
            
            # Clean up footnote references and other non-regulation content
            reg_text = re.sub(r'\s+\d+\s+S\.I\..*?Consumer Protection Code\.', '', reg_text)
            reg_text = re.sub(r'\s+\d+\s+.*?\([^)]+\)', '', reg_text)
            # Remove specific regulation headers
            reg_text = re.sub(r'\s+1\.2\.\s+G20/OECD High.*?Protection', '', reg_text)
            reg_text = re.sub(r'\s+\d+\.\d+\.\s+[A-Z].*?$', '', reg_text)
            
            # Format the regulation number
            reg_num = f"{main_section}.{sub_section}"
            reg_sub = f"{main_section}.{sub_section}.{sub_sub_section}"
            
            # Find the page number for this regulation
            page = get_page_for_line(i, lines)
            
            # Determine section based on the first digit of the regulation number
            section_num = main_section
            section_name = get_section_name(section_num)
            
            # Get the regulation name
            reg_name = get_regulation_name(reg_num)
            
            # Create the regulation entry
            regulation = {
                "Section Number": section_num,
                "Section Name": section_name,
                "Regulation Number": reg_num,
                "Regulation Number Name": reg_name,
                "Regulation Sub Section Number": reg_sub,
                "Regulation Text": reg_text,
                "Document Name": "Guidance on Protecting Consumers in Vulnerable Circumstances",
                "Page": page
            }
            
            # Add to the list of regulations
            regulations.append(regulation)
            print(f"  Found Regulation {reg_sub}")
            i = j  # Skip to the next regulation or section
            continue
            
        # Check for regulation number on its own line
        reg_match = reg_pattern.match(line)
        if reg_match:
            main_section = reg_match.group(1)
            sub_section = reg_match.group(2)
            sub_sub_section = reg_match.group(3)
            
            # Format the regulation number
            reg_num = f"{main_section}.{sub_section}"
            reg_sub = f"{main_section}.{sub_section}.{sub_sub_section}"
            
            # Look at the next line for the regulation text
            if i + 1 < len(lines):
                reg_text = lines[i + 1].strip()
                
                # Collect all text until the next regulation or section
                j = i + 2
                while j < len(lines) and not new_reg_pattern.match(lines[j].strip()):
                    line_text = lines[j].strip()
                    # Skip page markers, headers, footers, and image blocks
                    if line_text and not re.match(r'\[Page \d+\]|Page \d+$|^Central Bank of Ireland|^\[IMAGE BLOCK\]|^\[Contains|^Guidance on', line_text):
                        reg_text += " " + line_text
                    j += 1
                
                # Clean up footnote references and other non-regulation content
                reg_text = re.sub(r'\s+\d+\s+S\.I\..*?Consumer Protection Code\.', '', reg_text)
                reg_text = re.sub(r'\s+\d+\s+.*?\([^)]+\)', '', reg_text)
                # Remove specific regulation headers
                reg_text = re.sub(r'\s+1\.2\.\s+G20/OECD High.*?Protection', '', reg_text)
                reg_text = re.sub(r'\s+\d+\.\d+\.\s+[A-Z].*?$', '', reg_text)
                
                # Find the page number for this regulation
                page = get_page_for_line(i, lines)
                
                # Determine section based on the first digit of the regulation number
                section_num = main_section
                section_name = get_section_name(section_num)
                
                # Get the regulation name
                reg_name = get_regulation_name(reg_num)
                
                # Create the regulation entry
                regulation = {
                    "Section Number": section_num,
                    "Section Name": section_name,
                    "Regulation Number": reg_num,
                    "Regulation Number Name": reg_name,
                    "Regulation Sub Section Number": reg_sub,
                    "Regulation Text": reg_text,
                    "Document Name": "Guidance on Protecting Consumers in Vulnerable Circumstances",
                    "Page": page
                }
                
                # Add to the list of regulations
                regulations.append(regulation)
                print(f"  Found Regulation {reg_sub}")
                i = j  # Skip to the next regulation or section
                continue
        
        i += 1
    
    return regulations

def main():
    # Extract text and images
    page_contents = extract_text_and_images(PDF_PATH)
    
    # Create full text
    full_text = create_full_text(page_contents)
    
    # Save the full text
    with open(TEXT_OUT, 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"  Saved full text to {os.path.basename(TEXT_OUT)}")
    
    # Parse regulations
    regs = parse_regulations(page_contents)
    print(f"  Extracted {len(regs)} regulations/sections.")
    
    # Save regulations to JSON
    with open(JSON_OUT, 'w', encoding='utf-8') as f:
        json.dump(regs, f, indent=2, ensure_ascii=False)
    print(f"  Saved regulations to {os.path.basename(JSON_OUT)}")
    
    # Also save structured page content
    structured_out = JSON_OUT.replace('.json', '_structured.json')
    with open(structured_out, 'w', encoding='utf-8') as f:
        json.dump(page_contents, f, indent=2, ensure_ascii=False)
    print(f"  Saved structured page content to {os.path.basename(structured_out)}")

if __name__ == "__main__":
    main()
