"""
Document Processor Module

This module processes client documents to extract text and metadata.
It handles PDF files and extracts text from each page.
"""

import os
import fitz  # PyMuPDF
from pathlib import Path
from tqdm import tqdm

class DocumentProcessor:
    def __init__(self, base_dir=None):
        """
        Initialize the document processor.
        
        Args:
            base_dir (Path, optional): Base directory path. If None, will use default.
        """
        if base_dir is None:
            self.base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
        else:
            self.base_dir = Path(base_dir)
            
        self.documents_dir = self.base_dir / "Input" / "Compliance Documents"
    
    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path (str): Path to PDF file
            
        Returns:
            tuple: (full_text, pages_text)
                full_text (str): Full text of the PDF
                pages_text (list): List of dictionaries with page number and text
        """
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            pages_text = []
            
            for page_num, page in enumerate(tqdm(doc, desc="Processing pages", leave=False)):
                text = page.get_text()
                full_text += text + "\n\n"
                pages_text.append({
                    "page_number": page_num + 1,
                    "text": text
                })
            
            return full_text, pages_text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {str(e)}")
            return "", []
    
    def process_document(self, pdf_path):
        """
        Process a document to extract text and metadata.
        
        Args:
            pdf_path (str): Path to PDF file
            
        Returns:
            dict: Document dictionary with metadata and text
        """
        try:
            # Extract metadata
            filename = os.path.basename(pdf_path)
            file_size = os.path.getsize(pdf_path)
            
            # Extract text
            print(f"Extracting text from {filename}")
            full_text, pages_text = self.extract_text_from_pdf(pdf_path)
            
            # Create document dictionary
            document = {
                "metadata": {
                    "filename": filename,
                    "file_path": str(pdf_path),
                    "file_size": file_size,
                    "page_count": len(pages_text)
                },
                "full_text": full_text,
                "pages": pages_text
            }
            
            return document
        except Exception as e:
            print(f"Error processing document {pdf_path}: {str(e)}")
            return None
    
    def process_all_documents(self):
        """
        Process all documents in the documents directory.
        
        Returns:
            list: List of document dictionaries
        """
        # Ensure documents directory exists
        if not self.documents_dir.exists():
            print(f"Documents directory not found: {self.documents_dir}")
            return []
        
        # Find all PDF files
        pdf_files = list(self.documents_dir.glob("*.pdf"))
        print(f"Found {len(pdf_files)} compliance documents to process")
        
        # Process each document
        documents = []
        for pdf_path in pdf_files:
            document = self.process_document(pdf_path)
            if document:
                documents.append(document)
        
        return documents


if __name__ == "__main__":
    processor = DocumentProcessor()
    documents = processor.process_all_documents()
    
    for doc in documents:
        print(f"Processed: {doc['metadata']['filename']}")
        print(f"Pages: {doc['metadata']['page_count']}")
        print(f"Text length: {len(doc['full_text'])}")
        print("-" * 50)
