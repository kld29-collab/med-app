#!/usr/bin/env python3
"""
Example: Programmatic Usage of Medication Interaction Tracker

Shows how to use the tracker as a library in your own Python code.
"""

from med_tracker import MedicationTracker, QueryParser, InteractionChecker

def example_1_simple_usage():
    """Example 1: Simple end-to-end usage."""
    print("=" * 70)
    print("Example 1: Simple Usage")
    print("=" * 70)
    
    tracker = MedicationTracker()
    result = tracker.process_query(
        "Can I take aspirin with warfarin?",
        use_llm_summary=False
    )
    print(result)
    print()


def example_2_component_usage():
    """Example 2: Using individual components."""
    print("=" * 70)
    print("Example 2: Using Individual Components")
    print("=" * 70)
    
    # Step 1: Parse query
    parser = QueryParser(api_key=None)
    parsed = parser.parse_query("Is grapefruit safe with statins?")
    print(f"Parsed query: {parsed}")
    
    # Step 2: Check interactions
    checker = InteractionChecker()
    interactions = checker.check_interactions(
        medications=parsed['medications'],
        supplements=parsed['supplements'],
        foods=parsed['foods']
    )
    print(f"\nFound {interactions['summary']['total_interactions']} interactions")
    print(f"High severity: {interactions['summary']['high_severity_count']}")
    print()


def example_3_custom_entities():
    """Example 3: Directly specify medications/supplements/foods."""
    print("=" * 70)
    print("Example 3: Direct Entity Specification")
    print("=" * 70)
    
    checker = InteractionChecker()
    
    # Check specific combination
    result = checker.check_interactions(
        medications=["warfarin", "aspirin"],
        supplements=["vitamin K"],
        foods=["leafy greens", "alcohol"]
    )
    
    print(f"Checking: warfarin + aspirin + vitamin K + leafy greens + alcohol")
    print(f"Total interactions: {result['summary']['total_interactions']}")
    
    # Show drug-food interactions
    if result['drug_food_interactions']:
        print(f"\nDrug-Food Interactions:")
        for interaction in result['drug_food_interactions']:
            print(f"  - {interaction['medication']} + {interaction['food']}")
            print(f"    Severity: {interaction['severity']}")
            print(f"    {interaction['interaction']}")
    print()


def example_4_batch_checking():
    """Example 4: Check multiple medication combinations."""
    print("=" * 70)
    print("Example 4: Batch Checking Multiple Combinations")
    print("=" * 70)
    
    checker = InteractionChecker()
    
    # List of medication combinations to check
    combinations = [
        (["aspirin", "ibuprofen"], "NSAIDs"),
        (["warfarin", "aspirin"], "Anticoagulants"),
        (["levothyroxine"], "Thyroid med alone"),
    ]
    
    for meds, description in combinations:
        result = checker.check_interactions(medications=meds)
        count = result['summary']['total_interactions']
        print(f"{description}: {count} interaction(s) found")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" Medication Interaction Tracker - Programmatic Usage Examples")
    print("=" * 70 + "\n")
    
    example_1_simple_usage()
    example_2_component_usage()
    example_3_custom_entities()
    example_4_batch_checking()
    
    print("=" * 70)
    print("For more information, see the README.md file")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
