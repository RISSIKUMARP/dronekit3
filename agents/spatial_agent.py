"""
Spatial Agent for conservation target queries.
Provides tools to find nearest targets and query the GeoJSON database.
"""

import json
from typing import Optional
from pathlib import Path
from agno.tools import tool
from tools.geojson_db import TargetStore
from tools.spatial_tools import format_distance


GEOJSON_PATH = Path(__file__).parent.parent / "data" / "targets.geojson"

# Module-level TargetStore instance (shared across all tool calls)
target_store = TargetStore(GEOJSON_PATH)


@tool
def get_nearest_target(lat: float, lon: float) -> str:
    """
    Find the conservation target closest to given GPS coordinates.
    
    Calculates Haversine distance from the provided position to all targets
    in the database and returns the nearest one with distance and metadata.
    
    Args:
        lat: Current latitude in decimal degrees
        lon: Current longitude in decimal degrees
    
    Returns:
        JSON string containing nearest target details and distance
    """
    try:
        nearest = target_store.nearest(lat, lon)
        
        if not nearest:
            return json.dumps({"error": "No targets in database"})
        
        # Build response with target details
        result = {
            "target_id": nearest['id'],
            "name": nearest['properties']['name'],
            "type": nearest['properties']['target_type'],
            "priority": nearest['properties']['priority'],
            "distance_m": nearest['distance_m'],
            "distance_readable": format_distance(nearest['distance_m']),
            "coordinates": {
                "lat": nearest['geometry']['coordinates'][1],
                "lon": nearest['geometry']['coordinates'][0]
            },
            "altitude_m": nearest['properties']['altitude_m'],
            "visit_count": nearest['properties']['visit_count'],
            "last_visited": nearest['properties'].get('last_visited'),
            "observation_count": len(nearest['properties']['observations'])
        }
        
        return json.dumps(result, indent=2)
    
    except ValueError as e:
        return json.dumps({"error": str(e)})


@tool
def get_target_by_name(name: str) -> str:
    """
    Retrieve a specific target by its name or ID.
    
    Performs case-insensitive search through target names and IDs.
    Useful when you need to revisit a known location.
    
    Args:
        name: Target name or ID to search for
    
    Returns:
        JSON string containing target details or error if not found
    """
    target = target_store.find_by_name(name)
    
    if not target:
        return json.dumps({"error": f"No target found matching '{name}'"})
    
    result = {
        "target_id": target['id'],
        "name": target['properties']['name'],
        "description": target['properties']['description'],
        "type": target['properties']['target_type'],
        "priority": target['properties']['priority'],
        "coordinates": {
            "lat": target['geometry']['coordinates'][1],
            "lon": target['geometry']['coordinates'][0]
        },
        "altitude_m": target['properties']['altitude_m'],
        "visit_count": target['properties']['visit_count'],
        "last_visited": target['properties'].get('last_visited'),
        "observations": target['properties']['observations']
    }
    
    return json.dumps(result, indent=2)


@tool
def list_all_targets(
    priority: Optional[str] = None,
    target_type: Optional[str] = None,
    min_visits: Optional[int] = None,
    max_visits: Optional[int] = None
) -> str:
    """
    List all targets with optional filters.
    
    Useful for getting an overview of targets or finding targets that meet
    specific criteria (e.g., high priority targets that haven't been visited).
    
    Args:
        priority: Filter by priority level ('high', 'medium', 'low')
        target_type: Filter by type ('wildlife_habitat', 'water_source', etc.)
        min_visits: Only show targets visited at least this many times
        max_visits: Only show targets visited at most this many times
    
    Returns:
        JSON string containing list of matching targets with basic info
    """
    targets = target_store.list_all(
        priority=priority,
        target_type=target_type,
        min_visits=min_visits,
        max_visits=max_visits
    )
    
    # Build summary list
    result = {
        "total_count": len(targets),
        "targets": []
    }
    
    for target in targets:
        summary = {
            "id": target['id'],
            "name": target['properties']['name'],
            "type": target['properties']['target_type'],
            "priority": target['properties']['priority'],
            "coordinates": {
                "lat": target['geometry']['coordinates'][1],
                "lon": target['geometry']['coordinates'][0]
            },
            "visit_count": target['properties']['visit_count'],
            "observation_count": len(target['properties']['observations'])
        }
        result["targets"].append(summary)
    
    return json.dumps(result, indent=2)


# Tool list for Agno agent
spatial_tools = [
    get_nearest_target,
    get_target_by_name,
    list_all_targets
]
