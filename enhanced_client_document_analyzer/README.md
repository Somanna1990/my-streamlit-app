# Enhanced Client Document Analyzer

This package provides an enhanced version of the client document analyzer with a two-phase approach for faster and more efficient compliance analysis while maintaining the exact same output format.

## Key Features

- **Two-Phase Analysis**: Implements a two-stage approach to significantly reduce API calls and processing time
  - **Phase 1**: Quick applicability check for all regulations
  - **Phase 2**: Detailed compliance analysis only for applicable regulations
- **Parallel Processing**: Efficiently processes multiple regulations simultaneously
- **Efficient Caching**: Avoids redundant API calls by caching both Phase 1 and Phase 2 results
- **Identical Output Format**: Maintains the exact same output format as the original client document analyzer

## Performance Benefits

- **Reduced API Calls**: Only performs detailed analysis on applicable regulations (typically 80-90% reduction)
- **Faster Processing**: Significantly reduces overall processing time
- **Resource Efficient**: Reduces computational resources and API costs
- **Detailed Output**: Maintains the same comprehensive output format

## Usage

```bash
# Basic usage
python run_analyzer.py

# Analyze a specific document
python run_analyzer.py --document "Executive Committee ToR"

# Use parallel processing with 4 worker threads
python run_analyzer.py --parallel --workers 4
```

## Components

1. **Document Processor**: Extracts text from client documents
2. **Document Validator**: Determines if documents are relevant for CPC regulation comparison
3. **Regulation Summarizer**: Generates summaries and guidance mapping
4. **Enhanced Compliance Analyzer**: Implements the two-phase approach for efficient analysis
5. **Main Module**: Orchestrates the entire analysis process

## Output

The analyzer generates the following output files in the `output/enhanced_document_analysis` directory:

- `regulation_summaries.json`: Summaries of all regulations
- `guidance_map.json`: Mapping of regulations to guidance items
- `document_validation_results.json`: Results of document validation
- `compliance_analysis_results.json`: Detailed compliance analysis results
- `enhanced_document_analysis_report.json`: Final report with overall statistics

## Model Usage

The analyzer uses Claude 3.7 Sonnet for both phases:
- **Phase 1**: Streamlined prompt for quick applicability check
- **Phase 2**: Comprehensive prompt for detailed compliance analysis (only for applicable regulations)
