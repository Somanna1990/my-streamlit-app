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

# Document name and paths for the General Guidance document only
PDF_PATH = str(INPUT_DIR / "general-guidance-on-the-consumer-protection-code March 2025.pdf")
DOC_NAME = "General Guidance on the Consumer Protection Code"
JSON_OUT = str(OUTPUT_DIR / "general-guidance-on-the-consumer-protection-code.json")
TEXT_OUT = str(OUTPUT_DIR / "general-guidance-on-the-consumer-protection-code.txt")

# Map regulation numbers to their names for the General Guidance document
REGULATION_NAMES = {
    "1.1": "Overview",
    "1.2": "Scope and Application",
    "1.3": "Definitions and Terminology",
    "1.4": "Assessing Compliance",
    "1.5": "Data Protection Obligations",
    "2.2": "Informing Effectively",
    "2.3": "Unregulated Activities",
    "2.4": "Financial Abuse",
    "3.2": "Knowing the Consumer and Suitability",
    "3.3": "Vulnerable Consumers",
    "3.4": "Complaints Resolution",
    "3.5": "Errors and Complaints Resolution",
    "3.6": "Advertising",
    "3.7": "Unsolicited Contact",
    "3.8": "Disclosure Requirements",
    "3.9": "Handling Claims",
    "3.10": "Rebates and Claims Processing",
    "3.11": "Arrears Handling",
    "3.12": "Charges",
    "3.13": "Payment Protection Insurance",
    "3.14": "Contact with Consumers",
    "3.15": "Premium Handling",
    "3.16": "Mortgage Lending",
    "3.17": "Advertising",
    "3.18": "Unsolicited Contact"
}

# Map section numbers to their names
SECTION_NAMES = {
    "1": "Introduction",
    "2": "Guidance on Standards for Business Regulations",
    "3": "Guidance on the Consumer Protection Regulations"
}

# Map regulation numbers to their correct sections
REGULATION_TO_SECTION = {
    "1.1": "1",
    "1.2": "1",
    "1.3": "1",
    "1.4": "1",
    "1.5": "1",
    "2.2": "2",
    "2.3": "2",
    "2.4": "2",
    "3.2": "3",
    "3.3": "3",
    "3.4": "3",
    "3.5": "3",
    "3.6": "3",
    "3.7": "3",
    "3.8": "3",
    "3.9": "3",
    "3.10": "3",
    "3.11": "3",
    "3.12": "3",
    "3.13": "3",
    "3.14": "3",
    "3.15": "3",
    "3.16": "3",
    "3.17": "3",
    "3.18": "3"
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

def get_regulation_name(doc_name, reg_num):
    """Get the name of a regulation based on regulation number"""
    # Since we're only dealing with one document, we can ignore doc_name
    if reg_num in REGULATION_NAMES:
        return REGULATION_NAMES[reg_num]
    
    # If not found in the map, use a generic name
    return f"Regulation {reg_num}"

def get_page_for_line(line_index, lines):
    """Determine which page a line is on based on page markers"""
    page = 1
    for i in range(line_index, -1, -1):
        page_match = re.match(r'\[Page (\d+)\]', lines[i])
        if page_match:
            page = int(page_match.group(1))
            break
    return page

def infer_section_from_context(doc_name, reg_num):
    """Infer section information based on regulation number"""
    # Extract the main section number from the regulation number
    main_section = reg_num.split('.')[0]
    
    # Map section numbers to their names for the General Guidance document
    section_map = {
        "1": "Introduction",
        "2": "Guidance on Standards for Business Regulations",
        "3": "Guidance on the Consumer Protection Regulations"
    }
    
    # Get default section name based on main section number
    if main_section in section_map:
        return main_section, section_map[main_section]
    
    # If not found in the map, use generic section name
    return main_section, f"Section {main_section}"

def get_section_name(section_num):
    """Get the name of a section based on section number"""
    if section_num in SECTION_NAMES:
        return SECTION_NAMES[section_num]
    return f"Section {section_num}"

def parse_regulations(page_contents, document_name):
    """Parse regulations from the extracted text"""
    print("Parsing regulations from extracted text")
    results = []
    
    # Combine all page text for processing
    full_text = create_full_text(page_contents)
    
    # Patterns for Section, Regulation, and Subsection
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
    
    # Keep track of regulation numbers and their names
    regulation_info = {}
    
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
                        "name": get_regulation_name(document_name, reg_num),
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
                if line_text and not re.match(r'\[Page \d+\]|Page \d+$|^Central Bank of Ireland|^\[IMAGE BLOCK\]|^\[Contains|^General Guidance', line_text):
                    reg_text += " " + line_text
                j += 1
            
            # Clean up footnote references and other non-regulation content
            reg_text = re.sub(r'\s+\d+\s+S\.I\..*?Consumer Protection Code\.', '', reg_text)
            reg_text = re.sub(r'\s+\d+\s+.*?\([^)]+\)', '', reg_text)
            # Remove any regulation headers that might have been included
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
            regulation_name = regulation_info[reg_num]["name"] if reg_num in regulation_info else get_regulation_name(document_name, reg_num)
            
            # Create the regulation entry
            entry = {
                "Section Number": section_num,
                "Section Name": section_name,
                "Regulation Number": reg_num,
                "Regulation Number Name": regulation_name,
                "Regulation Sub Section Number": reg_sub,
                "Regulation Text": reg_text,
                "Document Name": document_name,
                "Page": page
            }
            
            # Add to the list of regulations
            results.append(entry)
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
                    if line_text and not re.match(r'\[Page \d+\]|Page \d+$|^Central Bank of Ireland|^\[IMAGE BLOCK\]|^\[Contains|^General Guidance', line_text):
                        reg_text += " " + line_text
                    j += 1
                
                # Clean up footnote references and other non-regulation content
                reg_text = re.sub(r'\s+\d+\s+S\.I\..*?Consumer Protection Code\.', '', reg_text)
                reg_text = re.sub(r'\s+\d+\s+.*?\([^)]+\)', '', reg_text)
                # Remove any regulation headers that might have been included
                reg_text = re.sub(r'\s+\d+\.\d+\.\s+[A-Z].*?$', '', reg_text)
                
                # Find the page number for this regulation
                page = get_page_for_line(i, lines)
                
                # Determine section based on the first digit of the regulation number
                section_num = main_section
                section_name = get_section_name(section_num)
                
                # Get the regulation name
                regulation_name = regulation_info[reg_num]["name"] if reg_num in regulation_info else get_regulation_name(document_name, reg_num)
                
                # Create the regulation entry
                entry = {
                    "Section Number": section_num,
                    "Section Name": section_name,
                    "Regulation Number": reg_num,
                    "Regulation Number Name": regulation_name,
                    "Regulation Sub Section Number": reg_sub,
                    "Regulation Text": reg_text,
                    "Document Name": document_name,
                    "Page": page
                }
                
                # Add to the list of regulations
                results.append(entry)
                print(f"  Found Regulation {reg_sub}")
                i = j  # Skip to the next regulation or section
                continue
        
        i += 1
    
    return results

def process_pdf(pdf_path, doc_name, json_out, text_out):
    """Process a PDF file to extract text and regulations"""
    print(f"Processing {os.path.basename(pdf_path)} ...")
    
    # Extract text and images
    page_contents = extract_text_and_images(pdf_path)
    
    # Create full text
    full_text = create_full_text(page_contents)
    
    # Save the full text
    with open(text_out, 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"  Saved full text to {os.path.basename(text_out)}")
    
    # Parse regulations
    regs = parse_regulations(page_contents, doc_name)
    print(f"  Extracted {len(regs)} regulations/sections.")
    
    # Save regulations to JSON
    with open(json_out, 'w', encoding='utf-8') as f:
        json.dump(regs, f, indent=2, ensure_ascii=False)
    print(f"  Saved regulations to {os.path.basename(json_out)}")
    
    # Also save structured page content
    structured_out = json_out.replace('.json', '_structured.json')
    with open(structured_out, 'w', encoding='utf-8') as f:
        json.dump(page_contents, f, indent=2, ensure_ascii=False)
    print(f"  Saved structured page content to {os.path.basename(structured_out)}")

def main():
    # Extract text and images
    page_contents = extract_text_and_images(PDF_PATH)
    
    # Create full text
    full_text = create_full_text(page_contents)
    
    # Save the full text
    with open(TEXT_OUT, 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"Saved full text to {os.path.basename(TEXT_OUT)}")
    
    # Parse regulations
    regs = parse_regulations(page_contents, DOC_NAME)
    print(f"Extracted {len(regs)} regulations/sections.")
    
    # Save regulations to JSON
    with open(JSON_OUT, 'w', encoding='utf-8') as f:
        json.dump(regs, f, indent=2, ensure_ascii=False)
    print(f"Saved regulations to {os.path.basename(JSON_OUT)}")
    
    # Also save structured page content
    structured_out = JSON_OUT.replace('.json', '_structured.json')
    with open(structured_out, 'w', encoding='utf-8') as f:
        json.dump(page_contents, f, indent=2, ensure_ascii=False)
    print(f"Saved structured page content to {os.path.basename(structured_out)}")

if __name__ == "__main__":
    main()
