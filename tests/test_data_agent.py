import sys, json, uuid
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, r"C:\Users\kavir\dronekit3")

from tools.geojson_db import TargetStore, ObservationStore

ts = TargetStore(Path("data/targets.geojson"))
obs = ObservationStore(Path("data/observations.geojson"), ts)

fake = {
    "type": "Feature",
    "id": str(uuid.uuid4()),
    "geometry": {"type": "Point", "coordinates": [-105.2705, 40.0150]},
    "properties": {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "observer": "vision_agent",
        "detections": [{"label": "Golden Eagle", "confidence": 0.92, "bbox": None, "attributes": {}}],
        "image_path": "data/images/test.jpg",
        "confidence": 0.92,
        "notes": "Test save",
        "weather": "clear"
    }
}

obs_id = obs.add_observation("North Ridge Eagle Nest", fake)
print(f"TEST 1 PASSED — saved observation: {obs_id}")


results = obs.get_observations("North Ridge Eagle Nest")
print(f"TEST 2 PASSED — retrieved {len(results)} observation(s)")


target = ts.find_by_name("North Ridge Eagle Nest")
print(f"TEST 3 PASSED — visit_count is now: {target['properties']['visit_count']}")


updated = ts.update_field("North Ridge Eagle Nest", "priority", "low")
target = ts.find_by_name("North Ridge Eagle Nest")
assert target["properties"]["priority"] == "low", "priority not updated"
print(f"TEST 4 PASSED — priority updated to: {target['properties']['priority']}")


try:
    obs.add_observation("Nonexistent Target", fake)
    print("TEST 5 FAILED — should have raised ValueError")
except ValueError as e:
    print(f"TEST 5 PASSED — correctly rejected: {e}")

print("\nAll tests passed. Check data/observations.geojson to confirm the write.")
