"""
Test Enhanced Compliance Analyzer

This script tests the enhanced compliance analyzer with a single document
to verify the improvements to evidence collection and tracking.
"""

import json
from pathlib import Path
from enhanced_compliance_analyzer import EnhancedComplianceAnalyzer
from document_processor import DocumentProcessor

def main():
    # Define paths
    base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
    
    # Initialize the document processor and analyzer
    print("Initializing document processor and analyzer...")
    document_processor = DocumentProcessor(base_dir=base_dir)
    analyzer = EnhancedComplianceAnalyzer(base_dir=base_dir)
    
    # Process only the first document for testing
    print("Processing test document...")
    all_documents = document_processor.process_all_documents()
    test_document = all_documents[0] if all_documents else None
    
    if not test_document:
        print("No documents found to test!")
        return
    
    print(f"Testing with document: {test_document.get('metadata', {}).get('filename', 'Unknown')}")
    
    # Analyze the test document
    print("Analyzing test document...")
    result = analyzer.analyze_document_compliance(test_document)
    
    # Save the test result
    output_path = base_dir / "output" / "enhanced_document_analysis" / "test_result.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Test result saved to {output_path}")
    
    # Print model usage statistics
    print("\nModel Usage Statistics:")
    print(f"  Phase 1 (Claude 3.5 Sonnet): {result.get('model_usage', {}).get('claude_3_5_sonnet_phase1', 0)} calls")
    print(f"  Phase 2 (Claude 3.7 Sonnet): {result.get('model_usage', {}).get('claude_3_7_sonnet_phase2', 0)} calls")
    
    # Print chunk processing statistics if available
    chunk_stats = result.get('model_usage', {}).get('chunk_processing', {})
    if chunk_stats:
        print("\nChunk Processing Statistics:")
        print(f"  Total chunks processed: {chunk_stats.get('total_chunks_processed', 0)}")
        print(f"  Additional evidence found: {chunk_stats.get('additional_evidence_found', 0)}")
    else:
        print("\nNo chunk processing statistics available")
    
    # Check for evidence with page numbers
    detailed_results = result.get('detailed_results', [])
    evidence_with_page_count = sum(1 for r in detailed_results if 'compliance_evidence_with_page' in r)
    
    print(f"\nDetailed results count: {len(detailed_results)}")
    print(f"Results with page-referenced evidence: {evidence_with_page_count}")
    
    if evidence_with_page_count > 0:
        print("\nExample of evidence with page references:")
        for r in detailed_results:
            if 'compliance_evidence_with_page' in r:
                print(f"  Regulation {r.get('regulation_number', 'Unknown')}:")
                print(f"  {r.get('compliance_evidence_with_page', 'N/A')[:200]}...")
                break

if __name__ == "__main__":
    main()
