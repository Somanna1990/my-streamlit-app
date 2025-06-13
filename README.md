# CPC AIB Life - Compliance Analysis System

## Project Overview

This project provides an AI-powered compliance analysis system for financial services documents. It analyzes client documents against the Central Bank of Ireland's CPC regulations (Section 17A and Section 48) to determine compliance status, identify gaps, and provide recommendations.

The system uses a multi-phase approach with Claude AI models to efficiently analyze documents:
1. **Document Validation**: Determines if documents are relevant for CPC regulation comparison
2. **Compliance Analysis**: Analyzes relevant documents against applicable regulations using a two-phase approach:
   - Phase 1: Quick applicability check for all regulations
   - Phase 2: Detailed compliance analysis only for applicable regulations
3. **Results Processing**: Deduplicates and consolidates findings
4. **Reporting**: Converts analysis results to Excel and generates consolidated reports

## Directory Structure

```
CPC_AIB_Life/
├── compliance_pipeline.py         # Main pipeline script that orchestrates the entire workflow
├── Input/                         # Input directories for documents and regulations
│   ├── 17A/                       # Section 17A regulation documents
│   ├── Section-48/                # Section 48 regulation documents
│   ├── Compliance Documents/      # Client documents to be analyzed
│   ├── Guidance Document/         # Guidance documents for regulations
│   └── Client Annual Report/      # Client annual reports
├── enhanced_client_document_analyzer/  # Main package for compliance analysis
│   ├── document_processor.py      # Processes and extracts text from documents
│   ├── document_validator.py      # Validates document relevance for CPC regulations
│   ├── enhanced_compliance_analyzer.py # Core compliance analysis functionality
│   ├── deduplicate_regulations.py # Deduplicates regulation results
│   ├── convert_json_to_excel.py   # Converts JSON results to Excel
│   ├── consolidated_report_generator.py # Generates consolidated compliance reports
│   ├── skip_regulations.json      # Configuration for regulations to skip
│   └── test_enhanced_analyzer.py  # Test script for the analyzer
├── Data_Extraction/               # Tools for extracting regulation data
│   ├── 17A_Section/               # Section 17A extraction tools
│   ├── 48_Section/                # Section 48 extraction tools
│   └── Guidance_Section/          # Guidance document extraction tools
└── output/                        # Output directories for results
    ├── enhanced_document_analysis/ # Enhanced compliance analysis results
    │   ├── cache/                 # Cache for API responses
    │   ├── compliance_analysis_results.json # Raw analysis results
    │   ├── compliance_analysis_report.xlsx  # Excel report
    │   └── consolidated_compliance_report.json/xlsx # Consolidated reports
    ├── Data_extraction/           # Extracted regulation data
    └── Guidance/                  # Extracted guidance information
```

## Installation Requirements

### Required Python Packages

Create a `requirements.txt` file with the following dependencies:

```
requests==2.31.0
tqdm==4.66.1
pandas==2.0.3
openpyxl==3.1.2
PyMuPDF==1.23.3  # fitz
pathlib==1.0.1
```

Install the requirements using:

```bash
pip install -r requirements.txt
```

## Setup Instructions

1. **Clone/Download the Repository**:
   - Place the project in a directory of your choice

2. **Update Base Directory Paths**:
   - The project currently uses hardcoded paths: `C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life`
   - Update these paths in the following files to match your environment:
     - `enhanced_client_document_analyzer/document_processor.py`
     - `enhanced_client_document_analyzer/document_validator.py`
     - `enhanced_client_document_analyzer/enhanced_compliance_analyzer.py`
     - `enhanced_client_document_analyzer/convert_json_to_excel.py`
     - `compliance_pipeline.py`

3. **API Key Configuration**:
   - The project uses OpenRouter API to access Claude AI models
   - Update the API key in `enhanced_compliance_analyzer.py` and `document_validator.py`
   - Current key: `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`
   - For security, consider moving this to an environment variable

4. **Prepare Input Documents**:
   - Place client documents to be analyzed in `Input/Compliance Documents/`
   - Ensure regulation documents are in their respective folders:
     - Section 17A: `Input/17A/`
     - Section 48: `Input/Section-48/`

## Usage Guide

### Getting Started (For Beginners)

1. **Place Your Documents**:
   - Put all documents you want to analyze in the `Input/Compliance Documents/` folder

2. **Run the Compliance Pipeline**:
   - Open a command prompt or PowerShell window
   - Navigate to the project directory: `cd path\to\CPC_AIB_Life`
   - Run the pipeline: `python compliance_pipeline.py`

3. **View Results**:
   - Excel report: `output\enhanced_document_analysis\compliance_analysis_report.xlsx`
   - Consolidated report: `output\enhanced_document_analysis\consolidated_compliance_report.xlsx`

### Command-Line Options

The compliance pipeline supports several command-line options:

```bash
# Run full pipeline with document validation (default)
python compliance_pipeline.py

# Skip document validation (analyze all documents)
python compliance_pipeline.py --skip-validation

# Clean cache before running (force fresh API calls)
python compliance_pipeline.py --clean-cache

# Use both options together
python compliance_pipeline.py --skip-validation --clean-cache
```

### Step-by-Step Workflow

1. **Document Processing**:
   - The system extracts text from all documents in the input folder
   - Each document is processed to maintain page references

2. **Document Validation** (optional):
   - Each document is analyzed to determine if it's relevant for CPC regulation comparison
   - Documents deemed irrelevant are skipped in the compliance analysis
   - Use `--skip-validation` to analyze all documents regardless of relevance

3. **Compliance Analysis**:
   - Each relevant document is analyzed against applicable CPC regulations
   - Two-phase approach:
     - Phase 1: Quick applicability check for all regulations
     - Phase 2: Detailed compliance analysis only for applicable regulations

4. **Results Generation**:
   - JSON results: Detailed compliance analysis data
   - Excel report: Formatted spreadsheet for easy review

### Generating Consolidated Reports

After running the compliance pipeline, you can generate a consolidated report:

```bash
# Navigate to the project directory
cd path\to\CPC_AIB_Life

# Run the consolidated report generator
python -c "from enhanced_client_document_analyzer.consolidated_report_generator import generate_consolidated_report; generate_consolidated_report()"
```

The consolidated report provides:
- Summary of compliance across all documents
- Prioritized list of regulations with compliance gaps
- Detailed gap descriptions and recommendations
- Excel format for easy review

## System Components in Detail

### 1. Compliance Pipeline (`compliance_pipeline.py`)

**Purpose**: Orchestrates the entire workflow from document processing to report generation.

**What It Does**:
- Processes all documents in the input directory
- Validates documents for relevance (optional)
- Analyzes compliance of relevant documents
- Generates reports in JSON and Excel formats

**How to Use It**:
```bash
python compliance_pipeline.py [--skip-validation] [--clean-cache]
```

### 2. Document Processor

**Purpose**: Extract text from PDF documents and prepare them for analysis.

**What It Does**:
- Reads PDF files from the input directory
- Extracts text while maintaining page references
- Creates structured document objects for analysis

### 3. Document Validator

**Purpose**: Determine if documents are relevant for CPC regulation comparison.

**What It Does**:
- Analyzes document content to determine relevance
- Uses AI to identify documents that should be analyzed for compliance
- Skips irrelevant documents to save processing time

### 4. Enhanced Compliance Analyzer

**Purpose**: Analyze documents against CPC regulations to determine compliance.

**How It Works**:
- **Phase 1**: Quick applicability check for all regulations
  - Determines which regulations apply to each document
  - Filters out non-applicable regulations to save processing time
- **Phase 2**: Detailed compliance analysis only for applicable regulations
  - Analyzes document chunks to gather comprehensive evidence
  - Determines compliance status (Yes, Partial, No)
  - Identifies gaps and provides recommendations

### 5. Consolidated Report Generator

**Purpose**: Create a consolidated view of compliance across all documents.

**What It Does**:
- Groups compliance results by regulation
- Summarizes gaps and recommendations using AI
- Prioritizes regulations based on compliance status
- Generates both JSON and Excel reports

## Output Files and Reports

### Main Reports

1. **Detailed Excel Report**:
   - **Path**: `output\enhanced_document_analysis\compliance_analysis_report.xlsx`
   - **Contents**: Document-by-document compliance analysis with all regulations
   - **When to Use**: When you need to see detailed compliance status for each document

2. **Consolidated Compliance Report**:
   - **Path**: `output\enhanced_document_analysis\consolidated_compliance_report.xlsx`
   - **Contents**: Summarized view across all documents, prioritized by compliance gaps
   - **When to Use**: For a high-level overview and prioritized action plan

3. **JSON Results** (for advanced users):
   - **Path**: `output\enhanced_document_analysis\compliance_analysis_results.json`
   - **Contents**: Raw data from the compliance analysis
   - **When to Use**: For data processing or custom report generation

## How the System Works

### AI Models

The system uses Claude AI models via OpenRouter API:

- **Phase 1 (Applicability Check)**: Claude 3.5 Sonnet
  - Quickly determines which regulations apply to each document
  - Reduces processing time by filtering out non-applicable regulations

- **Phase 2 (Detailed Analysis)**: Claude 3.7 Sonnet
  - Performs in-depth compliance analysis on applicable regulations
  - Provides detailed reasoning, gap descriptions, and recommendations

### Cache System

To improve performance and reduce API costs, the system caches results:

- **Location**: `output\enhanced_document_analysis\cache\`
- **Purpose**: Avoids redundant API calls for the same document-regulation pairs
- **Clearing Cache**: Use `python compliance_pipeline.py --clean-cache` when you want fresh results

## Troubleshooting Guide

### Common Issues and Solutions

1. **"ModuleNotFoundError" when running scripts**
   - **Solution**: Run `pip install -r requirements.txt` to install missing packages

2. **Analysis taking too long**
   - **Solution**: Use `--skip-validation` to analyze only the most relevant documents
   - **Solution**: Check if the API key has usage limits or try processing fewer documents

3. **Path errors**
   - **Solution**: Update the base directory paths in the code to match your environment
   - **Solution**: Ensure all required directories exist (Input, output, etc.)

4. **Memory issues with large documents**
   - **Solution**: Process fewer documents at a time
   - **Solution**: Split very large PDF files into smaller parts

### Quick Fixes

- **Restart from scratch**: Delete the cache directory and run with `--clean-cache`
- **Test with a single document**: Copy just one document to the input folder for testing
- **Check API key**: Verify the OpenRouter API key in the code files is valid

## Security Best Practices

- **API Keys**: The current implementation has hardcoded API keys. For production use, consider moving these to environment variables.
- **Document Confidentiality**: Be aware that document content is sent to external AI models. Ensure this complies with your data protection policies.

## Getting Help

If you encounter issues not covered in this guide, please contact the project maintainer.

---

*This README was last updated on June 10, 2025*
