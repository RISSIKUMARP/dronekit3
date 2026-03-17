"""
GeoJSON database interface for conservation targets and observations.
Provides TargetStore and ObservationStore classes for spatial queries.
"""

import json
from typing import List, Dict, Optional
from pathlib import Path
from tools.spatial_tools import haversine_distance, validate_coordinates


class TargetStore:
    """Interface for querying conservation targets from GeoJSON database."""
    
    def __init__(self, geojson_path: str):
        """
        Initialize target store with GeoJSON file.
        
        Args:
            geojson_path: Path to targets.geojson file
        """
        self.geojson_path = Path(geojson_path)
        self.targets = self._load_targets()
    
    def _load_targets(self) -> List[Dict]:
        """Load all targets from GeoJSON file."""
        if not self.geojson_path.exists():
            raise FileNotFoundError(f"GeoJSON database not found at {self.geojson_path}")
        
        with open(self.geojson_path, 'r') as f:
            data = json.load(f)
        
        return data.get('features', [])
    
    def nearest(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Find target nearest to given coordinates.
        
        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
        
        Returns:
            Target dict with added 'distance_m' field, or None if no targets
        """
        valid, error = validate_coordinates(lat, lon)
        if not valid:
            raise ValueError(error)
        
        if not self.targets:
            return None
        
        nearest_target = None
        min_distance = float('inf')
        
        for target in self.targets:
            target_lon, target_lat = target['geometry']['coordinates']
            distance = haversine_distance(lat, lon, target_lat, target_lon)
            
            if distance < min_distance:
                min_distance = distance
                nearest_target = target
        
        if nearest_target:
            result = nearest_target.copy()
            result['distance_m'] = round(min_distance, 1)
            return result
        
        return None
    
    def find_by_name(self, name: str) -> Optional[Dict]:
        """
        Find target by name or ID (case-insensitive).
        
        Args:
            name: Target name or ID to search for
        
        Returns:
            Target dict or None if not found
        """
        name_lower = name.lower()
        
        for target in self.targets:
            target_name = target['properties']['name'].lower()
            target_id = target['id'].lower()
            
            if name_lower in target_name or name_lower in target_id:
                return target
        
        return None
    
    def list_all(
        self,
        priority: Optional[str] = None,
        target_type: Optional[str] = None,
        min_visits: Optional[int] = None,
        max_visits: Optional[int] = None
    ) -> List[Dict]:
        """
        Get all targets with optional filters.
        
        Args:
            priority: Filter by priority ('high', 'medium', 'low')
            target_type: Filter by type ('wildlife_habitat', 'water_source', etc.)
            min_visits: Minimum visit count
            max_visits: Maximum visit count
        
        Returns:
            List of target dicts matching filters
        """
        filtered = self.targets
        
        if priority:
            filtered = [t for t in filtered 
                       if t['properties']['priority'].lower() == priority.lower()]
        
        if target_type:
            filtered = [t for t in filtered 
                       if t['properties']['target_type'].lower() == target_type.lower()]
        
        if min_visits is not None:
            filtered = [t for t in filtered 
                       if t['properties']['visit_count'] >= min_visits]
        
        if max_visits is not None:
            filtered = [t for t in filtered 
                       if t['properties']['visit_count'] <= max_visits]
        
        return filtered
    
    def reload(self):
        """Reload targets from disk (useful after external updates)."""
        self.targets = self._load_targets()


class ObservationStore:
    """
    Interface for logging and querying observations.
    Will be implemented in Day 4 Data Agent.
    """
    
    def __init__(self, geojson_path: str):
        """
        Initialize observation store with GeoJSON file.
        
        Args:
            geojson_path: Path to targets.geojson file
        """
        self.geojson_path = Path(geojson_path)
    
    def add_observation(self, target_id: str, observation: Dict) -> bool:
        """
        Add observation to target's history.
        
        Args:
            target_id: Target ID to add observation to
            observation: Observation dict to append
        
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("ObservationStore.add_observation not yet implemented")
    
    def get_observations(self, target_id: str) -> List[Dict]:
        """
        Get all observations for a target.
        
        Args:
            target_id: Target ID to query
        
        Returns:
            List of observation dicts
        """
        raise NotImplementedError("ObservationStore.get_observations not yet implemented")
