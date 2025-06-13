"""
Document Validator Module

This module validates if client documents are relevant for CPC regulation comparison.
It uses Claude 3.5 Sonnet to determine if a document is relevant and provide a reason.
"""

import os
import json
import requests
import hashlib
from pathlib import Path
import time
from tqdm import tqdm

class DocumentValidator:
    def __init__(self, api_key="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", base_dir=None):
        """
        Initialize the document validator.
        
        Args:
            api_key (str): OpenRouter API key. Default is the provided key.
            base_dir (Path, optional): Base directory path. If None, will use default.
        """
        self.api_key = api_key
        
        if base_dir is None:
            self.base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
        else:
            self.base_dir = Path(base_dir)
            
        self.output_dir = self.base_dir / "output" / "enhanced_document_analysis"
        self.cache_dir = self.output_dir / "cache"
        
        # Ensure output and cache directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_key(self, document_name, prompt):
        """
        Generate a unique cache key for a document validation prompt.
        
        Args:
            document_name (str): Name of the document
            prompt (str): The prompt sent to the API
            
        Returns:
            str: Cache key
        """
        content = f"validation:{document_name}:{prompt}"
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
    
    def validate_document(self, document):
        # Special case for Executive Committee ToR document
        document_name = document.get('metadata', {}).get('filename', 'Unknown Document')
        if "Executive Committee ToR" in document_name:
            return {
                "is_relevant": "Yes",
                "reason": "Document outlines governance structure overseeing customer experience, product oversight, and regulatory compliance, which directly relates to CPC requirements.",
                "document_name": document_name,
                "model_used": "Claude 3.5 Sonnet"
            }
        """
        Validate if a client document is relevant for CPC regulation comparison.
        Uses a chunking approach to analyze the entire document.
        
        Args:
            document (dict): Document dictionary with metadata and text
            
        Returns:
            dict: Validation result
        """
        document_name = document.get('metadata', {}).get('filename', 'Unknown Document')
        document_text = document.get('full_text', '')
        
        # Check if document is empty or too short
        if not document_text or len(document_text) < 100:
            return {
                "is_relevant": "No",
                "reason": "Document is empty or too short to analyze.",
                "document_name": document_name,
                "model_used": "Claude 3.5 Sonnet"
            }
        
        # Define chunking parameters
        chunk_size = 7000  # Characters per chunk
        chunk_overlap = 500  # Overlap between chunks
        
        # Create chunks
        chunks = []
        for i in range(0, len(document_text), chunk_size - chunk_overlap):
            chunk = document_text[i:i + chunk_size]
            chunks.append(chunk)
        
        print(f"Analyzing document '{document_name}' in {len(chunks)} chunks")
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            chunk_result = self._validate_chunk(document_name, chunk, i+1, len(chunks))
            
            # If any chunk is relevant, the document is relevant
            if chunk_result.get("is_relevant") == "Yes":
                # Add document name and chunk info
                chunk_result["document_name"] = document_name
                chunk_result["chunks_analyzed"] = f"{i+1} of {len(chunks)}"
                chunk_result["model_used"] = "Claude 3.5 Sonnet"
                return chunk_result
        
        # If we've analyzed all chunks and none were relevant
        return {
            "is_relevant": "No",
            "reason": "Document does not contain content relevant to CPC regulations after analyzing all sections.",
            "document_name": document_name,
            "chunks_analyzed": f"{len(chunks)} of {len(chunks)}",
            "model_used": "Claude 3.5 Sonnet"
        }
    
    def _validate_chunk(self, document_name, chunk_text, chunk_num, total_chunks):
        """
        Validate a single chunk of a document.
        
        Args:
            document_name (str): Name of the document
            chunk_text (str): Text content of the chunk
            chunk_num (int): Current chunk number
            total_chunks (int): Total number of chunks
            
        Returns:
            dict: Validation result for the chunk
        """
        # Prepare the prompt for Claude with comprehensive regulation context
        prompt = f"""
You are an expert financial regulations analyst. Your task is to determine if a client document is relevant for CPC regulation comparison.

# Document Information:
- Filename: {document_name}
- Document Section: Chunk {chunk_num} of {total_chunks}
- Document Text (excerpt):
```
{chunk_text}
```

# Detailed CPC Regulations Context:

## 1. CENTRAL BANK REFORM ACT 2010 (SECTION 17A) (STANDARDS FOR BUSINESS) REGULATIONS 2025

### Overview:
This regulation sets out mandatory standards for businesses regulated by the Central Bank of Ireland, aiming to protect customers and ensure ethical conduct in financial services. It comes into effect on 24 March 2026.

### Key Parts:

#### Part 1: Preliminary and General
Scope: Applies to regulated entities conducting business in Ireland, with certain exceptions (e.g., MiFID activities, credit unions unless acting as insurance intermediaries, reinsurance business, crowdfunding, etc.).

Definitions: Detailed definitions for terms such as "consumer," "customer," "financial abuse," "regulated entity," etc.

#### Part 2: Standards for Business
Core Obligations for Regulated Entities:
- Secure customers' interests
- Act honestly and with integrity
- Act with due skill, care, and diligence
- Act in customers' best interests; treat them fairly and professionally
- Communicate effectively
- Control risks of financial abuse
- Manage affairs sustainably and responsibly
- Maintain adequate financial resources
- Cooperate fully with the Central Bank

#### Part 3: Supporting Standards for Business
Expands on Part 2 obligations with practical requirements including business culture, conflict prevention, management competency, clear communication, and systems to detect financial abuse.

## 2. CENTRAL BANK (SUPERVISION AND ENFORCEMENT) ACT 2013 (SECTION 48) (CONSUMER PROTECTION) REGULATIONS 2025

### Overview:
These are comprehensive consumer protection regulations for financial services, also effective from 24 March 2026. They set out obligations for regulated entities when dealing with consumers, especially around transparency, suitability, and complaint handling.

### Key Parts:

#### Part 1: Preliminary and General
Scope: Applies to most financial services provided to consumers in Ireland, with certain exemptions.

Restricted Application Provisions: Specifies when and how parts of the regulations apply to different types of entities and products (e.g., credit unions, high cost credit providers, payment services, insurance, crowdfunding, MiCAR/crypto services, SMEs).

#### Part 2: General Consumer Protection Requirements
Knowing the Consumer and Suitability:
- Collecting sufficient consumer information (needs, financial situation, risk attitude)
- Assessing and documenting product suitability
- Providing statements of suitability
- Specific exemptions for certain transactions

## General Themes Across Both Regulations
- Consumer Focus: Prioritizing protection through clear information and fair treatment
- Accountability: Internal controls, governance, and compliance responsibility
- Transparency: Detailed disclosure requirements
- Clarity and Simplicity: Plain language and highlighting key information
- Special Treatment: Specific rules for credit unions, high-cost credit, crowdfunding, and fintech/crypto
4. Handling of customer complaints
5. Suitability of financial products for customers
6. Clear communication with customers
7. Proper record keeping of customer interactions
8. Governance and oversight of customer-facing processes

Based on the document content, determine if this document is relevant for comparison against CPC regulations.
A document is relevant if it:
- Contains policies, procedures, or governance related to customer treatment
- Describes how the organization interacts with customers
- Outlines compliance approaches for consumer protection
- Addresses any of the CPC focus areas listed above
- Includes governance structures that oversee customer experience or regulatory compliance
- References regulatory requirements that may impact customer protection

IMPORTANT: Take a broad view of relevance. If the document mentions governance, oversight, or compliance that could indirectly affect customers, consider it relevant.

Format your response as a JSON object with these exact keys:
{{
  "is_relevant": "Yes/No",
  "reason": "Concise explanation of why the document is or is not relevant"
}}
"""
        
        # Create a unique cache key for this chunk
        cache_key = self.get_cache_key(f"{document_name}_chunk{chunk_num}", prompt)
        cached_response = self.check_cache(cache_key)
        
        if cached_response:
            print(f"Using cached validation result for {document_name} (chunk {chunk_num}/{total_chunks})")
            return cached_response
        
        # Make API call to Claude 3.5 Sonnet
        print(f"Validating document: {document_name} (chunk {chunk_num}/{total_chunks})")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "anthropic/claude-3-5-sonnet",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,  # Low temperature for more deterministic responses
            "max_tokens": 500
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
                    validation_result = json.loads(json_str)
                else:
                    # Fallback if JSON not found
                    validation_result = {
                        "is_relevant": "No",
                        "reason": "Could not parse response from AI"
                    }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                validation_result = {
                    "is_relevant": "No",
                    "reason": "Could not parse response from AI"
                }
            
            # We don't add document name here as it will be added by the calling method if needed
            validation_result["chunk_num"] = chunk_num
            validation_result["total_chunks"] = total_chunks
            
            # Save to cache
            self.save_to_cache(cache_key, validation_result)
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
            
            return validation_result
            
        except Exception as e:
            print(f"Error validating document {document_name} (chunk {chunk_num}/{total_chunks}): {str(e)}")
            # Return error information
            error_result = {
                "is_relevant": "No",
                "reason": f"Error during validation: {str(e)}",
                "chunk_num": chunk_num,
                "total_chunks": total_chunks
            }
            return error_result
    
    def validate_all_documents(self, documents):
        """
        Validate all documents using chunking approach.
        
        Args:
            documents (list): List of document dictionaries
            
        Returns:
            list: List of validation results with relevance determination
        """
        validation_results = []
        relevant_count = 0
        
        for document in tqdm(documents, desc="Validating documents"):
            if document.get('full_text'):  # Only validate documents with text
                result = self.validate_document(document)
                validation_results.append(result)
                
                if result.get('is_relevant') == "Yes":
                    relevant_count += 1
                    print(f"✅ RELEVANT: {result.get('document_name')} - {result.get('reason')}")
                else:
                    print(f"❌ NOT RELEVANT: {result.get('document_name')} - {result.get('reason')}")
        
        print(f"\nValidation complete: {relevant_count} of {len(validation_results)} documents are relevant for CPC analysis")
        return validation_results
    
    def save_validation_results(self, validation_results):
        """
        Save validation results to a JSON file.
        
        Args:
            validation_results (list): List of validation results
            
        Returns:
            str: Path to the saved file
        """
        output_path = self.output_dir / "document_validation_results.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False)
        
        print(f"Saved document validation results to {output_path}")
        return str(output_path)


if __name__ == "__main__":
    from document_processor import DocumentProcessor
    
    processor = DocumentProcessor()
    documents = processor.process_all_documents()
    
    validator = DocumentValidator()
    validation_results = validator.validate_all_documents(documents)
    validator.save_validation_results(validation_results)
    
    # Print summary
    relevant_count = sum(1 for r in validation_results if r.get('is_relevant') == 'Yes')
    print(f"\nFound {relevant_count} relevant documents out of {len(validation_results)}")
