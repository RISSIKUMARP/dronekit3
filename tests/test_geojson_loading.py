"""
Test loading and validating targets.geojson
"""

import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from schemas.geojson_schema import GeoJSONDatabase


def test_load_targets():
    """Load and validate targets.geojson"""
    
    # Path to data file
    data_path = Path(__file__).parent.parent / "data" / "targets.geojson"
    
    print(f"Loading {data_path}...")
    
    # Load JSON
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Validate with Pydantic
    database = GeoJSONDatabase(**data)
    
    print(f" Valid GeoJSON structure")
    print(f" Total targets: {len(database.features)}")
    
    # Print target summary
    print("\nTarget Summary:")
    for target in database.features:
        obs_count = len(target.properties.observations)
        print(f"  {target.id}: {target.properties.name}")
        print(f"    Type: {target.properties.target_type}, Priority: {target.properties.priority}")
        print(f"    Location: {target.geometry.coordinates}")
        print(f"    Observations: {obs_count}")
    

    # Find high priority targets
    high_priority = [t for t in database.features if t.properties.priority == "high"]
    print(f" High priority targets: {len(high_priority)}")
    
    # Find targets with observations
    with_obs = [t for t in database.features if t.properties.observations]
    print(f" Targets with observations: {len(with_obs)}")
    
    # Find wildlife habitats
    wildlife = [t for t in database.features if t.properties.target_type == "wildlife_habitat"]
    print(f" Wildlife habitat targets: {len(wildlife)}")
    
    print("\n All validations passed!")
    return database


if __name__ == "__main__":
    test_load_targets()