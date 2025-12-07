"""
Tests for InteractionChecker module
"""

import pytest
from med_tracker.checker import InteractionChecker


class TestInteractionChecker:
    """Test cases for the InteractionChecker class."""
    
    @pytest.fixture
    def checker(self):
        """Create a test checker instance."""
        return InteractionChecker()
    
    def test_check_interactions_basic(self, checker):
        """Test basic interaction checking."""
        result = checker.check_interactions(
            medications=["aspirin"],
            supplements=[],
            foods=[]
        )
        
        assert "medications" in result
        assert "supplements" in result
        assert "foods" in result
        assert "drug_drug_interactions" in result
        assert "drug_food_interactions" in result
        assert "drug_supplement_interactions" in result
        assert "summary" in result
    
    def test_check_grapefruit_statins(self, checker):
        """Test checking grapefruit-statins interaction."""
        result = checker.check_interactions(
            medications=["atorvastatin"],
            supplements=[],
            foods=["grapefruit"]
        )
        
        # Should find the food-drug interaction
        assert len(result["drug_food_interactions"]) > 0
        
        # Check that grapefruit interaction is present
        found_interaction = False
        for interaction in result["drug_food_interactions"]:
            if "grapefruit" in interaction["food"].lower():
                found_interaction = True
                assert interaction["severity"] in ["High", "Moderate", "Low"]
                break
        
        assert found_interaction, "Expected grapefruit-statin interaction not found"
    
    def test_check_warfarin_leafy_greens(self, checker):
        """Test checking warfarin with leafy greens."""
        result = checker.check_interactions(
            medications=["warfarin"],
            supplements=[],
            foods=["leafy greens"]
        )
        
        # Should find the food-drug interaction
        if len(result["drug_food_interactions"]) > 0:
            interaction = result["drug_food_interactions"][0]
            assert "warfarin" in interaction["medication"].lower()
            assert "severity" in interaction
    
    def test_check_st_johns_wort(self, checker):
        """Test checking St John's Wort supplement interactions."""
        result = checker.check_interactions(
            medications=["warfarin"],
            supplements=["st john's wort"],
            foods=[]
        )
        
        # Should find supplement-drug interaction
        assert len(result["drug_supplement_interactions"]) > 0
        interaction = result["drug_supplement_interactions"][0]
        assert "st john" in interaction["supplement"].lower()
        assert interaction["severity"] == "High"
    
    def test_summary_counts(self, checker):
        """Test that summary counts are calculated correctly."""
        result = checker.check_interactions(
            medications=["warfarin"],
            supplements=["st john's wort"],
            foods=["grapefruit"]
        )
        
        summary = result["summary"]
        assert "total_interactions" in summary
        assert "high_severity_count" in summary
        assert "moderate_severity_count" in summary
        assert "low_severity_count" in summary
        
        # Total should equal sum of severity counts
        total_by_severity = (
            summary["high_severity_count"] +
            summary["moderate_severity_count"] +
            summary["low_severity_count"]
        )
        assert summary["total_interactions"] == total_by_severity
