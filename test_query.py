#!/usr/bin/env python
"""
Quick test of DrugBank integration with retrieval agent
Tests the complete query flow: normalization → DrugBank → FDA → web search
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.retrieval_agent import RetrievalAgent
from agents.query_interpreter import QueryInterpreter
import json


def test_drugbank_integration():
    """Test the complete medication interaction query flow."""
    
    print("\n" + "="*60)
    print("DrugBank Integration Test")
    print("="*60 + "\n")
    
    # Initialize agents
    print("[1/3] Initializing agents...")
    query_interpreter = QueryInterpreter()
    retrieval_agent = RetrievalAgent()
    print("✓ Agents initialized\n")
    
    # Test query
    user_query = "Does aspirin interact with warfarin? What about food?"
    print(f"[2/3] Processing query: '{user_query}'\n")
    
    # Step 1: Interpret query
    print("Step A: Query Interpretation (LLM)")
    print("-" * 40)
    query_plan = query_interpreter.interpret_query(user_query)
    print(f"Extracted medications: {query_plan.get('medications', [])}")
    print(f"Extracted foods: {query_plan.get('foods', [])}")
    print(f"Query type: {query_plan.get('query_type')}\n")
    
    # Step 2: Retrieve interactions
    print("Step B: Retrieval (DrugBank → FDA → Web)")
    print("-" * 40)
    results = retrieval_agent.retrieve_interactions(query_plan)
    
    # Display results
    print(f"\nData Sources Used:")
    for source in results["metadata"]["sources_queried"]:
        print(f"  ✓ {source}")
    
    print(f"\n📊 Results Summary:")
    print(f"  - Normalized medications: {len(results['normalized_medications'])}")
    print(f"  - Drug-drug interactions: {len(results['drug_interactions'])}")
    print(f"  - Food interactions: {len(results['food_interactions'])}")
    print(f"  - FDA info sources: {len(results['fda_info'])}")
    print(f"  - Web sources: {len(results['web_sources'])}")
    
    # Show details if we have interactions
    print(f"\n📋 Detailed Results:")
    print("-" * 40)
    
    if results['normalized_medications']:
        print(f"\nNormalized Medications:")
        for med in results['normalized_medications']:
            print(f"  • {med.get('original_name', 'N/A')} → {med.get('normalized_name', 'N/A')}")
            if med.get('rxcui'):
                print(f"    (RxCUI: {med['rxcui']})")
    
    if results['drug_interactions']:
        print(f"\nDrug-Drug Interactions (from DrugBank):")
        for interaction in results['drug_interactions'][:5]:  # Show first 5
            drug1 = interaction.get('drug1_id', 'Unknown')
            drug2 = interaction.get('drug2_name', 'Unknown')
            desc = interaction.get('description', 'No description')[:60]
            source = interaction.get('source', 'Unknown')
            print(f"  ⚠️  {drug1} ↔ {drug2}")
            print(f"     {desc}...")
            print(f"     (Source: {source})\n")
    
    if results['food_interactions']:
        print(f"\nFood-Drug Interactions (from DrugBank):")
        for interaction in results['food_interactions'][:5]:  # Show first 5
            med = interaction.get('medication', 'Unknown')
            food = interaction.get('food', 'Unknown')
            confidence = interaction.get('confidence', 'Unknown')
            print(f"  🍎 {med} + {food}")
            print(f"     Confidence: {confidence}\n")
    
    if results['fda_info']:
        print(f"\nFDA Safety Information:")
        for info in results['fda_info'][:2]:  # Show first 2
            drug = info.get('drug_name', 'Unknown')
            warnings = len(info.get('warnings', []))
            interactions = len(info.get('drug_interactions', []))
            print(f"  📋 {drug}")
            print(f"     Warnings: {warnings}, Drug Interactions: {interactions}\n")
    
    if results['web_sources']:
        print(f"\nWeb Search Results (Supplementary):")
        for source in results['web_sources'][:3]:  # Show first 3
            title = source.get('title', 'N/A')[:50]
            url = source.get('url', 'N/A')
            print(f"  🔗 {title}...")
            print(f"     {url}\n")
    
    # Step 3: Show interaction table
    print("\nInteraction Table:")
    print("-" * 40)
    interaction_table = results.get('interaction_table', [])
    if interaction_table:
        for entry in interaction_table[:5]:  # Show first 5
            entry_type = entry.get('type', 'unknown').upper()
            item1 = entry.get('item1', 'N/A')
            item2 = entry.get('item2', 'N/A')
            severity = entry.get('severity', 'unknown')
            source = entry.get('source', 'unknown')
            print(f"  [{entry_type}] {item1} ↔ {item2}")
            print(f"           Severity: {severity}, Source: {source}\n")
    else:
        print("  (No interactions in table)")
    
    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60 + "\n")
    
    return results


if __name__ == "__main__":
    try:
        results = test_drugbank_integration()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
