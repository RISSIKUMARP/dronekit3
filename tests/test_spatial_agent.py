"""
Test script for Spatial Agent tools.
Run this before integrating with DroneKit to verify spatial queries work.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import spatial tools directly for basic tests
from agents.spatial_agent import spatial_tools
from tools.geojson_db import TargetStore


def test_target_store_directly():
    """Test TargetStore class methods directly."""
    
    print("Testing TargetStore Class Methods\n")
    print("=" * 50)
    
    # Initialize store
    geojson_path = Path(__file__).parent.parent / "data" / "targets.geojson"
    store = TargetStore(str(geojson_path))
    
    # Test 1: nearest() method
    print("\nTEST 1: TargetStore.nearest()")
    print("=" * 50)
    test_coords = [
        (40.0150, -105.2050, "Near Rocky Ridge"),
        (40.0300, -105.2200, "Near Boulder Creek"),
    ]
    
    for lat, lon, desc in test_coords:
        result = store.nearest(lat, lon)
        if result:
            print(f"\n{desc} ({lat}, {lon})")
            print(f"  Nearest: {result['properties']['name']}")
            print(f"  Distance: {result['distance_m']:.1f}m")
            print(f"  Type: {result['properties']['target_type']}")
    
    # Test 2: find_by_name() method
    print("\n\nTEST 2: TargetStore.find_by_name()")
    print("=" * 50)
    test_names = ["Rocky Ridge", "Boulder Creek", "Invalid"]
    
    for name in test_names:
        result = store.find_by_name(name)
        if result:
            print(f"\n'{name}' -> Found: {result['properties']['name']}")
            print(f"  ID: {result['id']}")
            print(f"  Visits: {result['properties']['visit_count']}")
        else:
            print(f"\n'{name}' -> Not found")
    
    # Test 3: list_all() method with filters
    print("\n\nTEST 3: TargetStore.list_all()")
    print("=" * 50)
    
    high_priority = store.list_all(priority="high")
    print(f"\nHigh priority targets: {len(high_priority)}")
    for t in high_priority:
        print(f"  - {t['properties']['name']}")
    
    unvisited = store.list_all(max_visits=0)
    print(f"\nUnvisited targets: {len(unvisited)}")
    for t in unvisited:
        print(f"  - {t['properties']['name']}")


def test_agent_integration():
    """Test Spatial Agent with Agno framework."""
    
    print("\n\n" + "=" * 50)
    print("Testing Agno Agent Integration")
    print("=" * 50)
    
    if not os.environ.get('OPENROUTER_API_KEY'):
        print("\nSkipping agent test - OPENROUTER_API_KEY not set")
        print("Set the key to test full agent integration:")
        print("  set OPENROUTER_API_KEY=your-key-here")
        return
    
    # Try importing Agno
    try:
        from agno import Agent
        from agno.models.openrouter import OpenRouter
    except ImportError as e:
        print(f"\nSkipping agent test - Agno import error: {e}")
        print("\nTo fix, run:")
        print("  pip install --upgrade agno")
        return
    
    agent = Agent(
        name='SpatialAgent',
        model=OpenRouter(
            id='google/gemini-2.0-flash-001',
            api_key=os.environ['OPENROUTER_API_KEY'],
        ),
        instructions="""You are a spatial query agent for conservation monitoring.
        You can find targets near GPS coordinates, lookup targets by name, and list targets.
        Answer queries concisely with relevant target information.""",
        tools=spatial_tools,
        debug_mode=False
    )
    
    test_queries = [
        "What's the nearest target to coordinates 40.0150, -105.2050?",
        "Tell me about Rocky Ridge Wildlife Habitat",
        "List all high priority targets that haven't been visited yet"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = agent.run(query)
        print(f"Response: {result.content}\n")


if __name__ == "__main__":
    # Test TargetStore class directly
    test_target_store_directly()

    # Test agent integration if API key available
    test_agent_integration()
    
    print("\n" + "=" * 50)
    print("Testing Complete")
    print("=" * 50)
