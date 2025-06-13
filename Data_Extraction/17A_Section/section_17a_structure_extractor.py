import os
import re
import json
import PyPDF2
from pathlib import Path

def extract_structure(pdf_path, output_path):
    """Extract just the structure from a Section 17A document without the text content"""
    
    # Extract text from PDF
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    
    # Source name is fixed for this document
    source_name = "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025"
    
    # Define the known structure
    structure = [
        {"section": 1, "part": "Part 1", "part_name": "PRELIMINARY AND GENERAL", "sub_chapter": "Citation and commencement"},
        {"section": 2, "part": "Part 1", "part_name": "PRELIMINARY AND GENERAL", "sub_chapter": "Scope and application"},
        {"section": 3, "part": "Part 1", "part_name": "PRELIMINARY AND GENERAL", "sub_chapter": "Definitions"},
        {"section": 4, "part": "Part 2", "part_name": "STANDARDS FOR BUSINESS", "sub_chapter": "Standards for business"},
        {"section": 5, "part": "Part 3", "part_name": "SUPPORTING STANDARDS FOR BUSINESS", "sub_chapter": "Securing customers' interests"},
        {"section": 6, "part": "Part 3", "part_name": "SUPPORTING STANDARDS FOR BUSINESS", "sub_chapter": "Acting with honesty and integrity"},
        {"section": 7, "part": "Part 3", "part_name": "SUPPORTING STANDARDS FOR BUSINESS", "sub_chapter": "Acting with due skill, care and diligence"},
        {"section": 8, "part": "Part 3", "part_name": "SUPPORTING STANDARDS FOR BUSINESS", "sub_chapter": "Acting in the best interests of customers and treating them fairly and professionally"},
        {"section": 9, "part": "Part 3", "part_name": "SUPPORTING STANDARDS FOR BUSINESS", "sub_chapter": "Informing effectively"},
        {"section": 10, "part": "Part 3", "part_name": "SUPPORTING STANDARDS FOR BUSINESS", "sub_chapter": "Financial abuse"},
        {"section": 11, "part": "Part 3", "part_name": "SUPPORTING STANDARDS FOR BUSINESS", "sub_chapter": "Controlling and managing its affairs"},
        {"section": 12, "part": "Part 3", "part_name": "SUPPORTING STANDARDS FOR BUSINESS", "sub_chapter": "Adequate financial resources"},
        {"section": 13, "part": "Part 3", "part_name": "SUPPORTING STANDARDS FOR BUSINESS", "sub_chapter": "Disclosure and cooperation"},
        {"section": 14, "part": "Part 3", "part_name": "SUPPORTING STANDARDS FOR BUSINESS", "sub_chapter": "Systems and controls"}
    ]
    
    # Create the result list with just the structure
    result = []
    for item in structure:
        section_num = item["section"]
        
        # Find the section in the text to confirm it exists
        section_pattern = rf"^{section_num}\.\s"
        if re.search(section_pattern, text, re.MULTILINE):
            result.append({
                "Source Name": source_name,
                "Chapter Number": item["part"],
                "Chapter Name": item["part_name"],
                "Sub Chapter Name": item["sub_chapter"],
                "Sub Section Number": section_num
            })
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"Structure data saved to {output_path}")
    return result

if __name__ == "__main__":
    # Define paths
    base_dir = Path(__file__).parent.parent
    input_17a = base_dir / "Input" / "17A" / "central-bank-reform-act-2010-section-17a-regulations.pdf"
    output_17a = base_dir / "output" / "17a_structure.json"
    
    print(f"Extracting structure from: {input_17a}")
    print(f"Output will be saved to: {output_17a}")
    
    extract_structure(input_17a, output_17a)
