"""
GeoJSON schema definitions for conservation monitoring targets.
Defines structure for targets and observations using Pydantic.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Observation(BaseModel):
    """Single observation record for a target."""
    timestamp: str = Field(description="ISO format timestamp of observation")
    observer: str = Field(default="analysis_agent", description="Who/what made this observation")
    species: Optional[str] = Field(None, description="Species identified (if wildlife)")
    count: int = Field(default=0, description="Number of individuals observed")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    notes: str = Field(default="", description="Additional observations")
    weather: Optional[str] = Field(None, description="Weather conditions during observation")
    image_quality: Optional[str] = Field(None, description="Quality of captured images")


class TargetProperties(BaseModel):
    """Properties (non-geographic data) for a target."""
    name: str
    description: str
    target_type: str  # wildlife_habitat, water_source, equipment, vegetation
    altitude_m: float
    image_paths: List[str] = Field(default_factory=list)
    priority: str = Field(default="medium")  # low, medium, high
    observations: List[Observation] = Field(default_factory=list)
    created_at: str
    last_visited: Optional[str] = None
    visit_count: int = Field(default=0)


class Geometry(BaseModel):
    """Geographic point data."""
    type: str = Field(default="Point")
    coordinates: List[float]  # [longitude, latitude]


class Target(BaseModel):
    """Individual target feature."""
    type: str = Field(default="Feature")
    id: str
    geometry: Geometry
    properties: TargetProperties


class GeoJSONDatabase(BaseModel):
    """Complete GeoJSON database structure."""
    type: str = Field(default="FeatureCollection")
    metadata: dict = Field(default_factory=dict)
    features: List[Target]


class Detection(BaseModel):
    """VLM detection result for a single object."""
    label: str = Field(description="Object or species label")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence 0-1")
    bbox: Optional[List[float]] = Field(None, description="Bounding box [x, y, width, height]")
    attributes: dict = Field(default_factory=dict, description="Additional attributes")


class CameraMeta(BaseModel):
    """Camera metadata for observation."""
    exposure: Optional[float] = Field(None, description="Exposure time in seconds")
    iso: Optional[int] = Field(None, description="ISO sensitivity")
    focal_length: Optional[float] = Field(None, description="Focal length in mm")
    aperture: Optional[float] = Field(None, description="F-stop value")
    timestamp: Optional[str] = Field(None, description="Camera timestamp")
    resolution: Optional[str] = Field(None, description="Image resolution (e.g., '1920x1080')")


class ObservationProps(BaseModel):
    """Detailed observation properties with VLM analysis."""
    timestamp: str = Field(description="ISO format timestamp")
    observer: str = Field(default="analysis_agent", description="Observer identifier")
    detections: List[Detection] = Field(default_factory=list, description="VLM detections")
    image_path: Optional[str] = Field(None, description="Path to captured image")
    camera_meta: Optional[CameraMeta] = Field(None, description="Camera metadata")
    weather: Optional[str] = Field(None, description="Weather conditions")
    notes: str = Field(default="", description="Additional notes")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall confidence")


class ObservationFeature(BaseModel):
    """GeoJSON feature for a single observation."""
    type: str = Field(default="Feature")
    id: str = Field(description="Unique observation ID")
    geometry: Geometry
    properties: ObservationProps