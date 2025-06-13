# Regulatory Analysis Tools

This directory contains tools for analyzing the applicability of Central Bank regulations (Section 17A and Section 48) to a specific company and generating strategic summaries based on the analysis.

## Components

### 1. Regulation Applicability Analyzer (`regulation_applicability_analyzer.py`)

**Purpose**: Analyzes a client's annual report against the combined Central Bank regulations to determine which regulations apply to the specific company.

**Features**:
- Extracts text from client annual reports (PDF format)
- Uses Claude 3.7 Sonnet via OpenRouter API for intelligent analysis
- Determines applicability of each regulation with reasoning and confidence score
- Generates a detailed Word document summarizing applicable regulations
- Saves analyzed regulations in JSON format for further processing

### 2. High-Level Summary Generator (`high_level_summary_generator.py`)

**Purpose**: Creates an executive-friendly strategic summary of regulatory analysis results, designed specifically for SME and leadership teams.

**Features**:
- Generates a professionally formatted Word document with executive insights
- Provides thematic analysis grouping regulations into strategic business areas
- Includes risk assessment with prioritized regulatory risks and mitigation strategies
- Delivers a phased strategic action plan with clear implementation timelines
- Presents data in visually appealing tables with color-coded sections
- Includes comprehensive appendices with statistics, methodology, and glossary
- Implements a caching system to reduce API costs and improve performance
- Automatically categorizes regulations by applicability status
- Calculates overall compliance posture rating (Low/Moderate/High Regulatory Exposure)
- Creates a visually intuitive implementation timeline with color-coding

## Requirements

The following Python libraries are required:
- PyPDF2 (for PDF text extraction)
- requests (for API calls)
- python-docx (for generating Word documents)
- tqdm (for progress bars)
- hashlib, json, os, pathlib (standard libraries)

You can install the required libraries using pip:
```
pip install PyPDF2 requests python-docx tqdm
```

The OpenRouter API key for Claude 3.7 Sonnet is already included in the scripts.

## Usage

### 1. Regulation Applicability Analyzer

To analyze the applicability of regulations to a specific company:

```bash
python regulation_applicability_analyzer.py --annual_report_path "path/to/annual_report.pdf" --output_dir "path/to/output_directory"
```

Options:
- `--annual_report_path`: Path to the client's annual report PDF file (required)
- `--output_dir`: Directory where output files will be saved (default: "output/regulations_applicable")
- `--regulations_path`: Path to the combined regulations JSON file (default: "output/Data_extraction/regulation_17A_48_combined.json")
- `--api_key`: OpenRouter API key (default: uses the key defined in the script)

### 2. High-Level Summary Generator

To generate a high-level executive summary of the regulatory analysis:

```bash
python high_level_summary_generator.py --analyzed_regulations_path "path/to/analyzed_regulations.json" --output_dir "path/to/output_directory"
```

Options:
- `--analyzed_regulations_path`: Path to the analyzed regulations JSON file (default: "output/regulations_applicable/analyzed_regulations.json")
- `--output_dir`: Directory where output files will be saved (default: "output/regulations_applicable")
- `--api_key`: OpenRouter API key (default: uses the key defined in the script)

**Note for Leadership Teams**: The high-level summary generator is specifically designed for executive audiences, providing strategic insights rather than technical details. The output document includes professional formatting with tables, color-coding, and visual elements to enhance readability and decision-making.

## Output Files

All output files are saved in the `output/regulations_applicable/` directory:

1. `analyzed_regulations.json`: Raw analysis data for each regulation
2. `regulation_applicability_summary.docx`: Detailed regulation-by-regulation summary
3. `regulatory_strategic_summary.docx`: High-level strategic summary
4. `cache/`: Directory containing cached API responses for efficiency

## Input Files
1. **Client Annual Report**: Place the client's annual report PDF in the `Input/Client Annual Report` folder.
2. **Regulations Data**: The analyzer uses the combined regulations JSON file from `output/Data_extraction/regulation_17A_48_combined.json`.

## How to Use
1. Place the client's annual report PDF in the `Input/Client Annual Report` folder.

2. Run the analyzer:
   ```
   python regulation_applicability_analyzer.py
   ```

3. The analyzer will:
   - Extract text from the client's annual report
   - Load the combined regulations
   - Analyze each regulation against the annual report using Claude 3.7 Sonnet
   - Generate enhanced JSON with applicability information
   - Create a summary Word document

## How It Works
1. The analyzer extracts text from the client's annual report PDF.
2. It loads the combined regulations JSON file.
3. For each regulation, it constructs a prompt for Claude 3.7 Sonnet that includes:
   - The regulation details
   - Context about the CPC Regulations
   - Relevant portions of the client's annual report
4. Claude analyzes whether the regulation applies to the company based on the annual report.
5. The results are compiled into an enhanced JSON file and a summary Word document.

## Note on API Usage
This tool makes API calls to OpenRouter for each regulation, which can result in significant API usage for large regulation sets. Consider implementing batching or sampling strategies for initial testing.
