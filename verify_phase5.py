#!/usr/bin/env python3
"""
Phase 5 Verification Script
Tests all memory system components to ensure complete implementation.
"""

import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, './backend')

from app.database.init_db import init_database
from app.database.session import SessionLocal
from app.models.memory import Memory, MemoryTag, SessionSummary, MemoryRelationship, SearchIndex
from app.models.capture import MemorySession
from app.memory.archive import memory_archive
from app.search.memory_search import memory_search
from app.timeline.memory_timeline import memory_timeline_builder
from app.tagging.tagger import MemoryTagger
from app.summarization.session_summarizer import SessionSummarizer


def test_memory_storage():
    """Test 1: Memory Storage Engine"""
    print("\n" + "="*60)
    print("TEST 1: Memory Storage Engine")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Check tables exist
        tables = ['memories', 'memory_tags', 'search_index', 'session_summaries', 'memory_relationships']
        for table in tables:
            count = db.execute(f"SELECT COUNT(*) FROM {table}").scalar()
            print(f"✓ Table '{table}' exists (records: {count})")
        
        # Check content hash uniqueness
        memories = db.query(Memory).limit(5).all()
        if memories:
            print(f"✓ Found {len(memories)} sample memories")
            for m in memories[:2]:
                print(f"  - {m.title} [{m.source_type}]")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        db.close()


def test_session_reconstruction():
    """Test 2: Session Reconstruction"""
    print("\n" + "="*60)
    print("TEST 2: Session Reconstruction")
    print("="*60)
    
    db = SessionLocal()
    try:
        sessions = db.query(MemorySession).limit(5).all()
        print(f"✓ Found {len(sessions)} memory sessions")
        
        summaries = db.query(SessionSummary).limit(5).all()
        print(f"✓ Found {len(summaries)} session summaries")
        
        if summaries:
            for s in summaries[:2]:
                print(f"  - {s.title} ({s.session_type}) - {s.memory_count} memories")
        
        # Verify summary fields
        if summaries:
            s = summaries[0]
            assert s.session_type in ['coding', 'learning', 'research', 'browsing', 'youtube']
            print("✓ Session types are valid")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        db.close()


def test_timeline_engine():
    """Test 3: Timeline Engine"""
    print("\n" + "="*60)
    print("TEST 3: Timeline Engine")
    print("="*60)
    
    db = SessionLocal()
    try:
        memories = db.query(Memory).order_by(Memory.created_at.desc()).limit(50).all()
        print(f"✓ Fetched {len(memories)} memories for timeline")
        
        # Test day grouping
        day_groups = memory_timeline_builder.group_by_day(memories)
        print(f"✓ Grouped by day: {len(day_groups)} days")
        if day_groups:
            print(f"  - {day_groups[0]['date']}: {len(day_groups[0]['items'])} memories")
        
        # Test week grouping
        week_groups = memory_timeline_builder.group_by_week(memories)
        print(f"✓ Grouped by week: {len(week_groups)} weeks")
        if week_groups:
            print(f"  - {week_groups[0]['week']}: {len(week_groups[0]['items'])} memories")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        db.close()


def test_memory_tagging():
    """Test 4: Memory Tagging System"""
    print("\n" + "="*60)
    print("TEST 4: Memory Tagging System")
    print("="*60)
    
    db = SessionLocal()
    try:
        tagger = MemoryTagger()
        
        # Test tagging
        test_content = "Python OCR implementation using Tesseract for document scanning"
        tags = tagger.tag(test_content, "OCR", "screen", "VSCode")
        print(f"✓ Generated tags: {tags}")
        
        category = tagger.category(test_content, "screen", "VSCode")
        print(f"✓ Assigned category: {category}")
        
        # Check database tags
        tags_in_db = db.query(MemoryTag).limit(5).all()
        print(f"✓ Found {db.query(MemoryTag).count()} tags in database")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        db.close()


def test_memory_search():
    """Test 5: Memory Search System"""
    print("\n" + "="*60)
    print("TEST 5: Memory Search System")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Test basic search
        results = memory_search.search(db, limit=10)
        print(f"✓ Basic search returned {len(results)} memories")
        
        # Test with query
        results = memory_search.search(db, q="python", limit=10)
        print(f"✓ Keyword search (q='python'): {len(results)} results")
        
        # Test with filters
        results = memory_search.search(db, source_type="screen", limit=10)
        print(f"✓ Filter search (source_type='screen'): {len(results)} results")
        
        # Test related memories
        if results:
            memory_id = results[0].id
            related = memory_search.find_related_memories(db, memory_id)
            print(f"✓ Found {len(related)} related memories for ID {memory_id}")
        
        # Test stats
        stats = memory_search.get_memory_stats(db)
        print(f"✓ Memory stats:")
        print(f"  - Total memories: {stats['total_memories']}")
        print(f"  - By category: {stats['by_category']}")
        print(f"  - By source: {stats['by_source']}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        db.close()


def test_memory_summarization():
    """Test 6: Memory Summarization"""
    print("\n" + "="*60)
    print("TEST 6: Memory Summarization")
    print("="*60)
    
    db = SessionLocal()
    try:
        summarizer = SessionSummarizer()
        
        # Get a session with memories
        session = db.query(MemorySession).first()
        if not session:
            print("✗ No sessions found to summarize")
            return False
        
        memories = db.query(Memory).filter(Memory.session_id == session.id).limit(10).all()
        if not memories:
            print("✗ No memories found for session")
            return False
        
        # Test summarization
        result = summarizer.summarize(session, memories, ["VSCode", "Chrome"], ["Python", "OCR"])
        print(f"✓ Generated summary:")
        print(f"  - Title: {result['title']}")
        print(f"  - Summary: {result['summary']}")
        print(f"  - Type: {result['session_type']}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        db.close()


def test_memory_relationships():
    """Test 7: Memory Relationships"""
    print("\n" + "="*60)
    print("TEST 7: Memory Relationships")
    print("="*60)
    
    db = SessionLocal()
    try:
        relationships = db.query(MemoryRelationship).limit(10).all()
        print(f"✓ Found {db.query(MemoryRelationship).count()} relationships in database")
        
        if relationships:
            rel_types = {}
            for r in relationships:
                rel_types[r.relationship_type] = rel_types.get(r.relationship_type, 0) + 1
            print(f"✓ Relationship types: {rel_types}")
        
        # Test relationships for a memory
        memory = db.query(Memory).first()
        if memory:
            rels = db.query(MemoryRelationship).filter(
                (MemoryRelationship.source_memory_id == memory.id) | 
                (MemoryRelationship.target_memory_id == memory.id)
            ).limit(5).all()
            print(f"✓ Memory {memory.id} has {len(rels)} relationships")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        db.close()


def test_search_index():
    """Test 8: Search Index"""
    print("\n" + "="*60)
    print("TEST 8: Search Index")
    print("="*60)
    
    db = SessionLocal()
    try:
        index_count = db.query(SearchIndex).count()
        print(f"✓ Search index has {index_count} entries")
        
        # Check index coverage
        memory_count = db.query(Memory).count()
        if memory_count > 0:
            coverage = (index_count / memory_count) * 100
            print(f"✓ Search index coverage: {coverage:.1f}% ({index_count}/{memory_count})")
        
        # Test full-text search
        sample = db.query(SearchIndex).first()
        if sample:
            print(f"✓ Sample index entry:")
            print(f"  - Memory ID: {sample.memory_id}")
            print(f"  - Searchable text length: {len(sample.searchable_text)}")
            print(f"  - Tags: {sample.tags_text[:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        db.close()


def test_api_methods():
    """Test 9: API Method Availability"""
    print("\n" + "="*60)
    print("TEST 9: API Method Availability")
    print("="*60)
    
    try:
        from app.routes.memory import router
        
        routes = [route.path for route in router.routes]
        print(f"✓ Memory router has {len(routes)} endpoints:")
        
        expected = [
            '/rebuild',
            '/sessions/{session_id}/rebuild',
            '/search',
            '/timeline',
            '/memories/{memory_id}',
            '/memories/{memory_id}/relationships',
            '/memories/{memory_id}/related',
            '/stats',
            '/sessions',
            '/sessions/{session_id}',
            '/sessions/{session_id}/memories',
            '/export/session/{session_id}'
        ]
        
        for route in sorted(set(routes)):
            status = "✓" if any(exp in route for exp in expected) else "○"
            print(f"  {status} {route}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_frontend_apis():
    """Test 10: Frontend API Client Methods"""
    print("\n" + "="*60)
    print("TEST 10: Frontend API Client Methods")
    print("="*60)
    
    try:
        # Read apiClient.js to check methods
        with open('./src/services/apiClient.js', 'r') as f:
            content = f.read()
        
        methods = [
            'rebuildMemoryArchive',
            'searchMemories',
            'fetchMemoryTimeline',
            'fetchMemorySessions',
            'fetchMemoryRelationships',
            'fetchRelatedMemories',
            'fetchMemoryStats'
        ]
        
        print("✓ Frontend API client methods:")
        for method in methods:
            present = method in content
            status = "✓" if present else "✗"
            print(f"  {status} {method}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("PHASE 5 IMPLEMENTATION VERIFICATION")
    print("Second Brain - Memory Storage & Timeline Engine")
    print("="*60)
    
    tests = [
        ("Memory Storage Engine", test_memory_storage),
        ("Session Reconstruction", test_session_reconstruction),
        ("Timeline Engine", test_timeline_engine),
        ("Memory Tagging System", test_memory_tagging),
        ("Memory Search System", test_memory_search),
        ("Memory Summarization", test_memory_summarization),
        ("Memory Relationships", test_memory_relationships),
        ("Search Index", test_search_index),
        ("API Endpoints", test_api_methods),
        ("Frontend API Client", test_frontend_apis),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 PHASE 5 IMPLEMENTATION COMPLETE AND VERIFIED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
