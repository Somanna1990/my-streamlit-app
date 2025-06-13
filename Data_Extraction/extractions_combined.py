import os
import sys
import json
import importlib.util
from pathlib import Path

# ===============================================================
# Combined extractor for Section 17A and Section 48 regulations
# ===============================================================

def import_module_from_path(module_name, file_path):
    """Import a module from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def run_17a_structure_extractor(output_path=None):
    """Run the section_17a_structure_extractor.py script"""
    # Get the directory of the current script
    current_dir = Path(__file__).parent
    
    # Path to the original script
    script_path = current_dir / "17A_Section" / "section_17a_structure_extractor.py"
    
    # Import the script as a module
    extractor = import_module_from_path("section_17a_structure_extractor", script_path)
    
    # Get the input PDF path - CORRECTED PATH
    input_path = Path("Input") / "17A" / "central-bank-reform-act-2010-section-17a-regulations.pdf"
    
    # Set output path if not provided
    if not output_path:
        output_path = Path("output") / "Data_extraction" / "17a_structure.json"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Run the extractor
    result = extractor.extract_structure(str(input_path), str(output_path))
    print(f"Section 17A structure saved to {output_path}")
    
    return result

def run_17a_text_extractor(structure_path, output_path=None):
    """Run the section_17a_text_extractor_v2.py script"""
    # Get the directory of the current script
    current_dir = Path(__file__).parent
    
    # Path to the original script
    script_path = current_dir / "17A_Section" / "section_17a_text_extractor_v2.py"
    
    # Import the script as a module
    extractor = import_module_from_path("section_17a_text_extractor_v2", script_path)
    
    # Get the input PDF path - CORRECTED PATH
    input_path = Path("Input") / "17A" / "central-bank-reform-act-2010-section-17a-regulations.pdf"
    
    # Set output path if not provided
    if not output_path:
        output_path = Path("output") / "Data_extraction" / "17a_complete.json"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Run the extractor
    result = extractor.extract_text_content(str(input_path), str(structure_path), str(output_path))
    print(f"Section 17A text extraction completed and saved to {output_path}")
    
    return result

def run_48_combined_extractor(output_path=None):
    """Run the combined_regulation_extractor.py script for Section 48"""
    # Get the directory of the current script
    current_dir = Path(__file__).parent
    
    # Path to the original script
    script_path = current_dir / "48_Section" / "combined_regulation_extractor.py"
    
    # Import the script as a module
    extractor = import_module_from_path("combined_regulation_extractor", script_path)
    
    # Get the input PDF path - PATH IS CORRECT
    input_path = Path("Input") / "Section-48" / "central-bank-supervision-and-enforcement-act-2013-section-48 (1).pdf"
    
    # Set output path if not provided
    if not output_path:
        output_path = Path("output") / "Data_extraction" / "section_48_combined.json"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Run the extractor directly using the functions from the original script
    print(f"Processing document: {input_path}")
    
    # Step 1: Extract structure (titles)
    print("Step 1: Extracting structure...")
    structure_data = extractor.extract_structure(str(input_path))
    print(f"Extracted structure for {len(structure_data)} regulations")
    
    # Step 2: Extract regulation text
    print("Step 2: Extracting regulation text...")
    text_data = extractor.extract_regulation_text(str(input_path))
    print(f"Extracted text for {len(text_data)} regulations")
    
    # Step 3: Combine structure and text
    print("Step 3: Combining structure and text...")
    extractor.combine_structure_and_text(structure_data, text_data, str(output_path))
    
    # Load the result
    with open(output_path, 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    print(f"Section 48 extraction completed and saved to {output_path}")
    
    return result

def standardize_17a_data(data):
    """Standardize Section 17A data to match the common schema"""
    standardized_data = []
    
    for item in data:
        # Create a new standardized entry
        entry = {
            "Source Name": item["Source Name"],
            "Section Type": "17A",
            "Part Number": item["Chapter Number"].replace("Part ", ""),
            "Part Name": item["Chapter Name"],
            "Chapter Number": "",  # No chapter in 17A
            "Chapter Name": "",    # No chapter in 17A
            "Regulation Number": item["Sub Section Number"],
            "Regulation Title": item["Sub Chapter Name"],
            "Regulation Text": item.get("Section Number Text", "")
        }
        standardized_data.append(entry)
    
    return standardized_data

def standardize_48_data(data):
    """Standardize Section 48 data to match the common schema"""
    standardized_data = []
    
    for item in data:
        # Create a new standardized entry
        entry = {
            "Source Name": item["Source Name"],
            "Section Type": "48",
            "Part Number": item.get("Part Number", "1"),  # Default to Part 1 for Section 48
            "Part Name": item.get("Part Name", ""),
            "Chapter Number": item.get("Chapter Number", ""),
            "Chapter Name": item.get("Chapter Name", ""),
            "Regulation Number": item["Regulation Number"],
            "Regulation Title": item["Regulation Title"],
            "Regulation Text": item["Regulation Text"]
        }
        standardized_data.append(entry)
    
    return standardized_data

def create_combined_json(data_17a, data_48, output_path):
    """Create a combined JSON file with both Section 17A and Section 48 data"""
    # Combine the data
    combined_data = data_17a + data_48
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"Combined data saved to {output_path}")
    
    return combined_data

def main():
    """Main function to run the extraction process"""
    # Define paths
    base_dir = Path(".")  # Current directory
    output_dir = base_dir / "output" / "Data_extraction"
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Run section_17a_structure_extractor.py
    print("Step 1: Running section_17a_structure_extractor.py")
    structure_17a_path = output_dir / "17a_structure.json"
    run_17a_structure_extractor(structure_17a_path)
    
    # Step 2: Run section_17a_text_extractor_v2.py
    print("Step 2: Running section_17a_text_extractor_v2.py")
    complete_17a_path = output_dir / "17a_complete.json"
    data_17a = run_17a_text_extractor(structure_17a_path, complete_17a_path)
    
    # Step 3: Run combined_regulation_extractor.py
    print("Step 3: Running combined_regulation_extractor.py")
    section_48_path = output_dir / "section_48_combined.json"
    data_48 = run_48_combined_extractor(section_48_path)
    
    # Step 4: Combine into one JSON with formalized schema
    print("Step 4: Combining into one JSON with formalized schema")
    # Standardize the data
    standardized_17a = standardize_17a_data(data_17a)
    standardized_48 = standardize_48_data(data_48)
    
    # Create combined JSON
    combined_path = output_dir / "regulation_17A_48_combined.json"
    create_combined_json(standardized_17a, standardized_48, combined_path)

if __name__ == "__main__":
    main()
