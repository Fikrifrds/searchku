# HNSW Vector Index Optimization Guide

## Current Configuration

Your HNSW index is currently configured with:
- **m = 16**: Number of connections per node
- **ef_construction = 64**: Size of the dynamic candidate list during construction

## Understanding HNSW Parameters

### 1. m (Maximum connections per node)
- **Current**: 16 (good default)
- **Range**: 4-64
- **Higher m**: Better recall, more memory usage, slower insertion
- **Lower m**: Faster insertion, less memory, potentially lower recall

### 2. ef_construction (Construction-time candidate list size)
- **Current**: 64 (moderate)
- **Range**: 32-500+
- **Higher ef_construction**: Better index quality, slower index building
- **Lower ef_construction**: Faster index building, potentially lower quality

### 3. ef (Query-time candidate list size)
- **Current**: Default (typically 64)
- **Range**: 1-1000+
- **Higher ef**: Better recall, slower queries
- **Lower ef**: Faster queries, potentially lower recall

## Pagination Impact on HNSW

### Traditional Pagination Issues
1. **OFFSET Performance**: Large OFFSETs become slower with traditional indices
2. **Vector Search**: HNSW maintains performance even with large offsets because it uses graph-based search

### Optimized Pagination Strategy

#### 1. Current Implementation (✅ Implemented)
```sql
-- Using LIMIT/OFFSET with HNSW
ORDER BY embedding_vector <=> query_vector
LIMIT :limit OFFSET :offset
```

#### 2. Alternative: Cursor-based Pagination
For very large datasets, consider cursor-based pagination:
```sql
-- Store the last similarity score and page_id from previous page
WHERE similarity_score < :last_score
   OR (similarity_score = :last_score AND page_id > :last_page_id)
ORDER BY similarity_score DESC, page_id ASC
LIMIT :limit
```

## Recommended Configurations by Use Case

### 1. High Recall (Research/Academic)
```sql
-- For maximum accuracy
WITH (m = 32, ef_construction = 200)
-- Runtime: SET hnsw.ef = 100
```

### 2. Balanced (Production Default) ✅ Current
```sql
-- Good balance of speed and accuracy
WITH (m = 16, ef_construction = 64)
-- Runtime: SET hnsw.ef = 64
```

### 3. High Speed (Real-time Applications)
```sql
-- For fastest queries
WITH (m = 8, ef_construction = 32)
-- Runtime: SET hnsw.ef = 32
```

### 4. Large Scale (Millions of vectors)
```sql
-- For very large datasets
WITH (m = 24, ef_construction = 128)
-- Runtime: SET hnsw.ef = 80
```

## Performance Tuning

### 1. Monitor Query Performance
```sql
-- Check query execution time
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM pages
ORDER BY embedding_vector <=> '[1,2,3...]'::vector
LIMIT 10;
```

### 2. Adjust Runtime ef Value
```sql
-- Set per session (temporary)
SET hnsw.ef = 100;

-- Set globally (permanent)
ALTER SYSTEM SET hnsw.ef = 100;
SELECT pg_reload_conf();
```

### 3. Memory Usage Monitoring
```sql
-- Check index size
SELECT schemaname, tablename, indexname,
       pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE indexname LIKE '%hnsw%';
```

## Migration Scripts for Different Configurations

### High Recall Configuration
```sql
-- migrations/004_optimize_hnsw_high_recall.sql
DROP INDEX IF EXISTS idx_pages_embedding_vector_hnsw;
CREATE INDEX idx_pages_embedding_vector_hnsw ON pages
USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 32, ef_construction = 200);
```

### High Speed Configuration
```sql
-- migrations/004_optimize_hnsw_high_speed.sql
DROP INDEX IF EXISTS idx_pages_embedding_vector_hnsw;
CREATE INDEX idx_pages_embedding_vector_hnsw ON pages
USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 8, ef_construction = 32);
```

## Benchmarking Your Configuration

### 1. Test Different ef Values
```python
import time
import psycopg2

def benchmark_search(ef_value, query_vector, iterations=10):
    # Set ef value
    cursor.execute(f"SET hnsw.ef = {ef_value}")

    times = []
    for _ in range(iterations):
        start = time.time()
        cursor.execute("""
            SELECT page_id, 1 - (embedding_vector <=> %s) as similarity
            FROM pages
            ORDER BY embedding_vector <=> %s
            LIMIT 20
        """, (query_vector, query_vector))
        results = cursor.fetchall()
        times.append(time.time() - start)

    return {
        'ef': ef_value,
        'avg_time': sum(times) / len(times),
        'results_count': len(results)
    }

# Test different ef values
for ef in [16, 32, 64, 100, 200]:
    stats = benchmark_search(ef, your_test_vector)
    print(f"ef={ef}: {stats['avg_time']:.3f}s avg, {stats['results_count']} results")
```

### 2. Pagination Performance Test
```python
def test_pagination_performance(limit=10):
    offsets = [0, 100, 1000, 5000, 10000]

    for offset in offsets:
        start = time.time()
        cursor.execute("""
            SELECT page_id FROM pages
            ORDER BY embedding_vector <=> %s
            LIMIT %s OFFSET %s
        """, (test_vector, limit, offset))
        duration = time.time() - start
        print(f"Offset {offset}: {duration:.3f}s")
```

## Production Recommendations

### 1. Start with Current Settings (m=16, ef_construction=64)
- Good balance for most use cases
- Monitor performance in production

### 2. Optimize Based on Usage Patterns
- **High query volume**: Lower ef (32-48)
- **Research/precision critical**: Higher ef (100-200)
- **Large result sets**: Consider cursor-based pagination

### 3. Regular Monitoring
```sql
-- Add to monitoring dashboard
SELECT
    schemaname, tablename, indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_indexes
WHERE indexname LIKE '%hnsw%';
```

## Environment-Specific Configuration

### Development
```sql
-- Faster rebuilds for development
WITH (m = 8, ef_construction = 32)
```

### Staging
```sql
-- Match production settings
WITH (m = 16, ef_construction = 64)
```

### Production
```sql
-- Optimized for your specific workload
WITH (m = 16, ef_construction = 64)  -- Current
-- OR adjust based on benchmarks
```

## Key Takeaways for Your Implementation

1. **Pagination Performance**: HNSW handles OFFSET well, your current implementation is efficient
2. **Current Config**: m=16, ef_construction=64 is a solid starting point
3. **Runtime Tuning**: Adjust `hnsw.ef` based on speed vs accuracy needs
4. **Monitoring**: Track query performance and adjust accordingly
5. **Scale Considerations**: Current config should handle hundreds of thousands of vectors well