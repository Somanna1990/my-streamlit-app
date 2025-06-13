import os
import re
import json
import PyPDF2
from pathlib import Path

def extract_text_content(pdf_path, structure_path, output_path):
    """Extract text content for each section and combine with the structure"""
    
    # Load the structure
    with open(structure_path, 'r', encoding='utf-8') as f:
        structure = json.load(f)
    
    # Extract text from PDF
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        # Extract text from each page
        all_pages_text = []
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            all_pages_text.append(page_text)
        
        # Join all pages
        full_text = "\n".join(all_pages_text)
    
    print(f"Extracted text from {len(reader.pages)} pages")
    
    # Create a list to store the complete data
    result = []
    
    # First, identify all section numbers and their positions in the text
    section_positions = {}
    for section_info in structure:
        section_num = section_info["Sub Section Number"]
        
        # Look for various formats of section numbers
        patterns = [
            rf"(?:^|\n)(?:{section_num}\.\s)",  # Format: "1. "
            rf"(?:^|\n)(?:\({section_num}\)\s)",  # Format: "(1) "
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, full_text))
            if matches:
                # Use the first match
                section_positions[section_num] = matches[0].start()
                print(f"Found section {section_num} at position {section_positions[section_num]}")
                break
    
    # Sort section numbers by their position in the text
    sorted_sections = sorted(section_positions.keys(), key=lambda x: section_positions[x])
    
    # Process each section
    for i, section_num in enumerate(sorted_sections):
        # Find the corresponding section info
        section_info = None
        for s in structure:
            if s["Sub Section Number"] == section_num:
                section_info = s
                break
        
        if not section_info:
            print(f"Warning: No structure info found for section {section_num}")
            continue
        
        # Get the start position of this section
        start_pos = section_positions[section_num]
        
        # Determine the end position (either the next section or the end of the text)
        end_pos = len(full_text)
        if i < len(sorted_sections) - 1:
            next_section_num = sorted_sections[i + 1]
            end_pos = section_positions[next_section_num]
        
        # Extract the text for this section
        section_text = full_text[start_pos:end_pos].strip()
        
        # Remove the section number from the beginning
        section_text = re.sub(rf"^{section_num}\.\s*", "", section_text)
        section_text = re.sub(rf"^\({section_num}\)\s*", "", section_text)
        
        # Clean up the text
        # 1. Remove page numbers like "[80] 3"
        section_text = re.sub(r'\[\d+\]\s+\d+', '', section_text)
        
        # 2. Remove sub-chapter names at the end of the text
        for s in structure:
            sub_chapter = s["Sub Chapter Name"]
            if not sub_chapter:
                continue
            
            # Check for exact matches at the end
            if section_text.endswith(sub_chapter):
                section_text = section_text[:-len(sub_chapter)].strip()
                continue
            elif section_text.endswith("\n" + sub_chapter):
                section_text = section_text[:-len("\n" + sub_chapter)].strip()
                continue
            elif section_text.endswith("\n\n" + sub_chapter):
                section_text = section_text[:-len("\n\n" + sub_chapter)].strip()
                continue
            
            # Check for the sub-chapter name anywhere in the text
            sub_chapter_pattern = rf"\n{re.escape(sub_chapter)}\n"
            if re.search(sub_chapter_pattern, section_text):
                # Only remove if it's not this section's own sub-chapter name
                if sub_chapter != section_info["Sub Chapter Name"]:
                    parts = section_text.split(sub_chapter)
                    if len(parts) > 1:
                        section_text = parts[0].strip()
                        
            # Also check for sub-chapter at the end with no newline after
            sub_chapter_end_pattern = rf"\n{re.escape(sub_chapter)}$"
            if re.search(sub_chapter_end_pattern, section_text):
                if sub_chapter != section_info["Sub Chapter Name"]:
                    section_text = re.sub(sub_chapter_end_pattern, "", section_text)
        
        # Special handling for section 7 which has section 8's sub-chapter name at the end
        if section_num == 7:
            # Hardcoded fix for section 7
            if "Acting in the best interests of customers and treating them fairly and" in section_text:
                section_text = section_text.split("Acting in the best interests of customers and treating them fairly and")[0].strip()
            elif "Acting in the best interests of customers and treating them fairly" in section_text:
                section_text = section_text.split("Acting in the best interests of customers and treating them fairly")[0].strip()
            elif "Acting in the best interests of customers" in section_text:
                section_text = section_text.split("Acting in the best interests of customers")[0].strip()
                
        # Special handling for section 14 to remove the explanatory note and signature
        if section_num == 14:
            if "Signed for and on behalf of the CENTRAL BANK OF IRELAND" in section_text:
                section_text = section_text.split("Signed for and on behalf of the CENTRAL BANK OF IRELAND")[0].strip()
        
        # Clean up the text to remove any section headers at the end
        
        # 1. Check for Part headers with various formats
        for part_num in range(1, 10):  # Assuming no more than 9 parts
            # Check for various formats of part headers
            patterns = [
                f"\n\nPart {part_num}\n",
                f"\n\nPart {part_num} ",
                f"\nPart {part_num}\n",
                f"\n \nPart {part_num}\n"
            ]
            
            for pattern in patterns:
                if pattern in section_text:
                    section_text = section_text.split(pattern)[0].strip()
        
        # 2. Check for specific part headers with their names
        part_headers = [
            "Part 1\nPRELIMINARY AND GENERAL",
            "Part 2\nSTANDARDS FOR BUSINESS",
            "Part 3\nSUPPORTING STANDARDS FOR BUSINESS"
        ]
        
        for header in part_headers:
            # Check for various formats
            patterns = [f"\n\n{header}", f"\n{header}", f" \n{header}"]
            for pattern in patterns:
                if pattern in section_text:
                    section_text = section_text.split(pattern)[0].strip()
        
        # 3. Check for all sub-chapter names that might appear at the end
        sub_chapter_names = [
            "Citation and commencement",
            "Scope and application",
            "Definitions",
            "Standards for business",
            "Securing customers' interests", "Securing customers\u2019 interests",
            "Acting with honesty and integrity",
            "Acting with due skill, care and diligence",
            "Acting in the best interests of customers and treating them fairly and professionally",
            "Informing effectively",
            "Financial abuse",
            "Controlling and managing its affairs",
            "Adequate financial resources",
            "Disclosure and cooperation",
            "Systems and controls"
        ]
        
        for sub_chapter in sub_chapter_names:
            # Skip the current section's own sub-chapter name
            if sub_chapter == section_info["Sub Chapter Name"]:
                continue
                
            # Check for various formats
            patterns = [f"\n\n{sub_chapter}", f"\n{sub_chapter}", f" \n{sub_chapter}"]
            for pattern in patterns:
                if pattern in section_text:
                    section_text = section_text.split(pattern)[0].strip()
        
        # 4. Special case for specific section headers that are causing issues
        if "\n\nPart 2\nSTANDARDS FOR BUSINESS" in section_text:
            section_text = section_text.split("\n\nPart 2\nSTANDARDS FOR BUSINESS")[0].strip()
            
        if "\n\nPart 3\nSUPPORTING STANDARDS FOR BUSINESS" in section_text:
            section_text = section_text.split("\n\nPart 3\nSUPPORTING STANDARDS FOR BUSINESS")[0].strip()
        
        # Final cleanup for specific patterns that might still be present
        # These are hardcoded fixes for the known issues
        if section_num == 3:
            # Remove Part 2 header at the end of regulation 3
            patterns = [
                "\n \nPart 2\nSTANDARDS FOR BUSINESS",
                "\nPart 2\nSTANDARDS FOR BUSINESS",
                "\n\nPart 2\nSTANDARDS FOR BUSINESS",
                "\n \nPart 2  \nSTANDARDS FOR BUSINESS",
                "\nPart 2  \nSTANDARDS FOR BUSINESS",
                "\n\nPart 2  \nSTANDARDS FOR BUSINESS",
                "Part 2\nSTANDARDS FOR BUSINESS",
                "Part 2  \nSTANDARDS FOR BUSINESS"
            ]
            
            for pattern in patterns:
                if pattern in section_text:
                    section_text = section_text.split(pattern)[0].strip()
        
        if section_num == 4:
            # Remove Part 3 header at the end of regulation 4
            patterns = [
                "\n \nPart 3\nSUPPORTING STANDARDS FOR BUSINESS",
                "\nPart 3\nSUPPORTING STANDARDS FOR BUSINESS",
                "\n\nPart 3\nSUPPORTING STANDARDS FOR BUSINESS",
                "\n \nPart 3  \nSUPPORTING STANDARDS FOR BUSINESS",
                "\nPart 3  \nSUPPORTING STANDARDS FOR BUSINESS",
                "\n\nPart 3  \nSUPPORTING STANDARDS FOR BUSINESS",
                "Part 3\nSUPPORTING STANDARDS FOR BUSINESS",
                "Part 3  \nSUPPORTING STANDARDS FOR BUSINESS"
            ]
            
            for pattern in patterns:
                if pattern in section_text:
                    section_text = section_text.split(pattern)[0].strip()
            
            # Also remove Securing customers' interests at the end of regulation 4
            patterns = [
                "\n \nSecuring customers' interests",
                "\nSecuring customers' interests",
                "\n\nSecuring customers' interests",
                "\n \nSecuring customers\u2019 interests",
                "\nSecuring customers\u2019 interests",
                "\n\nSecuring customers\u2019 interests",
                "Securing customers' interests",
                "Securing customers\u2019 interests"
            ]
            
            for pattern in patterns:
                if pattern in section_text:
                    section_text = section_text.split(pattern)[0].strip()
        
        # Add the section number back to the beginning of the text
        section_text = f"{section_num}. {section_text}"
        
        # Create a complete entry with structure and text
        entry = section_info.copy()
        entry["Section Number Text"] = section_text
        result.append(entry)
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"Complete data saved to {output_path}")
    return result

if __name__ == "__main__":
    # Define paths
    base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
    input_17a = base_dir / "Input" / "17A" / "central-bank-reform-act-2010-section-17a-regulations.pdf"
    
    # Create the output directory if it doesn't exist
    output_dir = base_dir / "output" / "Data_extraction"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a complete structure for all 14 subsections
    structure_data = [
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 1", "Chapter Name": "PRELIMINARY AND GENERAL", 
         "Sub Chapter Name": "Citation and commencement", "Sub Section Number": 1},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 1", "Chapter Name": "PRELIMINARY AND GENERAL", 
         "Sub Chapter Name": "Scope and application", "Sub Section Number": 2},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 1", "Chapter Name": "PRELIMINARY AND GENERAL", 
         "Sub Chapter Name": "Definitions", "Sub Section Number": 3},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 2", "Chapter Name": "STANDARDS FOR BUSINESS", 
         "Sub Chapter Name": "Standards for business", "Sub Section Number": 4},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 3", "Chapter Name": "SUPPORTING STANDARDS FOR BUSINESS", 
         "Sub Chapter Name": "Securing customers' interests", "Sub Section Number": 5},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 3", "Chapter Name": "SUPPORTING STANDARDS FOR BUSINESS", 
         "Sub Chapter Name": "Acting with honesty and integrity", "Sub Section Number": 6},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 3", "Chapter Name": "SUPPORTING STANDARDS FOR BUSINESS", 
         "Sub Chapter Name": "Acting with due skill, care and diligence", "Sub Section Number": 7},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 3", "Chapter Name": "SUPPORTING STANDARDS FOR BUSINESS", 
         "Sub Chapter Name": "Acting in the best interests of customers and treating them fairly and professionally", "Sub Section Number": 8},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 3", "Chapter Name": "SUPPORTING STANDARDS FOR BUSINESS", 
         "Sub Chapter Name": "Informing effectively", "Sub Section Number": 9},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 3", "Chapter Name": "SUPPORTING STANDARDS FOR BUSINESS", 
         "Sub Chapter Name": "Financial abuse", "Sub Section Number": 10},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 3", "Chapter Name": "SUPPORTING STANDARDS FOR BUSINESS", 
         "Sub Chapter Name": "Controlling and managing its affairs", "Sub Section Number": 11},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 3", "Chapter Name": "SUPPORTING STANDARDS FOR BUSINESS", 
         "Sub Chapter Name": "Adequate financial resources", "Sub Section Number": 12},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 3", "Chapter Name": "SUPPORTING STANDARDS FOR BUSINESS", 
         "Sub Chapter Name": "Disclosure and cooperation", "Sub Section Number": 13},
        {"Source Name": "CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025",
         "Chapter Number": "Part 3", "Chapter Name": "SUPPORTING STANDARDS FOR BUSINESS", 
         "Sub Chapter Name": "Systems and controls", "Sub Section Number": 14}
    ]
    
    # Save the structure to a temporary file
    structure_17a = output_dir / "17a_structure.json"
    with open(structure_17a, 'w', encoding='utf-8') as f:
        json.dump(structure_data, f, indent=2)
    
    output_17a = output_dir / "17a_complete.json"
    
    print(f"Extracting text content from: {input_17a}")
    print(f"Using structure from: {structure_17a}")
    print(f"Output will be saved to: {output_17a}")
    
    extract_text_content(input_17a, structure_17a, output_17a)
