"""
Compliance Analysis Pipeline

This script implements a complete pipeline for compliance analysis:
1. Document Validation: Check if documents are relevant for CPC regulation comparison
2. Compliance Analysis: Analyze relevant documents against CPC regulations
3. Excel Conversion: Convert JSON results to Excel for reporting

Usage:
    python compliance_pipeline.py [--skip-validation] [--clean-cache]
"""

import os
import json
import argparse
from pathlib import Path
from tqdm import tqdm

import sys
from enhanced_client_document_analyzer.document_processor import DocumentProcessor
from enhanced_client_document_analyzer.document_validator import DocumentValidator
from enhanced_client_document_analyzer.enhanced_compliance_analyzer import EnhancedComplianceAnalyzer
from enhanced_client_document_analyzer.convert_json_to_excel import convert_json_to_excel
from enhanced_client_document_analyzer.consolidated_report_generator import generate_consolidated_report

def clear_cache_directory(cache_dir):
    """
    Clear the cache directory to force fresh API calls.
    
    Args:
        cache_dir (Path): Path to the cache directory
    """
    print(f"Clearing cache directory: {cache_dir}")
    for cache_file in cache_dir.glob("*.json"):
        os.remove(cache_file)
    print("Cache cleared successfully")

def get_base_dir():
    """
    Get the base directory for the project.
    
    Returns:
        Path: Base directory path
    """
    # Get the directory where the script is running
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    return script_dir

def run_compliance_pipeline(skip_validation=False, clean_cache=False):
    """
    Run the complete compliance analysis pipeline.
    
    Args:
        skip_validation (bool): Whether to skip document validation
        clean_cache (bool): Whether to clean the cache before running
        
    Returns:
        tuple: (Path to JSON results, Path to Excel file, Path to consolidated Excel file)
    """
    # Initialize components
    base_dir = get_base_dir()
    document_processor = DocumentProcessor(base_dir=base_dir)
    document_validator = DocumentValidator(base_dir=base_dir)
    compliance_analyzer = EnhancedComplianceAnalyzer(base_dir=base_dir)
    
    # Clear cache if requested
    if clean_cache:
        cache_dir = base_dir / "output" / "enhanced_document_analysis" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        clear_cache_directory(cache_dir)
    
    # Step 1: Process all documents
    print("\n=== Step 1: Processing Documents ===")
    documents = document_processor.process_all_documents()
    print(f"Processed {len(documents)} documents")
    
    # Step 2: Validate documents (if not skipped)
    relevant_documents = []
    if not skip_validation:
        print("\n=== Step 2: Validating Documents ===")
        for doc in tqdm(documents, desc="Validating documents"):
            doc_name = doc.get('metadata', {}).get('filename', 'Unknown Document')
            validation_result = document_validator.validate_document(doc)
            
            if validation_result["is_relevant"]:
                print(f"✅ {doc_name}: Relevant - {validation_result['reason']}")
                relevant_documents.append(doc)
            else:
                print(f"❌ {doc_name}: Not relevant - {validation_result['reason']}")
                
        # Save validation results
        validation_results_path = base_dir / "output" / "enhanced_document_analysis" / "document_validation_results.json"
        validation_results = [
            {
                "document_name": doc.get('metadata', {}).get('filename', 'Unknown'),
                "is_relevant": doc in relevant_documents
            }
            for doc in documents
        ]
        with open(validation_results_path, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2)
    else:
        print("\n=== Step 2: Validation Skipped ===")
        relevant_documents = documents
    
    print(f"\nFound {len(relevant_documents)} relevant documents for compliance analysis")
    
    # Step 3: Analyze compliance for relevant documents
    json_path = None
    excel_path = None
    consolidated_excel_path = None
    
    if relevant_documents:
        print("\n=== Step 3: Analyzing Compliance ===")
        analysis_results = compliance_analyzer.analyze_all_documents(relevant_documents)
        
        # Step 4: Save results to JSON
        json_path = compliance_analyzer.save_analysis_results(analysis_results)
        print(f"Saved compliance analysis results to {json_path}")
        
        # Step 5: Convert JSON to Excel
        print("\n=== Step 5: Converting to Excel ===")
        excel_path = convert_json_to_excel()
        print(f"Excel report generated successfully at {excel_path}")
        
        # Step 6: Generate consolidated report
        print("\n=== Step 6: Generating Consolidated Report ===")
        try:
            from enhanced_client_document_analyzer.consolidated_report_generator import generate_consolidated_report
            consolidated_excel_path = generate_consolidated_report()
            print(f"Consolidated report generated successfully at {consolidated_excel_path}")
        except Exception as e:
            print(f"Warning: Could not generate consolidated report: {str(e)}")
        
        print("\n=== Analysis Complete ===")
        return json_path, excel_path, consolidated_excel_path
    else:
        print("No relevant documents found. Skipping compliance analysis.")
        print("\n=== Analysis Complete ===")
        return None, None, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the compliance analysis pipeline")
    parser.add_argument("--skip-validation", action="store_true", help="Skip document validation")
    parser.add_argument("--clean-cache", action="store_true", help="Clean cache before running")
    args = parser.parse_args()
    
    json_path, excel_path, consolidated_excel_path = run_compliance_pipeline(
        skip_validation=args.skip_validation,
        clean_cache=args.clean_cache
    )
    
    if json_path and excel_path:
        print("\n=== Pipeline Completed Successfully ===")
        print(f"JSON results: {json_path}")
        print(f"Excel report: {excel_path}")
        if consolidated_excel_path:
            print(f"Consolidated report: {consolidated_excel_path}")
    else:
        print("\n=== Pipeline Completed - No Results Generated ===")
