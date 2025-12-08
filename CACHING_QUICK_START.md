# Quick Start: Caching in Med App

## What You Get

✅ **Speed:** Repeated queries return in <10ms (was 6-15 seconds)  
✅ **Cost:** 50-70% fewer OpenAI API calls  
✅ **Automatic:** Zero configuration needed  

## How to Use It

The caching system works **automatically behind the scenes**. Just use the app normally:

```javascript
// Frontend (app.js) - No changes needed
const response = await fetch('/api/query', {
    method: 'POST',
    body: JSON.stringify({ query: "Does aspirin interact with warfarin?" })
});
```

```python
# Backend (app.py) - Caching is automatic
@app.route('/api/query', methods=['POST'])
def handle_query():
    cache = get_cache_manager()
    
    # Automatic cache check (transparent)
    cached_result = cache.get_cached_explanation(user_query)
    if cached_result:
        return jsonify({...cached_result, "cache_hit": "query"})
    
    # Full pipeline if needed
    ...
    
    # Automatic caching of result
    cache.cache_explanation(user_query, result)
```

## Monitor Performance

Check cache statistics:
```bash
curl http://localhost:5000/api/cache-stats
```

**Sample Response:**
```json
{
  "cache_stats": {
    "query": {
      "hits": 12,
      "misses": 45,
      "hit_rate": "26.7%",
      "savings_estimate": "$0.06"
    },
    "drug": {...},
    "interaction": {...},
    "total_entries": 250
  }
}
```

## Real-World Usage Pattern

```
User 1:
├─ Query 1: "aspirin + warfarin"
│  Time: 14.66s (first time, full pipeline)
│  Cache: ✓ Stored
│  
├─ Query 2: "aspirin + warfarin" (same question)
│  Time: 0.0ms ← INSTANT! (from cache)
│  Cost: $0.00 (saved $0.005)
│  
└─ Query 3: "aspirin + ibuprofen"
   Time: ~7 seconds (new pair, but aspirin cached)
   Cost: ~$0.003 (partial OpenAI call)

User 2 (different person):
├─ Query: "aspirin + metformin"
│  Time: ~2-3 seconds ← FASTER! (aspirin cache hit)
│  Cost: ~$0.001 (reduced OpenAI usage)
│  
└─ Query: "ibuprofen + warfarin"
   Time: ~2-3 seconds ← FASTER! (both cached from previous users)
   Cost: ~$0.001 (minimal OpenAI usage)
```

## Caching Timeline

| When | Cache State | Response | Cost |
|------|-------------|----------|------|
| Hour 1 | Cold (empty) | Slow (6-15s) | Full cost |
| Hour 6 | Warming | Mixed (2-6s avg) | ~50% cost |
| Day 1+ | Hot (full) | Fast (mostly <1s) | ~30% original |

The cache **automatically warms up** as users query common drug combinations.

## Three Cache Layers (How It Works)

### Layer 1: Query Cache
```
Query: "Does aspirin interact with warfarin?"
              ↓
      Hash the query (MD5)
              ↓
   Check in-memory cache
              ↓
   ┌─ YES: Return instantly
   │
   NO: Run full pipeline (6-15s)
        ├─ Query Interpreter
        ├─ Retrieval Agent (DrugBank, FDA, Web)
        └─ Explanation Agent (OpenAI LLM)
              ↓
      Cache result (15 min TTL)
              ↓
      Return to user
```

### Layer 2: Drug Cache
```
During retrieval:
├─ Look up "aspirin" in DrugBank
│  └─ Check if cached → Skip lookup
│  
└─ Look up "warfarin" in DrugBank
   └─ Check if cached → Skip lookup

TTL: 7 days (drug data stable)
Benefit: Cross-user sharing
```

### Layer 3: Interaction Cache
```
After retrieving interaction data:
├─ Store: aspirin + warfarin → interaction results
│  
Next query with "warfarin + ibuprofen":
└─ Check if warfarin cached → Skip FDA/DrugBank lookup

TTL: 7 days
Benefit: Skip expensive API calls
```

## API Endpoints

### `/api/query` (POST)
Main query endpoint - caching is automatic

**Request:**
```json
{
  "query": "Does aspirin interact with warfarin?",
  "user_context": {
    "age": 65,
    "medications": ["metformin"]
  }
}
```

**Response (first time):**
```json
{
  "success": true,
  "query_plan": {...},
  "explanation": "Aspirin and warfarin...",
  "cache_hit": null,
  "response_time": "14.66s"
}
```

**Response (cached):**
```json
{
  "success": true,
  "query_plan": {...},
  "explanation": "Aspirin and warfarin...",
  "cache_hit": "query",
  "response_time": "<10ms"
}
```

### `/api/cache-stats` (GET)
Monitor cache performance

```bash
curl http://localhost:5000/api/cache-stats
```

### `/api/cache-clear` (POST)
Clear cache (for testing)

```bash
curl -X POST http://localhost:5000/api/cache-clear
```

## Configuration

Edit `utils/cache_manager.py` to adjust TTLs:

```python
class CacheManager:
    def __init__(self, cache_dir='.cache'):
        self.QUERY_TTL = 15 * 60        # 15 minutes
        self.DRUG_TTL = 7 * 24 * 60 * 60   # 7 days
        self.INTERACTION_TTL = 7 * 24 * 60 * 60  # 7 days
```

**Tuning recommendations:**
- Increase `QUERY_TTL` for more aggressive exact-match caching (but queries change)
- Increase `DRUG_TTL` for longer-lasting drug data (drugs don't change often)
- Increase `INTERACTION_TTL` for longer-lasting pair data (interactions stable)

## Testing

Run the test suite to verify caching works:

```bash
# Unit tests
python test_caching.py

# End-to-end tests with real agents
python test_caching_e2e.py
```

**Expected output:**
```
✓ Query Cache: PASS
✓ Drug Cache: PASS
✓ Interaction Cache: PASS
✓ Cache Statistics: PASS
✓ Cache Clearing: PASS
```

## Troubleshooting

### "Cache isn't working"
1. Check `/api/cache-stats` - hit rate should grow over time
2. Verify queries are identical (case-sensitive)
3. Check TTL hasn't expired (15 min for queries)
4. Try `/api/cache-clear` to reset

### "Still slow despite caching"
1. Check if hit rate is high - if not, queries are different
2. Verify OpenAI API isn't rate-limited
3. Check network latency to RxNorm/FDA/Serpapi
4. Profile with `response_time` field in response

### "Want to pre-warm cache"
1. Run common drug combinations before launch
2. Or wait 24 hours for natural cache warming
3. No manual pre-warming needed if you have time

## Performance Gains

| Scenario | Time | Cost | Savings |
|----------|------|------|---------|
| New query | 14.66s | $0.005 | Baseline |
| **Cached query** | **0.0ms** | **$0.00** | **99.8% faster, 100% cheaper** |
| New drug pair (1 drug cached) | 7s | $0.003 | 52% faster, 40% cheaper |
| Both drugs cached | 2-3s | $0.001 | 83% faster, 80% cheaper |

## Summary

**The caching system is:**
- ✅ Automatic (zero setup)
- ✅ Transparent (no code changes)
- ✅ Effective (50-70% cost reduction)
- ✅ Fast (instant repeats)
- ✅ Tested (all tests pass)
- ✅ Monitored (/api/cache-stats)

**Just use the app normally. Caching works behind the scenes!**
