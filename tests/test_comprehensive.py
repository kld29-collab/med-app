#!/usr/bin/env python
"""
Comprehensive test of DrugBank integration with multiple queries
Tests various drug combinations and edge cases
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.retrieval_agent import RetrievalAgent
from agents.query_interpreter import QueryInterpreter


def run_test_query(user_query: str, interpreter, retrieval_agent):
    """Run a single test query and display results."""
    
    print(f"\n{'='*60}")
    print(f"Query: {user_query}")
    print(f"{'='*60}\n")
    
    # Interpret query
    query_plan = interpreter.interpret_query(user_query)
    print(f"📋 Interpreted Query:")
    print(f"   Medications: {query_plan.get('medications', [])}")
    print(f"   Foods: {query_plan.get('foods', [])}")
    print(f"   Type: {query_plan.get('query_type')}\n")
    
    # Retrieve interactions
    results = retrieval_agent.retrieve_interactions(query_plan)
    
    # Display summary
    print(f"📊 Results:")
    print(f"   Drug-drug interactions: {len(results['drug_interactions'])}")
    print(f"   Food interactions: {len(results['food_interactions'])}")
    print(f"   FDA info: {len(results['fda_info'])}")
    print(f"   Web sources: {len(results['web_sources'])}\n")
    
    # Show drug interactions
    if results['drug_interactions']:
        print(f"⚠️  Drug-Drug Interactions:")
        for i, interaction in enumerate(results['drug_interactions'][:3], 1):
            drug1 = interaction.get('drug1_id', 'Unknown')
            drug2 = interaction.get('drug2_name', 'Unknown')
            desc = interaction.get('description', 'No description')[:60]
            confidence = interaction.get('confidence', 'unknown')
            print(f"   {i}. {drug1} ↔ {drug2}")
            print(f"      {desc}...")
            print(f"      (Confidence: {confidence})\n")
    else:
        print(f"   ℹ️  No drug-drug interactions found\n")
    
    # Show food interactions
    if results['food_interactions']:
        print(f"🍎 Food Interactions:")
        for i, interaction in enumerate(results['food_interactions'][:2], 1):
            med = interaction.get('medication', 'Unknown')
            food = interaction.get('food', 'Unknown')[:50]
            print(f"   {i}. {med} + {food}")
    else:
        print(f"   ℹ️  No food interactions found\n")
    
    # Show FDA warnings
    if results['fda_info']:
        print(f"\n📋 FDA Info:")
        for info in results['fda_info'][:1]:
            drug = info.get('drug_name', 'Unknown')
            warnings = len(info.get('warnings', []))
            print(f"   {drug}: {warnings} warning(s)")
    
    return results


def main():
    """Run comprehensive test suite."""
    
    print("\n" + "="*60)
    print("DrugBank Integration - Comprehensive Test Suite")
    print("="*60)
    
    # Initialize agents
    print("\n[Setup] Initializing agents...")
    query_interpreter = QueryInterpreter()
    retrieval_agent = RetrievalAgent()
    print("✓ Ready\n")
    
    # Test queries
    test_queries = [
        "Does aspirin interact with warfarin?",
        "Can I take ibuprofen with metformin?",
        "What are the side effects of lisinopril?",
        "Is there any food I should avoid with warfarin?",
        "Do statins interact with alcohol?",
    ]
    
    results_summary = []
    
    for query in test_queries:
        try:
            results = run_test_query(query, query_interpreter, retrieval_agent)
            results_summary.append({
                "query": query,
                "interactions": len(results['drug_interactions']),
                "food": len(results['food_interactions']),
                "fda": len(results['fda_info']),
                "success": True
            })
        except Exception as e:
            print(f"❌ Error processing query: {str(e)}\n")
            results_summary.append({
                "query": query,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60 + "\n")
    
    print(f"{'Query':<40} {'Drug Int':<10} {'Food':<8} {'FDA':<8}")
    print("-" * 70)
    
    for summary in results_summary:
        if summary['success']:
            query_short = summary['query'][:37] + "..." if len(summary['query']) > 40 else summary['query']
            print(f"{query_short:<40} {summary['interactions']:<10} {summary['food']:<8} {summary['fda']:<8}")
        else:
            query_short = summary['query'][:37] + "..." if len(summary['query']) > 40 else summary['query']
            print(f"{query_short:<40} ERROR")
    
    print("\n" + "="*60)
    successful = sum(1 for s in results_summary if s['success'])
    print(f"✅ Tests Completed: {successful}/{len(test_queries)} successful")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
