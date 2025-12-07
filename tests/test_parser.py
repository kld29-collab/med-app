"""
Tests for QueryParser module
"""

import pytest
from med_tracker.parser import QueryParser


class TestQueryParser:
    """Test cases for the QueryParser class."""
    
    def test_basic_parse_aspirin_ibuprofen(self):
        """Test parsing a simple drug interaction query."""
        parser = QueryParser(api_key=None)  # Use basic parser
        result = parser.parse_query("Can I take aspirin with ibuprofen?")
        
        assert "medications" in result
        assert "aspirin" in result["medications"]
        assert "ibuprofen" in result["medications"]
        assert result["query_type"] == "interaction_check"
    
    def test_basic_parse_grapefruit_statins(self):
        """Test parsing a drug-food interaction query."""
        parser = QueryParser(api_key=None)
        result = parser.parse_query("Is it safe to eat grapefruit while on statins?")
        
        assert "medications" in result
        assert "foods" in result
        assert "statins" in result["medications"]
        assert "grapefruit" in result["foods"]
    
    def test_basic_parse_warfarin_supplements(self):
        """Test parsing a query about supplements."""
        parser = QueryParser(api_key=None)
        result = parser.parse_query("What supplements interact with warfarin?")
        
        assert "medications" in result
        assert "warfarin" in result["medications"]
        assert result["query_type"] == "interaction_check"
    
    def test_basic_parse_no_medications(self):
        """Test parsing a query with no recognized medications."""
        parser = QueryParser(api_key=None)
        result = parser.parse_query("What is the weather today?")
        
        assert result["medications"] == []
        assert result["supplements"] == []
        assert result["foods"] == []
    
    def test_basic_parse_original_query_preserved(self):
        """Test that original query is preserved in result."""
        parser = QueryParser(api_key=None)
        query = "Can I combine aspirin and warfarin?"
        result = parser.parse_query(query)
        
        assert result["original_query"] == query
