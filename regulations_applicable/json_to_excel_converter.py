import json
import pandas as pd
import os
from pathlib import Path

def convert_json_to_excel(json_path, excel_path):
    """
    Convert the analyzed regulations JSON file to Excel format.
    
    Args:
        json_path (str): Path to the analyzed regulations JSON file
        excel_path (str): Path to save the Excel file
    """
    print(f"Converting {json_path} to Excel format...")
    
    # Load the JSON data
    with open(json_path, 'r', encoding='utf-8') as f:
        regulations = json.load(f)
    
    # Convert to DataFrame
    df = pd.DataFrame(regulations)
    
    # Reorder columns for better readability
    columns_order = [
        'Source Name', 'Section Type', 'Part Number', 'Part Name', 
        'Regulation Number', 'Regulation Title', 'Applicability', 
        'Reason for Applicability', 'How are you reasoning', 'Confidence Score',
        'Regulation Text'
    ]
    
    # Only include columns that exist in the dataframe
    columns_to_use = [col for col in columns_order if col in df.columns]
    
    # Add any remaining columns that weren't in our predefined order
    for col in df.columns:
        if col not in columns_to_use:
            columns_to_use.append(col)
    
    # Reorder the dataframe
    df = df[columns_to_use]
    
    # Create Excel writer with formatting
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        # Write the dataframe to Excel
        df.to_excel(writer, sheet_name='Regulations', index=False)
        
        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Regulations']
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D9D9D9',
            'border': 1
        })
        
        # Define formats for different applicability statuses
        applies_format = workbook.add_format({'bg_color': '#C6EFCE'})  # Light green
        may_apply_format = workbook.add_format({'bg_color': '#FFEB9C'})  # Light yellow
        not_apply_format = workbook.add_format({'bg_color': '#FFC7CE'})  # Light red
        
        # Format the header row
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Source Name
        worksheet.set_column('B:B', 12)  # Section Type
        worksheet.set_column('C:C', 12)  # Part Number
        worksheet.set_column('D:D', 25)  # Part Name
        worksheet.set_column('E:E', 18)  # Regulation Number
        worksheet.set_column('F:F', 30)  # Regulation Title
        worksheet.set_column('G:G', 15)  # Applicability
        worksheet.set_column('H:H', 40)  # Reason for Applicability
        worksheet.set_column('I:I', 40)  # How are you reasoning
        worksheet.set_column('J:J', 15)  # Confidence Score
        worksheet.set_column('K:K', 60)  # Regulation Text
        
        # Apply conditional formatting based on applicability
        applicability_col = columns_to_use.index('Applicability')
        worksheet.conditional_format(1, applicability_col, len(df), applicability_col, {
            'type': 'cell',
            'criteria': 'equal to',
            'value': '"Applies"',
            'format': applies_format
        })
        
        worksheet.conditional_format(1, applicability_col, len(df), applicability_col, {
            'type': 'cell',
            'criteria': 'equal to',
            'value': '"May Apply - Requires Further Review"',
            'format': may_apply_format
        })
        
        worksheet.conditional_format(1, applicability_col, len(df), applicability_col, {
            'type': 'cell',
            'criteria': 'equal to',
            'value': '"Does Not Apply"',
            'format': not_apply_format
        })
        
        # Add filters to all columns
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
        
        # Freeze the header row
        worksheet.freeze_panes(1, 0)
    
    print(f"Excel file saved to {excel_path}")
    return excel_path

def main():
    # Set up paths
    base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
    json_path = base_dir / "output" / "regulations_applicable" / "analyzed_regulations.json"
    excel_path = base_dir / "output" / "regulations_applicable" / "analyzed_regulations.xlsx"
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    
    # Convert JSON to Excel
    excel_file = convert_json_to_excel(json_path, excel_path)
    
    print(f"\nConversion complete! The Excel file is ready at:\n{excel_file}")
    print("\nThe Excel file includes:")
    print("- Formatted headers and column widths")
    print("- Color-coded applicability status")
    print("- Filtering capability for all columns")
    print("- Frozen header row for easier navigation")

if __name__ == "__main__":
    main()
