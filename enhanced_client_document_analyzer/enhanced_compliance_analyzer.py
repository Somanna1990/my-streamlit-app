"""
Enhanced Compliance Analyzer Module

This module analyzes client documents against applicable CPC regulations to determine compliance.
It uses a two-phase approach with different Claude models for faster and more efficient analysis:
1. Phase 1: Quick applicability check for all regulations using Claude 3.5 Sonnet (full document analysis)
2. Phase 2: Detailed compliance analysis only for applicable regulations using Claude 3.7 Sonnet with document chunking

Key features:
- Full document analysis in Phase 1 to improve applicability determination
- Document chunking in Phase 2 to gather comprehensive evidence from throughout the document
- Detailed compliance reasoning for each regulation
- Multiple evidence collection with page references
"""

import os
import json
import requests
import hashlib
import concurrent.futures
from pathlib import Path
import time
from tqdm import tqdm
from .deduplicate_regulations import deduplicate_regulations_in_results

class EnhancedComplianceAnalyzer:
    def __init__(self, api_key="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", base_dir=None):
        """
        Initialize the enhanced compliance analyzer.
        
        Args:
            api_key (str): OpenRouter API key. Default is the provided key.
            base_dir (Path, optional): Base directory path. If None, will use default.
        """
        self.api_key = api_key
        
        if base_dir is None:
            self.base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
        else:
            self.base_dir = Path(base_dir)
            
        self.regulations_path = self.base_dir / "output" / "Data_extraction" / "regulation_17A_48_combined.json"
        self.guidance_path = self.base_dir / "output" / "Guidance" / "combined_guidance.json"
        self.output_dir = self.base_dir / "output" / "enhanced_document_analysis"
        self.cache_dir = self.output_dir / "cache"
        self.skip_regulations_path = Path(__file__).parent / "skip_regulations.json"
        
        # Ensure output and cache directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load skip regulations configuration
        self.skip_regulations = self.load_skip_regulations()
    
    def load_skip_regulations(self):
        """
        Load the skip regulations configuration from JSON file.
        
        Returns:
            dict: Dictionary with section types as keys and lists of regulation numbers to skip as values
        """
        default_config = {"17A": [], "48": []}
        
        try:
            if self.skip_regulations_path.exists():
                try:
                    with open(self.skip_regulations_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        # Print first 100 characters for debugging
                        print(f"First 100 chars of skip_regulations.json: {file_content[:100]}...")
                        try:
                            config = json.loads(file_content)
                            # Ensure both sections exist
                            if "17A" not in config:
                                config["17A"] = []
                            if "48" not in config:
                                config["48"] = []
                            
                            # Ensure all regulation numbers are integers for consistent comparison
                            for section in config:
                                config[section] = [int(reg) if isinstance(reg, (int, str)) and str(reg).isdigit() else reg 
                                                  for reg in config[section]]
                            
                            return config
                        except json.JSONDecodeError as je:
                            print(f"JSON parsing error in skip_regulations.json: {str(je)}")
                            print("Please check the file format and ensure it is valid JSON.")
                            print("Using default configuration (no regulations skipped).")
                            return default_config
                except Exception as e:
                    print(f"Error reading skip_regulations.json: {str(e)}")
                    return default_config
            else:
                print(f"Skip regulations file not found at {self.skip_regulations_path}. No regulations will be skipped.")
                return default_config
        except Exception as e:
            print(f"Unexpected error loading skip regulations configuration: {str(e)}. No regulations will be skipped.")
            return default_config
    
    def load_regulations(self):
        """
        Load the combined regulations JSON file.
        
        Returns:
            list: List of regulation dictionaries
        """
        try:
            with open(self.regulations_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading regulations: {str(e)}")
            return []
    
    def load_guidance(self):
        """
        Load the combined guidance JSON file.
        
        Returns:
            list: List of guidance dictionaries
        """
        try:
            with open(self.guidance_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading guidance: {str(e)}")
            return []
    
    def get_cache_key(self, document_name, regulation_number, phase, prompt=None):
        """
        Generate a unique cache key for a compliance analysis prompt.
        
        Args:
            document_name (str): Name of the document
            regulation_number: Regulation number
            phase (int): Analysis phase (1 or 2)
            prompt (str, optional): The prompt sent to the API
            
        Returns:
            str: Cache key
        """
        if prompt:
            content = f"{document_name}:{regulation_number}:phase{phase}:{prompt}"
        else:
            content = f"{document_name}:{regulation_number}:phase{phase}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def check_cache(self, cache_key):
        """
        Check if a response is cached.
        
        Args:
            cache_key (str): Cache key
            
        Returns:
            dict or None: Cached response or None if not found
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_to_cache(self, cache_key, response):
        """
        Save a response to the cache.
        
        Args:
            cache_key (str): Cache key
            response (dict): Response to cache
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
    
    def filter_applicable_regulations(self, document):
        """
        Filter regulations that are applicable to the document using Phase 1 analysis.
        
        Args:
            document (dict): Document dictionary with metadata and text
            
        Returns:
            list: List of applicable regulations with their Phase 1 results
        """
        document_name = document.get('metadata', {}).get('filename', 'Unknown Document')
        document_text = document.get('full_text', '')
        
        # Load all regulations
        regulations = self.load_regulations()
        print(f"Phase 1: Screening {len(regulations)} regulations for applicability")
        
        # Debug: Print skip configuration
        print(f"Skip configuration loaded: {self.skip_regulations}")
        if any(len(regs) > 0 for regs in self.skip_regulations.values()):
            print("Skip regulations configuration:")
            for section_type, reg_numbers in self.skip_regulations.items():
                if reg_numbers:
                    print(f"  Section {section_type}: {', '.join(map(str, reg_numbers[:10]))}{'...' if len(reg_numbers) > 10 else ''}")
                    print(f"  Total regulations to skip in section {section_type}: {len(reg_numbers)}")
        
        # Filter out regulations that should be skipped
        regulations_to_process = []
        skipped_count = 0
        
        for reg in regulations:
            reg_number = reg.get('Regulation Number', '')
            section_type = reg.get('Section Type', '')
            
            # Check if this regulation should be skipped
            should_skip = False
            if section_type in self.skip_regulations:
                # Regulation number could already be an integer in the data
                if isinstance(reg_number, int) and reg_number in self.skip_regulations[section_type]:
                    should_skip = True
                    skipped_count += 1
                    print(f"Skipping regulation {section_type}-{reg_number} (direct integer match)")
                else:
                    # Try converting to integer if it's not already an int
                    try:
                        reg_number_int = int(reg_number) if reg_number else 0
                        if reg_number_int in self.skip_regulations[section_type]:
                            should_skip = True
                            skipped_count += 1
                            print(f"Skipping regulation {section_type}-{reg_number} (converted to integer {reg_number_int})")
                    except (ValueError, TypeError):
                        # If regulation number can't be converted to int, use string comparison
                        if str(reg_number) in map(str, self.skip_regulations[section_type]):
                            should_skip = True
                            skipped_count += 1
                            print(f"Skipping regulation {section_type}-{reg_number} (matched as string)")
            
            if not should_skip:
                regulations_to_process.append(reg)
        
        if skipped_count > 0:
            print(f"Skipped {skipped_count} regulations based on skip configuration")
        else:
            print("WARNING: No regulations were skipped despite skip configuration being present!")
        
        # Process regulations in parallel for Phase 1
        applicable_regulations = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_reg = {
                executor.submit(self.check_regulation_applicability, document, reg): reg 
                for reg in regulations_to_process
            }
            
            for future in tqdm(concurrent.futures.as_completed(future_to_reg), 
                              total=len(regulations_to_process),
                              desc="Screening regulations"):
                reg = future_to_reg[future]
                try:
                    result = future.result()
                    # More conservative filtering: include regulations that apply, may apply, or have low confidence
                    if result and (result.get('applicability') in ['Applies', 'May Apply - Requires Further Review'] or 
                                  (result.get('applicability') == 'Does Not Apply' and 
                                   result.get('confidence_score', 'High') != 'High')):
                        applicable_regulations.append((reg, result))
                except Exception as e:
                    print(f"Error checking applicability for regulation {reg.get('Regulation Number', '')}: {str(e)}")
        
        print(f"Found {len(applicable_regulations)} applicable regulations out of {len(regulations_to_process)}")
        return applicable_regulations
    
    def check_regulation_applicability(self, document, regulation):
        """
        Quickly check if a regulation is applicable to the document (Phase 1).
        Uses a streamlined prompt with Claude 3.5 Sonnet to analyze the full document.
        
        Args:
            document (dict): Document dictionary with metadata and text
            regulation (dict): Regulation dictionary
            
        Returns:
            dict: Phase 1 analysis result with applicability determination and reasoning
        """
        # Extract document and regulation information
        document_name = document.get('metadata', {}).get('filename', 'Unknown Document')
        document_text = document.get('full_text', '')
        regulation_number = regulation.get('Regulation Number', '')
        regulation_title = regulation.get('Regulation Title', '')
        regulation_text = regulation.get('Regulation Text', '')
        section_type = regulation.get('Section Type', '')
        source_name = regulation.get('Source Name', '')
        
        # Check cache first
        cache_key = self.get_cache_key(document_name, regulation_number, 1)
        cached_result = self.check_cache(cache_key)
        if cached_result:
            print(f"Using cached Phase 1 result for Regulation {regulation_number}")
            return cached_result
        
        # No text truncation for Phase 1 since we're using Claude 3.5 Sonnet with larger context window
        # This ensures the entire document is considered for applicability determination
        
        # Enhanced prompt for Phase 1 applicability check with more context
        prompt = f"""
You are an expert financial regulations analyst. Your task is to determine if a specific CPC regulation applies to a client document.

# Document Information:
- Filename: {document_name}
- Document Text (excerpt):
```
{document_text}
```

# Regulation Details:
- Source: {source_name}
- Section Type: {section_type}
- Regulation Number: {regulation_number}
- Regulation Title: {regulation_title}
- Regulation Text: {regulation_text}

# Regulatory Context:
## CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025
These regulations set mandatory standards for businesses regulated by the Central Bank of Ireland, aiming to protect customers and ensure ethical conduct in financial services.

## CENTRAL BANK (SUPERVISION AND ENFORCEMENT) ACT 2013 (SECTION 48) (CONSUMER PROTECTION) REGULATIONS 2025
These are comprehensive consumer protection regulations for financial services, setting obligations for regulated entities when dealing with consumers, especially around transparency, suitability, and complaint handling.

Based on the document content and the regulation, determine if this regulation applies to this document.
Answer with EXACTLY ONE of these options:
- "Applies"
- "Does Not Apply"
- "May Apply - Requires Further Review"

Please provide a detailed explanation of why this regulation applies or does not apply to the document.

Format your response as a JSON object with these exact keys:
{{
  "applicability": "Applies/Does Not Apply/May Apply - Requires Further Review",
  "applicability_reasoning": "Detailed explanation of why this regulation applies or does not apply to the document",
  "confidence_score": "High/Medium/Low"
}}
"""
        
        # Make API call to Claude 3.5 Sonnet
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "anthropic/claude-3-5-sonnet",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,  # Low temperature for more deterministic responses
            "max_tokens": 500  # Increased to accommodate reasoning
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            # Extract the response content
            result = response.json()
            response_text = result["choices"][0]["message"]["content"]
            
            # Extract the JSON part from the response
            try:
                # Find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    phase1_result = json.loads(json_str)
                else:
                    # Fallback if JSON not found
                    phase1_result = {
                        "applicability": "May Apply - Requires Further Review",
                        "applicability_reasoning": "Unable to determine applicability due to JSON parsing issue. Defaulting to 'May Apply' for safety.",
                        "confidence_score": "Low"
                    }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                phase1_result = {
                    "applicability": "May Apply - Requires Further Review",
                    "applicability_reasoning": "Unable to determine applicability due to JSON parsing issue. Defaulting to 'May Apply' for safety.",
                    "confidence_score": "Low"
                }
            
            # Add regulation and document info to the result, including full regulation text
            phase1_result["regulation_number"] = regulation_number
            phase1_result["regulation_title"] = regulation_title
            phase1_result["regulation_text"] = regulation_text
            phase1_result["section_type"] = section_type
            phase1_result["source_name"] = source_name
            phase1_result["document_name"] = document_name
            
            # Save to cache
            self.save_to_cache(cache_key, phase1_result)
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
            return phase1_result
            
        except Exception as e:
            print(f"Error checking applicability for Regulation {regulation_number}: {str(e)}")
            # Return error information, including full regulation text
            error_result = {
                "regulation_number": regulation_number,
                "regulation_title": regulation_title,
                "regulation_text": regulation_text,
                "section_type": section_type,
                "source_name": source_name,
                "document_name": document_name,
                "applicability": "May Apply - Requires Further Review",
                "confidence_score": "Low"
            }
            return error_result
    
    def analyze_regulation_compliance(self, document, regulation, phase1_result=None, guidance_items=None):
        """
        Analyze compliance of a document with a specific regulation (Phase 2).
        
        Args:
            document (dict): Document dictionary with metadata and text
            regulation (dict): Regulation dictionary
            phase1_result (dict, optional): Result from Phase 1 analysis
            guidance_items (list, optional): List of guidance items for the regulation
            
        Returns:
            dict: Compliance analysis result
        """
        # Extract document and regulation information
        document_name = document.get('metadata', {}).get('filename', 'Unknown Document')
        document_text = document.get('full_text', '')
        pages_text = document.get('pages', [])
        regulation_number = regulation.get('Regulation Number', '')
        regulation_title = regulation.get('Regulation Title', '')
        regulation_text = regulation.get('Regulation Text', '')
        section_type = regulation.get('Section Type', '')
        source_name = regulation.get('Source Name', '')
        
        # Check cache first for Phase 2
        cache_key = self.get_cache_key(document_name, regulation_number, 2)
        cached_result = self.check_cache(cache_key)
        if cached_result:
            print(f"Using cached Phase 2 result for Regulation {regulation_number}")
            # Return cached result with zero chunk statistics since we're not processing chunks
            return cached_result, 0, 0
        
        # If we have a Phase 1 result and it says "Does Not Apply", return that without Phase 2 analysis
        if phase1_result and phase1_result.get('applicability') == 'Does Not Apply':
            # Get the reasoning from either applicability_reasoning or compliance_reasoning field
            reasoning = phase1_result.get('applicability_reasoning') or phase1_result.get('compliance_reasoning') or "No reasoning provided"
            
            result = {
                "regulation_number": regulation_number,
                "regulation_title": regulation_title,
                "regulation_text": regulation_text,
                "section_type": section_type,
                "source_name": source_name,
                "document_name": document_name,
                "applicability": "Does Not Apply",
                "applicability_reasoning": reasoning,  # Add the applicability reasoning from Phase 1
                "is_compliant": "N/A",
                "compliance_reasoning": reasoning,  # Keep the compliance reasoning for backward compatibility
                "compliance_evidence": "N/A",
                "evidence_page": "N/A",
                "compliance_evidence_with_page": "N/A",
                "gap_description": "N/A",
                "gap_recommendations": "N/A",
                "confidence_score": phase1_result.get('confidence_score', 'High')
            }
            # Return the result with zero chunk statistics since we're not processing chunks
            return result, 0, 0
        
        # Implement document chunking for comprehensive evidence collection
        # This allows us to analyze the entire document in manageable chunks
        chunk_size = 7000
        overlap = 500  # Overlap between chunks to avoid missing evidence that spans chunk boundaries
        
        # Create chunks with overlap
        if len(document_text) > chunk_size:
            chunks = []
            for i in range(0, len(document_text), chunk_size - overlap):
                end = min(i + chunk_size, len(document_text))
                chunks.append(document_text[i:end])
                if end == len(document_text):
                    break
            print(f"Document split into {len(chunks)} chunks for analysis")
        else:
            # If document is small enough, use it as a single chunk
            chunks = [document_text]
            
        # We'll use the first chunk for initial analysis, then gather additional evidence if needed
        document_text = chunks[0]
        
        # Prepare guidance text if available
        guidance_text = ""
        if guidance_items:
            guidance_text = "# Relevant Guidance:\n"
            for item in guidance_items[:3]:  # Limit to 3 guidance items to avoid token limits
                guidance_text += f"- {item.get('regulation_sub_section_number', '')}: {item.get('regulation_text', '')[:500]}\n\n"
        
        # Enhanced prompt for Phase 2 with more detailed regulatory context
        prompt = f"""
You are an expert financial regulations analyst. Your task is to determine if a client document complies with a specific CPC regulation.

# Document Information:
- Filename: {document_name}
- Document Text (excerpt):
```
{document_text}
```

# Regulation Details:
- Source: {source_name}
- Section Type: {section_type}
- Regulation Number: {regulation_number}
- Regulation Title: {regulation_title}
- Regulation Text: {regulation_text}

{guidance_text}

# Regulatory Context:
## CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025
These regulations set mandatory standards for businesses regulated by the Central Bank of Ireland, including:
- Securing customers' interests
- Acting honestly and with integrity
- Acting with due skill, care, and diligence
- Acting in customers' best interests and treating them fairly
- Communicating effectively
- Controlling risks of financial abuse
- Managing affairs sustainably and responsibly

## CENTRAL BANK (SUPERVISION AND ENFORCEMENT) ACT 2013 (SECTION 48) (CONSUMER PROTECTION) REGULATIONS 2025
These regulations focus on consumer protection requirements including:
- Knowing the consumer and assessing suitability
- Providing clear information and statements
- Handling complaints appropriately
- Special provisions for different financial sectors

Based on the document content and the regulation, determine:

1. Applicability: Does this regulation apply to this document? Answer with EXACTLY ONE of these options:
   - "Applies"
   - "Does Not Apply"
   - "May Apply - Requires Further Review"

2. If "Applies" or "May Apply", assess compliance:
   - Is the document compliant with this regulation?
   - If compliant, what EXACT text from the document demonstrates compliance? Include the exact quote.
   - If there's a gap, what is missing or inadequate?
   - What recommendations would you make to address any gaps?

Format your response as a JSON object with these exact keys:
{{
  "applicability": "Applies/Does Not Apply/May Apply - Requires Further Review",
  "is_compliant": "Yes/No/Partial",
  "compliance_reasoning": "Detailed explanation of why the document is or is not compliant with this regulation",
  "compliance_evidence": "EXACT text from the document that demonstrates compliance (if any)",
  "gap_description": "Description of any compliance gaps (if any)",
  "gap_recommendations": "Recommendations to address gaps (if any)",
  "confidence_score": "High/Medium/Low"
}}
"""
        
        # Make API call to Claude 3.7 Sonnet
        print(f"Analyzing compliance with Regulation {regulation_number} (Phase 2)...")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "anthropic/claude-3-7-sonnet",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,  # Low temperature for more deterministic responses
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            # Extract the response content
            result = response.json()
            response_text = result["choices"][0]["message"]["content"]
            
            # Extract the JSON part from the response
            try:
                # Find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    compliance_result = json.loads(json_str)
                else:
                    # Fallback if JSON not found
                    compliance_result = {
                        "applicability": "May Apply - Requires Further Review",
                        "is_compliant": "Partial",
                        "compliance_reasoning": "Unable to determine compliance reasoning due to parsing issues.",
                        "compliance_evidence": "",
                        "evidence_page": "N/A",
                        "compliance_evidence_with_page": "N/A",
                        "gap_description": "Could not parse response from AI",
                        "gap_recommendations": "Manual review required",
                        "confidence_score": "Low"
                    }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                compliance_result = {
                    "applicability": "May Apply - Requires Further Review",
                    "is_compliant": "Partial",
                    "compliance_reasoning": "Unable to determine compliance reasoning due to parsing issues.",
                    "compliance_evidence": "",
                    "evidence_page": "N/A",
                    "compliance_evidence_with_page": "N/A",
                    "gap_description": "Could not parse response from AI",
                    "gap_recommendations": "Manual review required",
                    "confidence_score": "Low"
                }
            
            # Find the page number for the compliance evidence if available
            evidence_page = 1  # Default to page 1 if we can't find a better match
            
            try:
                if compliance_result.get("compliance_evidence") and compliance_result.get("compliance_evidence") != "N/A":
                    evidence_text = compliance_result.get("compliance_evidence")
                    
                    # Try to find the page with the most matching words
                    if pages_text and len(pages_text) > 0:
                        # Get some key phrases from the evidence (at least 3 words long)
                        evidence_words = evidence_text.lower().split()
                        
                        if len(evidence_words) >= 3:
                            # Look for the first 3 words as a phrase
                            search_phrase = ' '.join(evidence_words[:3])
                            
                            for page in pages_text:
                                page_text = page.get("text", "").lower()
                                if search_phrase in page_text:
                                    evidence_page = page.get("page_number")
                                    break
            except Exception as e:
                print(f"Error finding evidence page: {str(e)}")
                # Continue with default page 1
            
            # Add regulation and document info to the result, including full regulation text
            compliance_result["regulation_number"] = regulation_number
            compliance_result["regulation_title"] = regulation_title
            compliance_result["regulation_text"] = regulation_text
            compliance_result["section_type"] = section_type
            compliance_result["source_name"] = source_name
            compliance_result["document_name"] = document_name
            
            # Always add evidence page (with N/A if not found)
            compliance_result["evidence_page"] = evidence_page
            
            # Process additional chunks if document is compliant or partially compliant and has multiple chunks
            all_evidence = []
            all_evidence_pages = []
            
            # Store the initial evidence if available
            initial_evidence = compliance_result.get("compliance_evidence")
            if initial_evidence and initial_evidence != "N/A" and evidence_page != "N/A":
                all_evidence.append(initial_evidence)
                all_evidence_pages.append(evidence_page)
            
            # Only process additional chunks if the document is compliant or partially compliant
            # and we have more than one chunk
            if (compliance_result.get("is_compliant") in ["Yes", "Partial"] and 
                len(chunks) > 1 and 
                initial_evidence and initial_evidence != "N/A"):
                
                print(f"Finding additional evidence in {len(chunks)-1} more chunks...")
                
                # Process each additional chunk to find more evidence
                for chunk_idx, chunk_text in enumerate(chunks[1:], 1):
                    # Create a modified prompt focused on finding additional evidence
                    additional_evidence_prompt = f"""
                    You are an expert financial regulations analyst. Your task is to find additional evidence of compliance with a specific regulation in this document chunk.
                    
                    # Document Information:
                    - Filename: {document_name}
                    - Document Chunk {chunk_idx+1} of {len(chunks)}:
                    ```
                    {chunk_text}
                    ```
                    
                    # Regulation Details:
                    - Source: {source_name}
                    - Section Type: {section_type}
                    - Regulation Number: {regulation_number}
                    - Regulation Title: {regulation_title}
                    - Regulation Text: {regulation_text}
                    
                    # Previous Compliance Finding:
                    This document has been found to be {compliance_result.get("is_compliant")} compliant with this regulation.
                    Previous evidence found: "{initial_evidence}"
                    
                    Your task is to find ADDITIONAL evidence of compliance in this chunk of the document.
                    If you find additional evidence, provide the EXACT text from this chunk that demonstrates compliance.
                    If you don't find additional evidence in this chunk, respond with "No additional evidence found".
                    
                    Format your response as a JSON object with this exact key:
                    {{
                      "additional_evidence": "EXACT text from this chunk that demonstrates compliance (if any)"
                    }}
                    """
                    
                    # Make API call to find additional evidence
                    try:
                        # Use the same API call setup but with the new prompt
                        chunk_data = {
                            "model": "anthropic/claude-3-7-sonnet",
                            "messages": [{"role": "user", "content": additional_evidence_prompt}],
                            "temperature": 0.1,
                            "max_tokens": 500
                        }
                        
                        chunk_response = requests.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json=chunk_data
                        )
                        chunk_response.raise_for_status()
                        
                        # Extract and parse the response
                        chunk_result = chunk_response.json()
                        chunk_text_response = chunk_result["choices"][0]["message"]["content"]
                        
                        # Find JSON in the response
                        start_idx = chunk_text_response.find('{')
                        end_idx = chunk_text_response.rfind('}') + 1
                        if start_idx >= 0 and end_idx > start_idx:
                            json_str = chunk_text_response[start_idx:end_idx]
                            chunk_json = json.loads(json_str)
                            
                            # If additional evidence was found, add it to our collection
                            additional_evidence = chunk_json.get("additional_evidence")
                            if additional_evidence and additional_evidence != "No additional evidence found":
                                # Find the page number for this evidence
                                chunk_evidence_page = 1  # Default
                                
                                # Try to find the page with the evidence
                                if pages_text and len(pages_text) > 0:
                                    # Get some key phrases from the evidence (at least 3 words long)
                                    evidence_words = additional_evidence.lower().split()
                                    
                                    if len(evidence_words) >= 3:
                                        # Look for the first 3 words as a phrase
                                        search_phrase = ' '.join(evidence_words[:3])
                                        
                                        for page in pages_text:
                                            page_text = page.get("text", "").lower()
                                            if search_phrase in page_text:
                                                chunk_evidence_page = page.get("page_number")
                                                break
                                
                                # Add to our collections
                                all_evidence.append(additional_evidence)
                                all_evidence_pages.append(chunk_evidence_page)
                                print(f"Found additional evidence on page {chunk_evidence_page}")
                    except Exception as e:
                        print(f"Error processing chunk {chunk_idx+1}: {str(e)}")
                    
                    # Add a small delay to avoid rate limiting
                    time.sleep(1)
            
            # Format all compliance evidence with page numbers
            if all_evidence and all_evidence_pages:
                # Combine all evidence with page references
                combined_evidence = "; ".join([f"[Page {page}] {evidence}" for evidence, page in zip(all_evidence, all_evidence_pages)])
                compliance_result["compliance_evidence_with_page"] = combined_evidence
                
                # Update the main compliance evidence field with all evidence (without page numbers)
                compliance_result["compliance_evidence"] = "; ".join(all_evidence)
            elif compliance_result.get("compliance_evidence") and compliance_result.get("compliance_evidence") != "N/A":
                # Just format the single piece of evidence if that's all we have
                compliance_result["compliance_evidence_with_page"] = f"[Page {evidence_page}] {compliance_result.get('compliance_evidence')}"
            
            # Save to cache
            self.save_to_cache(cache_key, compliance_result)
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
            
            # Return the result along with chunk processing statistics
            chunks_processed = len(chunks) - 1 if len(chunks) > 1 and compliance_result.get("is_compliant") in ["Yes", "Partial"] else 0
            additional_evidence_count = len(all_evidence) - 1 if len(all_evidence) > 1 else 0
            
            return compliance_result, chunks_processed, additional_evidence_count
            
        except Exception as e:
            print(f"Error analyzing compliance with Regulation {regulation_number}: {str(e)}")
            # Return error information, including full regulation text
            error_result = {
                "regulation_number": regulation_number,
                "regulation_title": regulation_title,
                "regulation_text": regulation_text,
                "section_type": section_type,
                "source_name": source_name,
                "document_name": document_name,
                "applicability": "May Apply - Requires Further Review",
                "is_compliant": "Partial",
                "compliance_reasoning": "Unable to determine compliance reasoning due to an error during analysis.",
                "compliance_evidence": "",
                "evidence_page": "N/A",
                "compliance_evidence_with_page": "N/A",
                "gap_description": f"Error during analysis: {str(e)[:50]}",
                "gap_recommendations": "Manual review required",
                "confidence_score": "Low"
            }
            # Return error result with zero chunk statistics
            return error_result, 0, 0
    
    def get_guidance_for_regulation(self, regulation_number):
        """
        Get guidance items for a specific regulation.
        
        Args:
            regulation_number: Regulation number
            
        Returns:
            list: List of guidance items
        """
        guidance = self.load_guidance()
        
        # Convert regulation number to string for comparison
        reg_num_str = str(regulation_number)
        
        # Filter guidance items for the regulation
        return [g for g in guidance if str(g.get('Regulation Number', '')) == reg_num_str]
    
    def analyze_all_documents(self, documents):
        """
        Analyze all documents for compliance with applicable regulations.
        
        Args:
            documents (list): List of document dictionaries
            
        Returns:
            list: List of document analysis results
        """
        # Log the skip regulations configuration at the start of analysis
        if any(len(regs) > 0 for regs in self.skip_regulations.values()):
            print("\nSkip regulations configuration:")
            for section_type, reg_numbers in self.skip_regulations.items():
                if reg_numbers:
                    print(f"  Section {section_type}: {', '.join(map(str, reg_numbers))}")
        
        all_results = []
        
        for document in tqdm(documents, desc="Analyzing documents"):
            document_name = document.get('metadata', {}).get('filename', 'Unknown Document')
            print(f"\nAnalyzing document: {document_name}")
            
            # Analyze document compliance
            document_results = self.analyze_document_compliance(document)
            all_results.append(document_results)
        
        return all_results
    
    def analyze_document_compliance(self, document):
        """
        Analyze compliance of a document with applicable regulations using the two-phase approach.
        
        Args:
            document (dict): Document dictionary with metadata and text
            
        Returns:
            dict: Compliance analysis results
        """
        document_name = document.get('metadata', {}).get('filename', 'Unknown Document')
        
        print(f"\nAnalyzing compliance for document: {document_name}")
        
        # Phase 1: Filter applicable regulations
        applicable_regulations_with_results = self.filter_applicable_regulations(document)
        
        # Phase 2: Detailed analysis of applicable regulations
        compliance_results = []
        
        # Track chunk processing statistics
        total_chunks_processed = 0
        additional_evidence_found_count = 0
        
        # Process all regulations that passed Phase 1
        for regulation, phase1_result in tqdm(applicable_regulations_with_results, 
                                              desc="Analyzing applicable regulations (Phase 2)"):
            regulation_number = regulation.get('Regulation Number', '')
            
            # Get guidance for the regulation
            guidance_items = self.get_guidance_for_regulation(regulation_number)
            
            # Analyze compliance in Phase 2
            result, chunks_processed, additional_evidence_count = self.analyze_regulation_compliance(document, regulation, phase1_result, guidance_items)
            compliance_results.append(result)
            
            # Update chunk processing statistics
            total_chunks_processed += chunks_processed
            additional_evidence_found_count += additional_evidence_count
        
        # Add "Does Not Apply" results from Phase 1 for all regulations
        all_regulations = self.load_regulations()
        analyzed_reg_numbers = [r[0].get('Regulation Number', '') for r in applicable_regulations_with_results]
        
        for regulation in all_regulations:
            regulation_number = regulation.get('Regulation Number', '')
            if regulation_number not in analyzed_reg_numbers:
                # Check if we have a cached Phase 1 result with applicability_reasoning
                cache_key = self.get_cache_key(document_name, regulation_number, 1)
                cached_result = self.check_cache(cache_key)
                
                # Create a "Does Not Apply" result
                result = {
                    "regulation_number": regulation_number,
                    "regulation_title": regulation.get('Regulation Title', ''),
                    "section_type": regulation.get('Section Type', ''),
                    "source_name": regulation.get('Source Name', ''),
                    "document_name": document_name,
                    "applicability": "Does Not Apply",
                    "is_compliant": "N/A",
                    "compliance_evidence": "N/A",
                    "gap_description": "N/A",
                    "gap_recommendations": "N/A",
                    "confidence_score": "High"
                }
                
                # Add applicability_reasoning from cache if available
                if cached_result and 'applicability_reasoning' in cached_result:
                    result['applicability_reasoning'] = cached_result['applicability_reasoning']
                
                compliance_results.append(result)
        
        # Compile overall compliance summary
        applies_count = sum(1 for r in compliance_results if r.get('applicability') == 'Applies')
        may_apply_count = sum(1 for r in compliance_results if r.get('applicability') == 'May Apply - Requires Further Review')
        does_not_apply_count = sum(1 for r in compliance_results if r.get('applicability') == 'Does Not Apply')
        
        compliant_count = sum(1 for r in compliance_results if r.get('is_compliant') == 'Yes' and r.get('applicability') != 'Does Not Apply')
        partial_count = sum(1 for r in compliance_results if r.get('is_compliant') == 'Partial' and r.get('applicability') != 'Does Not Apply')
        non_compliant_count = sum(1 for r in compliance_results if r.get('is_compliant') == 'No' and r.get('applicability') != 'Does Not Apply')
        
        # Calculate model usage statistics
        phase1_count = len(all_regulations)
        phase2_count = len(applicable_regulations_with_results)
        
        compliance_summary = {
            "document_name": document_name,
            "total_regulations_analyzed": len(compliance_results),
            "applicability_summary": {
                "applies": applies_count,
                "may_apply": may_apply_count,
                "does_not_apply": does_not_apply_count
            },
            "compliance_summary": {
                "compliant": compliant_count,
                "partial": partial_count,
                "non_compliant": non_compliant_count
            },
            "model_usage": {
                "claude_3_5_sonnet_phase1": phase1_count,
                "claude_3_7_sonnet_phase2": phase2_count,
                "chunk_processing": {
                    "total_chunks_processed": total_chunks_processed,
                    "additional_evidence_found": additional_evidence_found_count
                }
            },
            "compliance_percentage": round(compliant_count / (applies_count + may_apply_count) * 100, 2) if (applies_count + may_apply_count) > 0 else 0,
            "detailed_results": compliance_results
        }
        
        return compliance_summary
    
    def analyze_all_documents(self, documents, use_parallel=True, max_workers=4):
        """
        Analyze compliance for all documents.
        
        Args:
            documents (list): List of document dictionaries
            use_parallel (bool): Whether to use parallel processing
            max_workers (int): Maximum number of worker threads
            
        Returns:
            list: List of compliance analysis results
        """
        analysis_results = []
        
        # Initialize aggregate statistics for chunk processing
        total_chunks_processed = 0
        total_additional_evidence_found = 0
        
        if use_parallel and len(documents) > 1:
            print(f"Using parallel processing with {max_workers} workers")
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_doc = {
                    executor.submit(self.analyze_document_compliance, doc): doc 
                    for doc in documents if doc.get('full_text')
                }
                
                for future in tqdm(concurrent.futures.as_completed(future_to_doc), 
                                 total=len(future_to_doc),
                                 desc="Analyzing documents"):
                    try:
                        result = future.result()
                        analysis_results.append(result)
                    except Exception as e:
                        doc = future_to_doc[future]
                        doc_name = doc.get('metadata', {}).get('filename', 'Unknown Document')
                        print(f"Error analyzing document {doc_name}: {str(e)}")
        else:
            for document in documents:
                if document.get('full_text'):  # Only analyze documents with text
                    result = self.analyze_document_compliance(document)
                    analysis_results.append(result)
        
        return analysis_results
    
    def save_analysis_results(self, analysis_results):
        """
        Save analysis results to a JSON file.
        
        Args:
            analysis_results (list): List of analysis results
            
        Returns:
            str: Path to the saved file
        """
        output_path = self.output_dir / "compliance_analysis_results.json"
        
        # Deduplicate regulations before saving
        print("Deduplicating regulations in analysis results...")
        deduplicated_results = deduplicate_regulations_in_results(analysis_results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(deduplicated_results, f, indent=2, ensure_ascii=False)
        
        print(f"Saved compliance analysis results to {output_path}")
        return str(output_path)


if __name__ == "__main__":
    # This is a test that would be run with actual documents
    from document_processor import DocumentProcessor
    
    processor = DocumentProcessor()
    documents = processor.process_all_documents()
    
    analyzer = EnhancedComplianceAnalyzer()
    analysis_results = analyzer.analyze_all_documents(documents)
    analyzer.save_analysis_results(analysis_results)
    
    # Print summary
    for result in analysis_results:
        print(f"\nDocument: {result['document_name']}")
        print(f"Compliance percentage: {result['compliance_percentage']}%")
        print(f"Applicable regulations: {result['applicability_summary']['applies'] + result['applicability_summary']['may_apply']}")
        print(f"Compliant: {result['compliance_summary']['compliant']}")
        print(f"Partial: {result['compliance_summary']['partial']}")
        print(f"Non-compliant: {result['compliance_summary']['non_compliant']}")
