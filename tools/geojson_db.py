"""
Database interface layer for GeoJSON conservation data.
TargetStore: read/query targets.geojson
ObservationStore: read/write observations.geojson, update target visit metadata
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from tools.spatial_tools import haversine_distance


class TargetStore:
    """
    Read-only interface to targets.geojson.
    Loads features into memory on init. Call reload() to pick up external changes.
    """

    def __init__(self, geojson_path):
        self.path = Path(geojson_path)
        self._data = None
        self._load()

    def _load(self):
        with open(self.path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    def reload(self):
        self._load()

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def nearest(self, lat: float, lon: float) -> Optional[dict]:
        """Return the target closest to (lat, lon) with a distance_m key injected."""
        features = self._data.get("features", [])
        if not features:
            return None

        best = None
        best_dist = float("inf")

        for feature in features:
            coords = feature["geometry"]["coordinates"]
            t_lon, t_lat = coords[0], coords[1]
            dist = haversine_distance(lat, lon, t_lat, t_lon)
            if dist < best_dist:
                best_dist = dist
                best = feature

        if best:
            result = dict(best)
            result["distance_m"] = round(best_dist, 2)
            return result
        return None

    def find_by_name(self, name: str) -> Optional[dict]:
        """Case-insensitive search by target name or ID."""
        name_lower = name.lower()
        for feature in self._data.get("features", []):
            if feature["id"].lower() == name_lower:
                return feature
            if feature["properties"]["name"].lower() == name_lower:
                return feature
        return None

    def list_all(
        self,
        priority: Optional[str] = None,
        target_type: Optional[str] = None,
        min_visits: Optional[int] = None,
        max_visits: Optional[int] = None,
    ) -> list:
        """Return features filtered by optional criteria."""
        results = []
        for feature in self._data.get("features", []):
            props = feature["properties"]
            if priority and props.get("priority") != priority:
                continue
            if target_type and props.get("target_type") != target_type:
                continue
            visits = props.get("visit_count", 0)
            if min_visits is not None and visits < min_visits:
                continue
            if max_visits is not None and visits > max_visits:
                continue
            results.append(feature)
        return results

    def update_visit_metadata(self, target_name: str, timestamp: str):
        """
        Increment visit_count and set last_visited on a target.
        Called by ObservationStore.add_observation() — not exposed as an Agno tool.
        """
        for feature in self._data.get("features", []):
            props = feature["properties"]
            if props["name"].lower() == target_name.lower():
                props["visit_count"] = props.get("visit_count", 0) + 1
                props["last_visited"] = timestamp
                self._save()
                return True
        return False

    def update_field(self, target_name: str, field: str, value) -> bool:
        """
        Set an arbitrary top-level property field on a target.
        Used by update_target_metadata tool. Restricted to safe fields.
        """
        allowed = {"priority", "description", "notes", "altitude_m"}
        if field not in allowed:
            raise ValueError(f"Field '{field}' is not patchable. Allowed: {allowed}")

        for feature in self._data.get("features", []):
            if feature["properties"]["name"].lower() == target_name.lower():
                feature["properties"][field] = value
                self._save()
                return True
        return False


class ObservationStore:
    """
    Persistence layer for ObservationFeature objects.

    Writes to data/observations.geojson (separate from targets.geojson).
    Each stored feature gets a target_name injected into properties so
    observations can be filtered by target without a join.

    Also updates visit_count and last_visited on the parent target via TargetStore.
    """

    def __init__(self, observations_path, target_store: TargetStore):
        self.path = Path(observations_path)
        self.target_store = target_store
        self._ensure_file()

    def _ensure_file(self):
        """Create an empty FeatureCollection if the file does not exist."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            empty = {
                "type": "FeatureCollection",
                "metadata": {
                    "description": "AVA drone observation records",
                    "created": datetime.now(timezone.utc).isoformat(),
                },
                "features": [],
            }
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(empty, f, indent=2)

    def _load(self) -> dict:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_observation(self, target_name: str, observation_feature: dict) -> str:
        """
        Persist an ObservationFeature dict to observations.geojson.

        Injects target_name into properties. Updates visit metadata on the
        parent target in targets.geojson.

        Args:
            target_name: Name of the target this observation belongs to.
            observation_feature: Dict representation of an ObservationFeature.

        Returns:
            The observation ID that was written.

        Raises:
            ValueError: If target_name does not match any target in TargetStore.
        """
        target = self.target_store.find_by_name(target_name)
        if not target:
            raise ValueError(f"Target '{target_name}' not found in targets.geojson")

        # Inject target_name so observations are filterable without a join
        observation_feature["properties"]["target_name"] = target["properties"]["name"]

        data = self._load()
        data["features"].append(observation_feature)
        self._save(data)

        # Update parent target visit metadata
        ts = observation_feature["properties"].get(
            "timestamp", datetime.now(timezone.utc).isoformat()
        )
        self.target_store.update_visit_metadata(target["properties"]["name"], ts)

        return observation_feature["id"]

    def get_observations(self, target_name: str) -> list:
        """
        Return all observation features for a given target name.

        Args:
            target_name: Case-insensitive target name to filter by.

        Returns:
            List of ObservationFeature dicts. Empty list if none found.
        """
        data = self._load()
        name_lower = target_name.lower()
        return [
            f for f in data["features"]
            if f.get("properties", {}).get("target_name", "").lower() == name_lower
        ]

    def list_observation_ids(self) -> list:
        """Return all observation IDs across all targets."""
        data = self._load()
        return [f["id"] for f in data["features"]]
