"""
Integration tests for the complete Medication Tracker workflow
"""

import pytest
from med_tracker.cli import MedicationTracker


class TestMedicationTracker:
    """Integration tests for the MedicationTracker class."""
    
    @pytest.fixture
    def tracker(self):
        """Create a test tracker instance."""
        return MedicationTracker(openai_api_key=None, drugbank_api_key=None)
    
    def test_process_query_basic(self, tracker):
        """Test processing a basic query end-to-end."""
        response = tracker.process_query(
            "Can I take aspirin with ibuprofen?",
            use_llm_summary=False
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        # Should include disclaimer
        assert "medical advice" in response.lower() or "healthcare provider" in response.lower()
    
    def test_process_query_with_grapefruit(self, tracker):
        """Test processing a query about grapefruit interactions."""
        response = tracker.process_query(
            "Is it safe to eat grapefruit while on statins?",
            use_llm_summary=False
        )
        
        assert isinstance(response, str)
        assert "grapefruit" in response.lower() or "statins" in response.lower()
    
    def test_process_query_no_medications(self, tracker):
        """Test processing a query with no recognized medications."""
        response = tracker.process_query(
            "What is the weather today?",
            use_llm_summary=False
        )
        
        assert isinstance(response, str)
        # Should indicate that no medications were found
        assert "couldn't identify" in response.lower() or "rephrase" in response.lower()
    
    def test_process_query_warfarin_supplements(self, tracker):
        """Test processing a query about warfarin and supplements."""
        response = tracker.process_query(
            "What supplements should I avoid with warfarin?",
            use_llm_summary=False
        )
        
        assert isinstance(response, str)
        assert len(response) > 50  # Should have substantial content
