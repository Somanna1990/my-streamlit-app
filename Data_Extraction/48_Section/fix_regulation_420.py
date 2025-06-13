import json
from pathlib import Path

def fix_regulation_420():
    # Path to the combined regulations JSON file
    json_path = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life\output\combined_regulations.json")
    
    # Load the JSON data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find Regulation 420 and fix its text
    for item in data:
        if item["Regulation Number"] == 420:
            # Set the correct text for Regulation 420
            item["Regulation Text"] = "420. A failure by a regulated entity to comply with any requirement or obligation imposed pursuant to these Regulations is a prescribed contravention for the purpose of the administrative sanctions procedure under Part IIIC of the Act of 1942 and may be subject to enforcement action and the imposition of administrative sanctions by the Bank in accordance with that Part."
            break
    
    # Save the updated JSON data
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Fixed Regulation 420 in {json_path}")

if __name__ == "__main__":
    fix_regulation_420()
