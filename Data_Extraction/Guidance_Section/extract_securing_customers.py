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
PDF_PATH = str(INPUT_DIR / "securing-customers-interests-guidance.pdf")
DOC_NAME = "Guidance on Securing Customers' Interests"
JSON_OUT = str(OUTPUT_DIR / "securing-customers-interests-guidance.json")
TEXT_OUT = str(OUTPUT_DIR / "securing-customers-interests-guidance.txt")
STRUCTURED_JSON_OUT = str(OUTPUT_DIR / "securing-customers-interests-guidance_structured.json")

# Map regulation numbers to their names for this specific document
REGULATION_NAMES = {
    "1.1": "Introduction",
    "1.2": "Purpose of Guidance",
    "1.3": "Assessing Compliance",
    "1.4": "Scope",
    "1.5": "Proportionality",
    "1.6": "Customer Autonomy",
    "1.7": "Structure of Guidance",
    "2.1": "Aligning Culture, Strategy, Business Model, Decision-Making and Systems, Controls, Policies, Processes and Procedures with Customers’ Interests",
    "2.2": "Securing Customers’ Interests During Business Model Change and Innovation",
    "2.3": "Securing Customers’ Interests Through Product, Service and Delivery Channel Design",
    "2.4": "Customer Behaviours, Habits, Preferences and Biases",
    "2.5": "Dealing with Errors or Mistakes and Customer Complaints",
    "2.6": "Securing the Interests of All Customers",
    "2.7": "Unregulated Activities of Regulated Firms",
    "2.8": "Importance of Contractual Clarity",
    "2.9": "Delivering Fair Outcomes for Customers"
}

# Map section numbers to their names
SECTION_NAMES = {
    "1": "Introduction",
    "2": "Guidance"
}

# Map regulation numbers to their correct sections
REGULATION_TO_SECTION = {
    "1.1": "1",
    "1.2": "1",
    "1.3": "1",
    "1.4": "1",
    "1.5": "1",
    "1.6": "1",
    "1.7": "1",
    "2.1": "2",
    "2.2": "2",
    "2.3": "2",
    "2.4": "2",
    "2.5": "2",
    "3.1": "3",
    "3.2": "3",
    "3.3": "3",
    "3.4": "3",
    "3.5": "3"
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
        text_plain = page.get_text("text")
        
        # Process the text dictionary to extract structured content
        processed_text = process_text_dict(text_dict)
        
        # Get image information
        image_list = page.get_images(full=True)
        image_count = len(image_list)
        
        # Extract images if present
        images = []
        if image_list:
            for img_index, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]  # Get the image reference
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Create a PIL Image object
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Add image info to the list
                    images.append({
                        "index": img_index,
                        "width": image.width,
                        "height": image.height,
                        "format": image_ext
                    })
                except Exception as e:
                    print(f"Error extracting image: {e}")
        
        # Combine all content for this page
        page_content = {
            "page_number": page_num + 1,
            "text": processed_text if processed_text else text_plain,
            "image_count": image_count,
            "images": images
        }
        
        all_page_content.append(page_content)
    
    doc.close()
    return all_page_content

def process_text_dict(text_dict):
    """Process the text dictionary from PyMuPDF to extract structured content"""
    if not text_dict or "blocks" not in text_dict:
        return ""
    
    all_text = []
    
    for block in text_dict["blocks"]:
        block_text = []
        
        # Check if it's a text block
        if "lines" in block:
            for line in block["lines"]:
                line_text = []
                for span in line["spans"]:
                    if span["text"].strip():
                        line_text.append(span["text"])
                
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
                "Document Name": DOC_NAME,
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
                    "Document Name": DOC_NAME,
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

if __name__ == "__main__":
    main()
