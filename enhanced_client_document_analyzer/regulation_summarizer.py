"""
Regulation Summarizer Module

This module summarizes CPC regulations and creates a guidance mapping.
It processes the combined regulations and guidance files to create
structured summaries for use in compliance analysis.
"""

import os
import json
from pathlib import Path

class RegulationSummarizer:
    def __init__(self, base_dir=None):
        """
        Initialize the regulation summarizer.
        
        Args:
            base_dir (Path, optional): Base directory path. If None, will use default.
        """
        if base_dir is None:
            self.base_dir = Path(r"C:\Users\91810\OneDrive\Desktop\CPC_AIB_Life")
        else:
            self.base_dir = Path(base_dir)
            
        self.regulations_path = self.base_dir / "output" / "Data_extraction" / "regulation_17A_48_combined.json"
        self.guidance_path = self.base_dir / "output" / "Guidance" / "combined_guidance.json"
        self.output_dir = self.base_dir / "output" / "enhanced_document_analysis"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
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
    
    def create_regulation_summaries(self):
        """
        Create summaries of all regulations.
        
        Returns:
            list: List of regulation summaries
        """
        regulations = self.load_regulations()
        
        # Create summaries
        summaries = []
        for regulation in regulations:
            summary = {
                "regulation_number": regulation.get('Regulation Number', ''),
                "regulation_title": regulation.get('Regulation Title', ''),
                "section_type": regulation.get('Section Type', ''),
                "source_name": regulation.get('Source Name', ''),
                "regulation_text": regulation.get('Regulation Text', '')[:500] + "..." if len(regulation.get('Regulation Text', '')) > 500 else regulation.get('Regulation Text', '')
            }
            summaries.append(summary)
        
        return summaries
    
    def create_guidance_mapping(self):
        """
        Create a mapping of regulations to guidance items.
        
        Returns:
            dict: Mapping of regulation numbers to guidance items
        """
        regulations = self.load_regulations()
        guidance = self.load_guidance()
        
        # Create mapping
        guidance_map = {}
        for regulation in regulations:
            reg_num = str(regulation.get('Regulation Number', ''))
            
            # Find guidance items for this regulation
            reg_guidance = []
            for item in guidance:
                if str(item.get('Regulation Number', '')) == reg_num:
                    guidance_item = {
                        "guidance_id": item.get('Guidance ID', ''),
                        "guidance_text": item.get('Guidance Text', '')[:500] + "..." if len(item.get('Guidance Text', '')) > 500 else item.get('Guidance Text', ''),
                        "regulation_sub_section_number": item.get('Regulation Sub-Section Number', '')
                    }
                    reg_guidance.append(guidance_item)
            
            guidance_map[reg_num] = reg_guidance
        
        return guidance_map
    
    def save_regulation_summaries(self, summaries):
        """
        Save regulation summaries to a JSON file.
        
        Args:
            summaries (list): List of regulation summaries
            
        Returns:
            str: Path to the saved file
        """
        output_path = self.output_dir / "regulation_summaries.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, indent=2, ensure_ascii=False)
        
        print(f"Saved regulation summaries to {output_path}")
        return str(output_path)
    
    def save_guidance_mapping(self, guidance_map):
        """
        Save guidance mapping to a JSON file.
        
        Args:
            guidance_map (dict): Mapping of regulation numbers to guidance items
            
        Returns:
            str: Path to the saved file
        """
        output_path = self.output_dir / "guidance_map.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(guidance_map, f, indent=2, ensure_ascii=False)
        
        print(f"Saved guidance mapping to {output_path}")
        return str(output_path)
    
    def generate_all(self):
        """
        Generate all regulation summaries and guidance mapping.
        
        Returns:
            tuple: (summaries_path, guidance_map_path)
        """
        print("Generating regulation summaries...")
        summaries = self.create_regulation_summaries()
        summaries_path = self.save_regulation_summaries(summaries)
        
        print("Generating guidance mapping...")
        guidance_map = self.create_guidance_mapping()
        guidance_map_path = self.save_guidance_mapping(guidance_map)
        
        return summaries_path, guidance_map_path


if __name__ == "__main__":
    summarizer = RegulationSummarizer()
    summarizer.generate_all()
