"""
DrugBank XML Parser and Data Loader

Parses the DrugBank full database XML file and extracts drug information,
interactions, and food interactions for use in the medication tracker.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
import sys
from pathlib import Path


class DrugBankLoader:
    """Loads and parses DrugBank XML database."""
    
    # XML namespace used in DrugBank files
    NAMESPACE = {"db": "http://www.drugbank.ca"}
    
    def __init__(self, xml_file_path: str):
        """
        Initialize loader with path to DrugBank XML file.
        
        Args:
            xml_file_path: Path to full_database.xml file
        """
        self.xml_file_path = Path(xml_file_path)
        self.drugs: Dict[str, Dict] = {}  # drugbank_id -> drug_data
        self.drug_name_index: Dict[str, str] = {}  # drug_name -> drugbank_id
        self.loaded = False
    
    def load(self) -> bool:
        """
        Load and parse the DrugBank XML file.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.xml_file_path.exists():
            print(f"[ERROR] DrugBank XML file not found: {self.xml_file_path}", file=sys.stderr)
            return False
        
        try:
            print(f"[INFO] Loading DrugBank XML from {self.xml_file_path}", file=sys.stderr)
            
            # Parse XML - using iterparse for memory efficiency with large files
            context = ET.iterparse(str(self.xml_file_path), events=("end",))
            
            drug_count = 0
            for event, elem in context:
                if elem.tag == "{http://www.drugbank.ca}drug":
                    drug_data = self._parse_drug(elem)
                    if drug_data:
                        primary_id = drug_data["primary_id"]
                        self.drugs[primary_id] = drug_data
                        
                        # Index by name for lookup
                        name = drug_data.get("name", "")
                        if name:
                            self.drug_name_index[name.lower()] = primary_id
                        
                        drug_count += 1
                        if drug_count % 1000 == 0:
                            print(f"[INFO] Loaded {drug_count} drugs...", file=sys.stderr)
                    
                    # Clear element to save memory
                    elem.clear()
            
            self.loaded = True
            print(f"[INFO] Successfully loaded {drug_count} drugs from DrugBank", file=sys.stderr)
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load DrugBank XML: {str(e)}", file=sys.stderr)
            return False
    
    def _parse_drug(self, drug_elem: ET.Element) -> Optional[Dict]:
        """
        Parse a single drug element from XML.
        
        Args:
            drug_elem: XML element representing a drug
            
        Returns:
            Dictionary with drug data or None
        """
        try:
            # Get primary drugbank ID
            primary_id = None
            for id_elem in drug_elem.findall("db:drugbank-id", self.NAMESPACE):
                if id_elem.get("primary") == "true":
                    primary_id = id_elem.text
                    break
            
            if not primary_id:
                return None
            
            # Extract basic info
            name = self._get_text(drug_elem, "db:name")
            description = self._get_text(drug_elem, "db:description")
            indication = self._get_text(drug_elem, "db:indication")
            mechanism = self._get_text(drug_elem, "db:mechanism-of-action")
            toxicity = self._get_text(drug_elem, "db:toxicity")
            
            # Extract interactions
            drug_interactions = self._parse_drug_interactions(drug_elem)
            food_interactions = self._parse_food_interactions(drug_elem)
            
            return {
                "primary_id": primary_id,
                "name": name,
                "description": description,
                "indication": indication,
                "mechanism_of_action": mechanism,
                "toxicity": toxicity,
                "drug_interactions": drug_interactions,
                "food_interactions": food_interactions,
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to parse drug: {str(e)}", file=sys.stderr)
            return None
    
    def _parse_drug_interactions(self, drug_elem: ET.Element) -> List[Dict]:
        """
        Extract drug-drug interactions from drug element.
        
        Args:
            drug_elem: XML element representing a drug
            
        Returns:
            List of interaction dictionaries
        """
        interactions = []
        
        interactions_elem = drug_elem.find("db:drug-interactions", self.NAMESPACE)
        if interactions_elem is None:
            return interactions
        
        for interaction_elem in interactions_elem.findall("db:drug-interaction", self.NAMESPACE):
            interaction_id = self._get_text(interaction_elem, "db:drugbank-id")
            interaction_name = self._get_text(interaction_elem, "db:name")
            description = self._get_text(interaction_elem, "db:description")
            
            if interaction_name:
                interactions.append({
                    "drugbank_id": interaction_id,
                    "name": interaction_name,
                    "description": description,
                })
        
        return interactions
    
    def _parse_food_interactions(self, drug_elem: ET.Element) -> List[str]:
        """
        Extract food interactions from drug element.
        
        Args:
            drug_elem: XML element representing a drug
            
        Returns:
            List of food interaction descriptions
        """
        interactions = []
        
        food_interactions_elem = drug_elem.find("db:food-interactions", self.NAMESPACE)
        if food_interactions_elem is None:
            return interactions
        
        for interaction_elem in food_interactions_elem.findall("db:food-interaction", self.NAMESPACE):
            text = interaction_elem.text
            if text:
                interactions.append(text.strip())
        
        return interactions
    
    def _get_text(self, elem: ET.Element, path: str) -> Optional[str]:
        """
        Safely get text from XML element.
        
        Args:
            elem: XML element
            path: XPath to child element
            
        Returns:
            Text content or None
        """
        child = elem.find(path, self.NAMESPACE)
        if child is not None and child.text:
            return child.text.strip()
        return None
    
    def get_drug_by_id(self, drugbank_id: str) -> Optional[Dict]:
        """
        Get drug data by DrugBank ID.
        
        Args:
            drugbank_id: DrugBank ID
            
        Returns:
            Drug data dictionary or None
        """
        return self.drugs.get(drugbank_id)
    
    def get_drug_by_name(self, drug_name: str) -> Optional[Dict]:
        """
        Get drug data by name (case-insensitive).
        
        Args:
            drug_name: Name of drug
            
        Returns:
            Drug data dictionary or None
        """
        drugbank_id = self.drug_name_index.get(drug_name.lower())
        if drugbank_id:
            return self.drugs.get(drugbank_id)
        return None
    
    def search_drugs_by_name(self, search_term: str) -> List[Dict]:
        """
        Search for drugs by partial name match.
        
        Args:
            search_term: Partial drug name
            
        Returns:
            List of matching drug dictionaries
        """
        search_lower = search_term.lower()
        results = []
        
        for drug_id, drug_data in self.drugs.items():
            if search_lower in drug_data.get("name", "").lower():
                results.append(drug_data)
        
        return results
    
    def get_all_drugs(self) -> List[Dict]:
        """
        Get all loaded drugs.
        
        Returns:
            List of all drug dictionaries
        """
        return list(self.drugs.values())
