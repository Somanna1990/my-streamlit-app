"""
Regulation Deduplication Module

This module provides functions to deduplicate regulations in compliance analysis results.
It can be used as a post-processing step before saving the results to a JSON file.
"""

import json
from pathlib import Path
import copy

def create_regulation_id(regulation):
    """
    Create a unique identifier for a regulation based on its key attributes.
    
    Args:
        regulation (dict): Regulation dictionary
        
    Returns:
        tuple: Unique identifier tuple
    """
    return (
        str(regulation.get('regulation_number', '')),
        regulation.get('section_type', ''),
        regulation.get('source_name', '')
    )

def deduplicate_regulations_in_document(document_results):
    """
    Deduplicate regulations in a single document's compliance results.
    
    Args:
        document_results (dict): Document compliance results
        
    Returns:
        dict: Document compliance results with deduplicated regulations
    """
    if not document_results or 'detailed_results' not in document_results:
        return document_results
    
    # Create a deep copy to avoid modifying the original
    result_copy = copy.deepcopy(document_results)
    detailed_results = result_copy.get('detailed_results', [])
    
    # Track unique regulations by their ID
    unique_regulations = {}
    
    for result in detailed_results:
        reg_id = create_regulation_id(result)
        
        # If we haven't seen this regulation before, add it
        if reg_id not in unique_regulations:
            unique_regulations[reg_id] = result
        else:
            # If we've seen it before, merge evidence if possible
            existing = unique_regulations[reg_id]
            
            # Only merge if both have the same applicability
            if existing.get('applicability') == result.get('applicability'):
                # Merge evidence if available
                if (result.get('compliance_evidence') and 
                    result.get('compliance_evidence') != 'N/A' and
                    existing.get('compliance_evidence') and 
                    existing.get('compliance_evidence') != 'N/A'):
                    
                    # Combine evidence, avoiding duplicates
                    existing_evidence = existing.get('compliance_evidence', '').split('; ')
                    new_evidence = result.get('compliance_evidence', '').split('; ')
                    
                    # Remove empty strings
                    existing_evidence = [e for e in existing_evidence if e]
                    new_evidence = [e for e in new_evidence if e]
                    
                    # Combine and deduplicate
                    combined_evidence = list(set(existing_evidence + new_evidence))
                    existing['compliance_evidence'] = '; '.join(combined_evidence)
                
                # Merge evidence with page if available
                if (result.get('compliance_evidence_with_page') and 
                    result.get('compliance_evidence_with_page') != 'N/A' and
                    existing.get('compliance_evidence_with_page') and 
                    existing.get('compliance_evidence_with_page') != 'N/A'):
                    
                    # Combine evidence with page, avoiding duplicates
                    existing_evidence = existing.get('compliance_evidence_with_page', '').split('; ')
                    new_evidence = result.get('compliance_evidence_with_page', '').split('; ')
                    
                    # Remove empty strings
                    existing_evidence = [e for e in existing_evidence if e]
                    new_evidence = [e for e in new_evidence if e]
                    
                    # Combine and deduplicate
                    combined_evidence = list(set(existing_evidence + new_evidence))
                    existing['compliance_evidence_with_page'] = '; '.join(combined_evidence)
    
    # Update the detailed results with the unique regulations
    result_copy['detailed_results'] = list(unique_regulations.values())
    
    return result_copy

def deduplicate_regulations_in_results(analysis_results):
    """
    Deduplicate regulations in all documents' compliance results.
    
    Args:
        analysis_results (list): List of document compliance results
        
    Returns:
        list: Document compliance results with deduplicated regulations
    """
    if not analysis_results:
        return analysis_results
    
    # Process each document's results
    deduplicated_results = []
    
    for document_results in analysis_results:
        deduplicated_document = deduplicate_regulations_in_document(document_results)
        deduplicated_results.append(deduplicated_document)
    
    return deduplicated_results

def process_json_file(input_path, output_path=None):
    """
    Process a JSON file containing compliance analysis results to deduplicate regulations.
    
    Args:
        input_path (str): Path to the input JSON file
        output_path (str, optional): Path to save the deduplicated results. If None, will overwrite the input file.
        
    Returns:
        str: Path to the saved file
    """
    input_path = Path(input_path)
    
    if output_path is None:
        output_path = input_path
    else:
        output_path = Path(output_path)
    
    # Load the JSON file
    with open(input_path, 'r', encoding='utf-8') as f:
        analysis_results = json.load(f)
    
    # Deduplicate regulations
    deduplicated_results = deduplicate_regulations_in_results(analysis_results)
    
    # Save the deduplicated results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_results, f, indent=2, ensure_ascii=False)
    
    return str(output_path)

if __name__ == "__main__":
    # Example usage
    base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
    input_path = base_dir / "output" / "enhanced_document_analysis" / "compliance_analysis_results.json"
    
    # Process the file (will overwrite the original)
    output_path = process_json_file(input_path)
    print(f"Deduplicated regulations saved to {output_path}")
