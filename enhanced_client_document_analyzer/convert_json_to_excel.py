import json
import pandas as pd
from pathlib import Path
import re

def convert_json_to_excel():
    """Converts the compliance_analysis_results.json to an Excel file with improved formatting."""
    base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
    json_file_path = base_dir / "output" / "enhanced_document_analysis" / "compliance_analysis_results.json"
    excel_file_path = base_dir / "output" / "enhanced_document_analysis" / "compliance_analysis_report.xlsx"

    print(f"Reading JSON data from {json_file_path}...")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_rows = []
    # Define the order of columns we want in the Excel file
    detailed_results_columns = [
        'applicability',
        'is_compliant',
        'regulation_number',
        'regulation_title',
        'regulation_text',  # Added regulation_text
        'compliance_reasoning',
        'applicability_reasoning',  # Added applicability_reasoning next to compliance_reasoning
        'compliance_evidence',  # Added regular compliance_evidence
        'compliance_evidence_with_page',
        'gap_description',
        'gap_recommendations',
        'confidence_score',
        'section_type',
        'source_name',
        'evidence_page'
    ]

    print("Processing data...")
    for document_analysis in data:
        main_document_name = document_analysis.get('document_name', 'Unknown Document')
        detailed_results = document_analysis.get('detailed_results', [])

        # Create a set to track unique regulation numbers per document to avoid duplicates
        seen_regulations = set()

        for result_item in detailed_results:
            # Create a unique identifier for this regulation
            reg_id = (result_item.get('regulation_number', ''), 
                      result_item.get('section_type', ''), 
                      result_item.get('source_name', ''))
            
            # Skip if we've already seen this regulation for this document
            if reg_id in seen_regulations:
                continue
                
            seen_regulations.add(reg_id)
            
            row = {'document_name': main_document_name}
            
            # Include all fields from detailed_results
            for col_name in detailed_results_columns:
                if col_name != 'document_name':  # Skip the redundant column
                    row[col_name] = result_item.get(col_name)
            
            # Extract regulation number as integer for better sorting
            if 'regulation_number' in result_item:
                try:
                    row['regulation_number_int'] = int(result_item['regulation_number'])
                except (ValueError, TypeError):
                    # If it's not a simple integer, try to extract numbers
                    if isinstance(result_item['regulation_number'], str):
                        numbers = re.findall(r'\d+', result_item['regulation_number'])
                        if numbers:
                            row['regulation_number_int'] = int(numbers[0])
                        else:
                            row['regulation_number_int'] = 9999  # Default high value for non-numeric
                    else:
                        row['regulation_number_int'] = 9999  # Default high value for non-numeric
            else:
                row['regulation_number_int'] = 9999  # Default high value if no regulation number
                
            all_rows.append(row)

    if not all_rows:
        print("No data to write to Excel.")
        return

    df = pd.DataFrame(all_rows)

    # Custom sort order for 'applicability'
    applicability_order = {
        'Applies': 0, 
        'May Apply - Requires Further Review': 1,
        'May Apply': 1,  # Handle both formats
        'Does Not Apply': 2
    }
    df['sort_applicability'] = df['applicability'].map(applicability_order).fillna(3)  # Handle any other values

    print("Sorting data...")
    # Sort by document name, then applicability, then regulation number
    df.sort_values(
        by=['document_name', 'sort_applicability', 'regulation_number_int'], 
        inplace=True
    )
    
    # Remove the sorting helper columns
    df.drop(columns=['sort_applicability', 'regulation_number_int'], inplace=True)
    
    # Ensure document_name is the first column, followed by the rest in our preferred order
    final_column_order = ['document_name'] + [col for col in detailed_results_columns if col in df.columns]
    df = df[final_column_order]

    # Create Excel writer with formatting
    print(f"Writing data to Excel file: {excel_file_path}...")
    try:
        with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Compliance Analysis', index=False)
            
            # Get the workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Compliance Analysis']
            
            # Auto-adjust column widths based on content
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if cell.value:
                            cell_length = len(str(cell.value))
                            if cell_length > max_length:
                                max_length = cell_length
                    except:
                        pass
                
                # Limit maximum column width to avoid extremely wide columns
                adjusted_width = min(max_length + 2, 50)  
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Add filters to the header row
            worksheet.auto_filter.ref = worksheet.dimensions
            
        print(f"Successfully created Excel file: {excel_file_path}")
    except Exception as e:
        print(f"Error writing to Excel: {e}")
        print("Please ensure you have 'openpyxl' installed: pip install openpyxl")

if __name__ == "__main__":
    convert_json_to_excel()
