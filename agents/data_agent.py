"""
Data Agent for GeoJSON persistence operations.
Provides tools to save observations, retrieve observations, and patch target metadata.
"""

import json
from pathlib import Path
from agno.tools import tool
from tools.geojson_db import TargetStore, ObservationStore


TARGETS_PATH = Path(__file__).parent.parent / "data" / "targets.geojson"
OBSERVATIONS_PATH = Path(__file__).parent.parent / "data" / "observations.geojson"

# Module-level instances — shared across all tool calls
target_store = TargetStore(TARGETS_PATH)
observation_store = ObservationStore(OBSERVATIONS_PATH, target_store)


@tool
def save_observation(target_name: str, observation_json: str) -> str:
    """
    Persist an ObservationFeature to observations.geojson.

    Accepts the JSON string output from the Vision Agent's analyze_image
    or capture_and_analyze tools and writes it to disk. Also increments
    visit_count and updates last_visited on the parent target.

    Args:
        target_name:      Name of the conservation target this observation is for.
        observation_json: JSON string of an ObservationFeature object.

    Returns:
        JSON string with 'observation_id' and 'target_name' on success,
        'error' key on failure.
    """
    try:
        feature = json.loads(observation_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON: {str(e)}"})

    # Basic structural check before attempting write
    if feature.get("type") != "Feature":
        return json.dumps({"error": "observation_json must be a GeoJSON Feature"})
    if "id" not in feature:
        return json.dumps({"error": "ObservationFeature missing 'id' field"})

    try:
        obs_id = observation_store.add_observation(target_name, feature)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    return json.dumps({
        "observation_id": obs_id,
        "target_name": target_name,
        "status": "saved"
    })


@tool
def get_observations(target_name: str) -> str:
    """
    Retrieve all stored observations for a conservation target.

    Reads from observations.geojson and filters by target name.
    Returns full ObservationFeature objects including detections,
    image path, camera metadata, and confidence scores.

    Args:
        target_name: Name of the conservation target to query.

    Returns:
        JSON string with 'target_name', 'count', and 'observations' list.
    """
    observations = observation_store.get_observations(target_name)

    return json.dumps({
        "target_name": target_name,
        "count": len(observations),
        "observations": observations
    }, indent=2)


@tool
def update_target_metadata(target_name: str, field: str, value: str) -> str:
    """
    Update a metadata field on a conservation target.

    Patches a single property on the target in targets.geojson.
    Only safe, non-structural fields can be updated this way.
    Allowed fields: priority, description, notes, altitude_m.

    Args:
        target_name: Name of the target to update.
        field:       Property name to update (priority/description/notes/altitude_m).
        value:       New value as a string. altitude_m will be cast to float.

    Returns:
        JSON string confirming the update, or 'error' on failure.
    """
    # Cast altitude to float if that's the target field
    parsed_value = float(value) if field == "altitude_m" else value

    try:
        updated = target_store.update_field(target_name, field, parsed_value)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    if not updated:
        return json.dumps({"error": f"Target '{target_name}' not found"})

    return json.dumps({
        "target_name": target_name,
        "field": field,
        "new_value": parsed_value,
        "status": "updated"
    })


# Tool list for Agno agent
data_tools = [
    save_observation,
    get_observations,
    update_target_metadata,
]
