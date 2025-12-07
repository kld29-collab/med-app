"""
Tests for ResultSummarizer module
"""

import pytest
from med_tracker.summarizer import ResultSummarizer


class TestResultSummarizer:
    """Test cases for the ResultSummarizer class."""
    
    @pytest.fixture
    def summarizer(self):
        """Create a test summarizer instance."""
        return ResultSummarizer(api_key=None)  # Use basic summarizer
    
    @pytest.fixture
    def sample_interaction_data(self):
        """Create sample interaction data for testing."""
        return {
            "medications": ["aspirin", "warfarin"],
            "supplements": [],
            "foods": ["grapefruit"],
            "drug_drug_interactions": [
                {
                    "drug1": "aspirin",
                    "drug2": "warfarin",
                    "severity": "High",
                    "description": "Increased bleeding risk"
                }
            ],
            "drug_food_interactions": [
                {
                    "medication": "warfarin",
                    "food": "grapefruit",
                    "interaction": "May affect drug levels",
                    "severity": "Moderate",
                    "recommendation": "Consult healthcare provider"
                }
            ],
            "drug_supplement_interactions": [],
            "summary": {
                "total_interactions": 2,
                "high_severity_count": 1,
                "moderate_severity_count": 1,
                "low_severity_count": 0
            }
        }
    
    def test_basic_summary_structure(self, summarizer, sample_interaction_data):
        """Test that basic summary has the expected structure."""
        summary = summarizer._basic_summary(sample_interaction_data, "Test query")
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "IMPORTANT:" in summary or "medical advice" in summary.lower()
    
    def test_basic_summary_includes_query(self, summarizer, sample_interaction_data):
        """Test that summary includes the original query."""
        query = "Can I take aspirin with warfarin?"
        summary = summarizer._basic_summary(sample_interaction_data, query)
        
        assert query in summary
    
    def test_basic_summary_shows_interactions(self, summarizer, sample_interaction_data):
        """Test that summary displays interaction information."""
        summary = summarizer._basic_summary(sample_interaction_data)
        
        # Should mention the drugs
        assert "aspirin" in summary.lower() or "warfarin" in summary.lower()
        
        # Should show severity
        assert "High" in summary or "HIGH" in summary
        
        # Should show count
        assert "2" in summary  # Total interactions
    
    def test_basic_summary_no_interactions(self, summarizer):
        """Test summary when no interactions are found."""
        data = {
            "medications": ["aspirin"],
            "supplements": [],
            "foods": [],
            "drug_drug_interactions": [],
            "drug_food_interactions": [],
            "drug_supplement_interactions": [],
            "summary": {
                "total_interactions": 0,
                "high_severity_count": 0,
                "moderate_severity_count": 0,
                "low_severity_count": 0
            }
        }
        
        summary = summarizer._basic_summary(data)
        assert "No known interactions" in summary or "0" in summary
    
    def test_disclaimer_always_present(self, summarizer, sample_interaction_data):
        """Test that medical disclaimer is always included."""
        summary = summarizer._basic_summary(sample_interaction_data)
        
        disclaimer_keywords = ["medical advice", "healthcare provider", "educational"]
        has_disclaimer = any(keyword in summary.lower() for keyword in disclaimer_keywords)
        assert has_disclaimer, "Summary should include medical disclaimer"
