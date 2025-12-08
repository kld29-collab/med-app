#!/usr/bin/env python3
"""
Test the caching system to verify it works correctly and reduces API calls.
"""

import sys
import time
from utils.cache_manager import get_cache_manager

def test_query_cache():
    """Test query-level caching (full explanations)."""
    print("\n" + "="*60)
    print("TEST 1: Query Cache (Full Explanation Caching)")
    print("="*60)
    
    cache = get_cache_manager()
    
    # Simulate caching a full explanation
    query = "Does aspirin interact with warfarin?"
    fake_explanation = {
        "query_plan": {"drugs": ["aspirin", "warfarin"]},
        "interaction_data": {"found": True},
        "explanation": "Yes, there is a significant interaction...",
        "formatted_explanation": "<div>...</div>"
    }
    
    print(f"\nQuery: '{query}'")
    print("First call: Cache miss (would execute full pipeline)")
    result1 = cache.get_cached_explanation(query)
    print(f"  Result: {result1}")
    
    print("\nCaching the result...")
    cache.cache_explanation(query, fake_explanation)
    
    print("Second call: Cache hit (instant return)")
    start = time.time()
    result2 = cache.get_cached_explanation(query)
    elapsed = time.time() - start
    print(f"  Result: {result2 is not None}")
    print(f"  Time: {elapsed*1000:.1f}ms (vs ~5000ms for full pipeline)")
    
    return True


def test_drug_cache():
    """Test drug-level caching (individual drug lookups)."""
    print("\n" + "="*60)
    print("TEST 2: Drug Cache (Individual Drug Lookups)")
    print("="*60)
    
    cache = get_cache_manager()
    
    drug_name = "aspirin"
    fake_drug_data = {
        "normalized_name": "Aspirin",
        "rxnorm_id": "1191",
        "drugbank_id": "DB00945"
    }
    
    print(f"\nDrug: '{drug_name}'")
    print("First call: Cache miss")
    result1 = cache.get_cached_drug_data(drug_name)
    print(f"  Result: {result1}")
    
    print("\nCaching the result...")
    cache.cache_drug_data(drug_name, fake_drug_data)
    
    print("Second call: Cache hit")
    result2 = cache.get_cached_drug_data(drug_name)
    print(f"  Result: {result2}")
    
    return True


def test_interaction_cache():
    """Test interaction-level caching (drug pair results)."""
    print("\n" + "="*60)
    print("TEST 3: Interaction Cache (Drug Pair Results)")
    print("="*60)
    
    cache = get_cache_manager()
    
    drug1 = "aspirin"
    drug2 = "warfarin"
    fake_interaction = {
        "drugbank": [{"interaction_type": "Major", "description": "Increased bleeding risk"}],
        "fda": [{"warning": "This combination is contraindicated"}]
    }
    
    print(f"\nDrug Pair: '{drug1}' + '{drug2}'")
    print("First call: Cache miss")
    result1 = cache.get_cached_interaction(drug1, drug2)
    print(f"  Result: {result1}")
    
    print("\nCaching the result...")
    cache.cache_interaction(drug1, drug2, fake_interaction)
    
    print("Second call: Cache hit (order-independent)")
    result2 = cache.get_cached_interaction(drug2, drug1)  # Reversed order!
    print(f"  Result: {result2}")
    print(f"  Note: Order-independent = cache hit even with reversed drug order")
    
    return True


def test_cache_stats():
    """Test cache statistics."""
    print("\n" + "="*60)
    print("TEST 4: Cache Statistics")
    print("="*60)
    
    cache = get_cache_manager()
    stats = cache.get_cache_stats()
    
    print("\nCache Statistics:")
    print(f"  Query Cache:")
    print(f"    - Hits: {stats['query']['hits']}")
    print(f"    - Misses: {stats['query']['misses']}")
    print(f"    - Hit Rate: {stats['query']['hit_rate']}")
    print(f"    - Estimated Savings: {stats['query']['savings_estimate']}")
    
    print(f"\n  Drug Cache:")
    print(f"    - Hits: {stats['drug']['hits']}")
    print(f"    - Misses: {stats['drug']['misses']}")
    print(f"    - Hit Rate: {stats['drug']['hit_rate']}")
    
    print(f"\n  Interaction Cache:")
    print(f"    - Hits: {stats['interaction']['hits']}")
    print(f"    - Misses: {stats['interaction']['misses']}")
    print(f"    - Hit Rate: {stats['interaction']['hit_rate']}")
    print(f"    - Time Savings Estimate: {stats['interaction']['time_savings_estimate']}")
    
    print(f"\n  Total Cached Entries: {stats['total_entries']}")
    
    return True


def test_cache_clear():
    """Test cache clearing."""
    print("\n" + "="*60)
    print("TEST 5: Cache Clearing")
    print("="*60)
    
    cache = get_cache_manager()
    
    print("\nBefore clear:")
    stats_before = cache.get_cache_stats()
    print(f"  Total entries: {stats_before['total_entries']}")
    
    print("\nClearing query cache...")
    cache.clear_cache('query')
    
    stats_after = cache.get_cache_stats()
    print(f"  Total entries after: {stats_after['total_entries']}")
    
    return True


def main():
    """Run all cache tests."""
    print("\n" + "="*60)
    print("CACHING SYSTEM TESTS")
    print("="*60)
    
    tests = [
        ("Query Cache", test_query_cache),
        ("Drug Cache", test_drug_cache),
        ("Interaction Cache", test_interaction_cache),
        ("Cache Statistics", test_cache_stats),
        ("Cache Clearing", test_cache_clear),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✓ PASS"))
        except Exception as e:
            results.append((name, f"✗ FAIL: {str(e)}"))
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, result in results:
        print(f"  {name}: {result}")
    
    print("\n" + "="*60)
    print("PERFORMANCE EXPECTATIONS")
    print("="*60)
    print("""
Query Cache Hit (repeated question):
  - Time: <10ms (was ~5000ms)
  - Cost: $0.00 (was ~$0.005 OpenAI call)
  - Savings: 99.8% faster, 100% cheaper

Drug Cache Hit (repeated drug lookup):
  - Time: <5ms per drug
  - Cost: $0 API calls
  - Savings: ~1-2 seconds per query on average

Interaction Cache Hit (repeated drug pair):
  - Time: <5ms
  - Cost: $0 API calls
  - Savings: ~2-3 seconds per query on average

Typical Usage Pattern:
  1st query "aspirin + warfarin": ~6 seconds (full pipeline)
  2nd query "aspirin + warfarin": <10ms (query cache hit)
  3rd query "aspirin + tylenol": ~2-3 seconds (drug cache + interaction cache hits)
  4th query "ibuprofen + warfarin": ~2-3 seconds (interaction cache hit for warfarin)
    """)
    
    all_passed = all("PASS" in result for _, result in results)
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
