# Data Extraction Module

## Requirements
The following Python libraries are required to run the extraction scripts:
- PyPDF2 (for PDF text extraction)
- re (Regular expressions, part of Python standard library)
- json (JSON handling, part of Python standard library)
- os (Operating system interface, part of Python standard library)
- pathlib (Object-oriented filesystem paths, part of Python standard library)

You can install the required external libraries using pip:
```
pip install PyPDF2
```

## What it is doing?
This module extracts regulation data from PDF documents related to the Central Bank regulations:
1. Section 17A regulations from the Central Bank Reform Act 2010
2. Section 48 regulations from the Central Bank (Supervision and Enforcement) Act 2013

The extraction process:
1. Extracts the structure (parts, chapters, regulation numbers and titles) from the PDF documents
2. Extracts the full text of each regulation
3. Combines the structure and text data
4. Standardizes the data format across both section types
5. Merges both datasets into a single JSON file with consistent field names

The standardized fields include:
- Source Name
- Section Type (17A or 48)
- Part Number
- Part Name
- Chapter Number
- Chapter Name
- Regulation Number
- Regulation Title
- Regulation Text

## What to run?
To extract and combine the regulation data, run:
```
python combined_extractor.py
```

This script will process both Section 17A and Section 48 documents and generate three JSON files:
1. section_17a_combined.json - Contains only Section 17A regulations
2. section_48_combined.json - Contains only Section 48 regulations
3. regulation_17A_48_combined.json - Contains both Section 17A and Section 48 regulations with standardized fields

## Output to use
The main output file to use for further analysis is:
```
regulation_17A_48_combined.json
```

This file contains all regulations from both Section 17A and Section 48 with a standardized schema, making it easier to analyze and compare regulations across both sections while maintaining all the hierarchical structure information from the original documents.
