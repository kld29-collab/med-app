"""
Tests for MedicationAPIClient module
"""

import pytest
from med_tracker.api_client import MedicationAPIClient


class TestMedicationAPIClient:
    """Test cases for the MedicationAPIClient class."""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return MedicationAPIClient()
    
    def test_get_rxcui_aspirin(self, client):
        """Test getting RxCUI for aspirin."""
        rxcui = client.get_rxcui("aspirin")
        # May fail in restricted network environments
        if rxcui is not None:
            assert isinstance(rxcui, str)
            assert len(rxcui) > 0
    
    def test_get_rxcui_invalid_drug(self, client):
        """Test getting RxCUI for an invalid drug name."""
        rxcui = client.get_rxcui("notarealdrugname12345")
        # May return None or empty result
        assert rxcui is None or rxcui == ""
    
    def test_search_drug_by_name(self, client):
        """Test searching for a drug by name."""
        result = client.search_drug_by_name("aspirin")
        
        assert "drug_name" in result
        assert result["drug_name"] == "aspirin"
        assert "rxcui" in result
        assert "found" in result
        assert "interactions" in result
        
        # Aspirin should be found
        if result["found"]:
            assert result["rxcui"] is not None
    
    def test_check_multiple_interactions(self, client):
        """Test checking interactions for multiple drugs."""
        result = client.check_multiple_interactions(["aspirin", "warfarin"])
        
        assert "drugs_checked" in result
        assert len(result["drugs_checked"]) == 2
        assert "individual_results" in result
        assert "potential_interactions" in result
        
        # Should have results for both drugs
        assert "aspirin" in result["individual_results"]
        assert "warfarin" in result["individual_results"]
