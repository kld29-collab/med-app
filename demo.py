#!/usr/bin/env python3
"""
Demo script for Medication Interaction Tracker

Demonstrates the core functionality without requiring API keys.
Shows how the system parses queries, checks interactions, and generates summaries.
"""

from med_tracker import MedicationTracker


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_query(tracker, query):
    """Run a demo query and display results."""
    print(f"Query: \"{query}\"")
    print("-" * 70)
    response = tracker.process_query(query, use_llm_summary=False)
    print(response)
    print()


def main():
    """Run demonstration scenarios."""
    print_section("Medication Interaction Tracker - Demo")
    
    print("This demo shows the system working without API keys.")
    print("For full LLM features, set OPENAI_API_KEY in .env file.\n")
    
    # Initialize tracker without API keys
    tracker = MedicationTracker()
    
    # Example 1: Drug-Drug Interaction
    print_section("Example 1: Drug-Drug Interaction Check")
    demo_query(tracker, "Can I take aspirin with ibuprofen?")
    
    # Example 2: Drug-Food Interaction
    print_section("Example 2: Drug-Food Interaction Check")
    demo_query(tracker, "Is it safe to eat grapefruit while taking statins?")
    
    # Example 3: Drug-Supplement Interaction
    print_section("Example 3: Drug-Supplement Interaction Check")
    demo_query(tracker, "Can I take St John's Wort with warfarin?")
    
    # Example 4: Multiple Interactions
    print_section("Example 4: Complex Query with Multiple Items")
    demo_query(tracker, "I take warfarin and eat leafy greens daily. Can I also take vitamin K supplements?")
    
    # Example 5: Alcohol Interaction
    print_section("Example 5: Alcohol Interaction")
    demo_query(tracker, "Is it safe to drink alcohol while taking metformin?")
    
    print_section("Demo Complete")
    print("Key Features Demonstrated:")
    print("✓ Natural language query parsing")
    print("✓ Drug-drug interaction checking")
    print("✓ Drug-food interaction detection")
    print("✓ Drug-supplement interaction warnings")
    print("✓ Severity classification (High/Moderate/Low)")
    print("✓ Safety disclaimers")
    print("\nTo use the interactive mode, run: python run_tracker.py")
    print()


if __name__ == "__main__":
    main()
