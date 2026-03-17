"""
Generate sample targets.geojson for testing.
Creates 5 conservation monitoring targets with mock data.
"""

from datetime import datetime
import json
from pathlib import Path
import sys

# Add parent directory to path so we can import schemas
sys.path.append(str(Path(__file__).parent.parent))

from schemas.geojson_schema import (
    GeoJSONDatabase, Target, Geometry, 
    TargetProperties, Observation
)


def create_sample_targets():
    """Create sample targets for Mountain Village Environment."""
    
    # Target 1: Eagle nest site
    target1 = Target(
        id="target_001",
        geometry=Geometry(coordinates=[-105.2705, 40.0150]),  # Colorado coords
        properties=TargetProperties(
            name="North Ridge Eagle Nest",
            description="Golden Eagle nesting site on northern cliff face",
            target_type="wildlife_habitat",
            altitude_m=2450,
            image_paths=["images/eagle_nest_001.jpg", "images/eagle_nest_002.jpg"],
            priority="high",
            created_at="2026-01-15T10:00:00Z",
            observations=[
                Observation(
                    timestamp="2026-02-20T14:23:00Z",
                    observer="manual_survey",
                    species="Golden Eagle",
                    count=2,
                    confidence=0.95,
                    notes="Active nest with two adults observed",
                    weather="clear",
                    image_quality="excellent"
                )
            ],
            last_visited="2026-02-20T14:23:00Z",
            visit_count=1
        )
    )
    
    # Target 2: Water source
    target2 = Target(
        id="target_002",
        geometry=Geometry(coordinates=[-105.2820, 40.0180]),
        properties=TargetProperties(
            name="Alpine Creek Water Source",
            description="Natural water source frequented by wildlife",
            target_type="water_source",
            altitude_m=2380,
            image_paths=["images/water_source_001.jpg"],
            priority="medium",
            created_at="2026-01-20T12:00:00Z",
            observations=[],
            visit_count=0
        )
    )
    
    # Target 3: Research equipment
    target3 = Target(
        id="target_003",
        geometry=Geometry(coordinates=[-105.2650, 40.0120]),
        properties=TargetProperties(
            name="Weather Station Alpha",
            description="Automated weather monitoring equipment",
            target_type="equipment",
            altitude_m=2500,
            image_paths=["images/weather_station.jpg"],
            priority="low",
            created_at="2026-01-10T09:00:00Z",
            observations=[
                Observation(
                    timestamp="2026-03-01T11:00:00Z",
                    observer="analysis_agent",
                    species=None,
                    count=0,
                    confidence=0.88,
                    notes="Equipment operational, solar panels clean",
                    weather="partly_cloudy",
                    image_quality="good"
                )
            ],
            last_visited="2026-03-01T11:00:00Z",
            visit_count=3
        )
    )
    
    # Target 4: Deer habitat
    target4 = Target(
        id="target_004",
        geometry=Geometry(coordinates=[-105.2750, 40.0200]),
        properties=TargetProperties(
            name="East Valley Meadow",
            description="Mule deer grazing area",
            target_type="wildlife_habitat",
            altitude_m=2420,
            image_paths=["images/meadow_001.jpg", "images/meadow_002.jpg"],
            priority="high",
            created_at="2026-01-18T14:30:00Z",
            observations=[
                Observation(
                    timestamp="2026-02-15T08:45:00Z",
                    observer="manual_survey",
                    species="Mule Deer",
                    count=7,
                    confidence=0.92,
                    notes="Herd of 7 deer grazing, 2 juveniles present",
                    weather="clear",
                    image_quality="excellent"
                ),
                Observation(
                    timestamp="2026-02-28T09:15:00Z",
                    observer="analysis_agent",
                    species="Mule Deer",
                    count=5,
                    confidence=0.85,
                    notes="Smaller group observed, possible seasonal movement",
                    weather="overcast",
                    image_quality="fair"
                )
            ],
            last_visited="2026-02-28T09:15:00Z",
            visit_count=2
        )
    )
    
    # Target 5: Vegetation monitoring
    target5 = Target(
        id="target_005",
        geometry=Geometry(coordinates=[-105.2680, 40.0090]),
        properties=TargetProperties(
            name="South Slope Aspen Grove",
            description="Aspen regeneration monitoring site",
            target_type="vegetation",
            altitude_m=2400,
            image_paths=["images/aspen_grove.jpg"],
            priority="medium",
            created_at="2026-01-25T11:00:00Z",
            observations=[],
            visit_count=0
        )
    )
    
    # Create database
    database = GeoJSONDatabase(
        metadata={
            "project": "Mountain Village Conservation Monitoring",
            "created": "2026-03-04",
            "coordinate_system": "WGS84",
            "description": "Sample targets for AVA drone monitoring system",
            "total_targets": 5
        },
        features=[target1, target2, target3, target4, target5]
    )
    
    return database


def save_to_file(database, filepath="targets.geojson"):
    """Save database to JSON file."""
    # Convert Pydantic model to dict, then to JSON
    data = database.model_dump()
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Created {filepath}")
    print(f"Total targets: {len(database.features)}")
    print(f" Targets with observations: {sum(1 for t in database.features if t.properties.observations)}")


if __name__ == "__main__":
    print("Generating sample targets.geojson...")
    db = create_sample_targets()
    save_to_file(db, "targets.geojson")
    print("Done!")