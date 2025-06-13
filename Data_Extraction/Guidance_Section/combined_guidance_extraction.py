"""
Combined Guidance Extraction Script

This script runs all three guidance extraction scripts:
1. extract_general_guidance.py
2. extract_securing_customers.py
3. extract_vulnerable_circumstances.py

After running all scripts, it combines their outputs into a single JSON file.
"""

import os
import json
import subprocess
from pathlib import Path
from tqdm import tqdm

# Set up paths
BASE_DIR = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
OUTPUT_DIR = BASE_DIR / "output" / "Guidance"
COMBINED_JSON_OUT = str(OUTPUT_DIR / "combined_guidance.json")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_extraction_script(script_name):
    """Run an extraction script and return its status"""
    print(f"\n{'='*80}\nRunning {script_name}...\n{'='*80}")
    script_path = os.path.join("Data_Extraction", "Guidance_Section", script_name)
    result = subprocess.run(["python", script_path], cwd=str(BASE_DIR), capture_output=True, text=True)
    
    # Print the output
    print(result.stdout)
    
    if result.returncode != 0:
        print(f"Error running {script_name}:")
        print(result.stderr)
        return False
    
    return True

def combine_json_files():
    """Combine all guidance JSON files into a single file"""
    print(f"\n{'='*80}\nCombining JSON files...\n{'='*80}")
    
    # List of JSON files to combine
    json_files = [
        "general-guidance-on-the-consumer-protection-code.json",
        "securing-customers-interests-guidance.json",
        "guidance-on-vulnerable-customers.json"
    ]
    
    combined_data = []
    
    # Load and combine all JSON files
    for json_file in tqdm(json_files, desc="Processing JSON files"):
        file_path = OUTPUT_DIR / json_file
        
        if not file_path.exists():
            print(f"Warning: {json_file} does not exist, skipping...")
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Add a source field to each entry
            for entry in data:
                # The source is already in the Document Name field, but we'll keep it consistent
                entry["Source File"] = json_file
                
            combined_data.extend(data)
            print(f"  Added {len(data)} regulations from {json_file}")
            
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")
    
    # Save the combined data
    with open(COMBINED_JSON_OUT, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"Combined {len(combined_data)} regulations into {COMBINED_JSON_OUT}")
    return len(combined_data)

def main():
    """Run all extraction scripts and combine their outputs"""
    print("Starting combined guidance extraction...")
    
    # List of scripts to run
    scripts = [
        "extract_general_guidance.py",
        "extract_securing_customers.py",
        "extract_vulnerable_circumstances.py"
    ]
    
    # Run each script
    success_count = 0
    for script in scripts:
        if run_extraction_script(script):
            success_count += 1
    
    print(f"\nSuccessfully ran {success_count} out of {len(scripts)} extraction scripts.")
    
    # Combine the JSON files
    if success_count > 0:
        total_regulations = combine_json_files()
        print(f"\nExtraction complete! Combined {total_regulations} regulations from all guidance documents.")
    else:
        print("\nNo extraction scripts completed successfully. Cannot combine JSON files.")

if __name__ == "__main__":
    main()
