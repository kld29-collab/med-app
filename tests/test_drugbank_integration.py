"""
Tests for DrugBank integration (RAG approach)
"""

import pytest
import sys
from pathlib import Path
from utils.drugbank_loader import DrugBankLoader
from utils.drugbank_db import DrugBankDatabase
from utils.drug_apis import DrugAPIClient


class TestDrugBankLoader:
    """Test DrugBank XML loader."""
    
    @pytest.fixture
    def xml_file_path(self):
        """Get path to DrugBank XML file."""
        return Path(__file__).parent.parent / "data" / "full_database.xml"
    
    def test_loader_initialization(self, xml_file_path):
        """Test that loader initializes correctly."""
        loader = DrugBankLoader(str(xml_file_path))
        assert loader is not None
        assert not loader.loaded
    
    def test_load_xml(self, xml_file_path):
        """Test loading XML file."""
        if not xml_file_path.exists():
            pytest.skip("DrugBank XML file not found")
        
        loader = DrugBankLoader(str(xml_file_path))
        success = loader.load()
        
        assert success
        assert loader.loaded
        assert len(loader.drugs) > 0
        print(f"✓ Successfully loaded {len(loader.drugs)} drugs from XML")
    
    def test_drug_data_structure(self, xml_file_path):
        """Test that loaded drugs have expected structure."""
        if not xml_file_path.exists():
            pytest.skip("DrugBank XML file not found")
        
        loader = DrugBankLoader(str(xml_file_path))
        loader.load()
        
        # Get first drug
        drugs = loader.get_all_drugs()
        assert len(drugs) > 0
        
        drug = drugs[0]
        assert "primary_id" in drug
        assert "name" in drug
        assert "drug_interactions" in drug
        assert "food_interactions" in drug
        print(f"✓ Drug data structure is valid: {drug['name']}")


class TestDrugBankDatabase:
    """Test DrugBank SQLite database."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        """Get temporary database path."""
        return str(tmp_path / "test_drugbank.db")
    
    @pytest.fixture
    def xml_file_path(self):
        """Get path to DrugBank XML file."""
        return Path(__file__).parent.parent / "data" / "full_database.xml"
    
    def test_database_creation(self, db_path, xml_file_path):
        """Test database creation from XML."""
        if not xml_file_path.exists():
            pytest.skip("DrugBank XML file not found")
        
        db = DrugBankDatabase(db_path, str(xml_file_path))
        success = db.initialize()
        
        assert success
        print("✓ Database created successfully")
        
        db.close()
    
    def test_drug_lookup(self, db_path, xml_file_path):
        """Test looking up drugs in database."""
        if not xml_file_path.exists():
            pytest.skip("DrugBank XML file not found")
        
        # First create database with sample data
        loader = DrugBankLoader(str(xml_file_path))
        loader.load()
        
        drugs = loader.get_all_drugs()
        assert len(drugs) > 0
        
        # Get a sample drug name
        sample_drug = drugs[0]
        sample_name = sample_drug["name"]
        
        # Now test database lookup
        db = DrugBankDatabase(db_path, str(xml_file_path))
        db.initialize()
        
        # Try to find the drug
        found_drug = db.get_drug_by_name(sample_name)
        assert found_drug is not None
        assert found_drug["name"] == sample_name
        
        print(f"✓ Successfully found drug: {sample_name}")
        
        db.close()
    
    def test_search_drugs(self, db_path, xml_file_path):
        """Test searching for drugs."""
        if not xml_file_path.exists():
            pytest.skip("DrugBank XML file not found")
        
        db = DrugBankDatabase(db_path, str(xml_file_path))
        db.initialize()
        
        # Search for common drug names
        results = db.search_drugs("aspirin", limit=5)
        assert isinstance(results, list)
        
        if results:
            print(f"✓ Search found {len(results)} results for 'aspirin'")
            for result in results:
                print(f"  - {result['name']}")
        
        db.close()


class TestDrugAPIClient:
    """Test integrated DrugAPIClient with DrugBank."""
    
    def test_client_initialization(self):
        """Test that API client initializes."""
        client = DrugAPIClient()
        assert client is not None
        # DrugBank DB might be None if XML file not found, which is OK for this test
    
    def test_search_drugbank(self):
        """Test searching DrugBank through API client."""
        client = DrugAPIClient()
        
        if client.drugbank_db is None:
            pytest.skip("DrugBank database not initialized")
        
        results = client.search_drugbank("aspirin")
        assert isinstance(results, list)
        print(f"✓ API client search returned {len(results)} results")
    
    def test_get_food_interactions(self):
        """Test getting food interactions."""
        client = DrugAPIClient()
        
        if client.drugbank_db is None:
            pytest.skip("DrugBank database not initialized")
        
        # Get a drug from database and test food interactions
        all_drugs = client.drugbank_db.get_all_drugs()
        if not all_drugs:
            pytest.skip("No drugs in database")
        
        drug_name = all_drugs[0]["name"]
        interactions = client.get_food_interactions_drugbank(drug_name)
        
        assert isinstance(interactions, list)
        print(f"✓ Retrieved {len(interactions)} food interactions for {drug_name}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
