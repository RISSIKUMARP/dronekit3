"""
Vision Agent for conservation image analysis.
Captures frames via window_grabber, runs VLM inference via OpenRouter,
returns structured ObservationFeature objects.
"""

import json
import base64
import requests
import cv2
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from agno.tools import tool

from schemas.geojson_schema import (
    Detection,
    CameraMeta,
    ObservationProps,
    ObservationFeature,
    Geometry,
)


_grabber = None       # Threaded_Window_Grabber instance
_api_key = None       # OpenRouter API key
_model = "qwen/qwen3-vl-32b-instruct"
_images_dir = Path(__file__).parent.parent / "data" / "images"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def init_vision_agent(api_key: str, grabber=None, model: str = None):

    global _grabber, _api_key, _model

    _api_key = api_key
    _grabber = grabber
    if model:
        _model = model

    _images_dir.mkdir(parents=True, exist_ok=True)
    print(f"Vision agent ready. Model: {_model}")
    if _grabber is None:
        print("Warning: no grabber provided - capture_frame will not work.")



def _frame_to_base64(frame) -> str:
    """Encode a BGR numpy frame to a base64 JPEG string."""
    ret, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ret:
        raise RuntimeError("cv2.imencode failed on frame")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def _image_path_to_base64(image_path: str) -> str:
    """Load an image from disk and return base64 JPEG string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _build_vlm_prompt() -> str:
    return """You are analyzing an aerial drone image for wildlife conservation monitoring.
The image may contain Mission Planner HUD overlays (telemetry numbers, mode text, crosshairs).
Ignore all HUD UI elements. Focus only on the terrain, vegetation, water, and any wildlife visible.

Return a JSON object with exactly this structure, nothing else - no markdown, no explanation:
{
  "detections": [
    {
      "label": "string - species name or object class",
      "confidence": 0.0,
      "bbox": [x, y, width, height],
      "attributes": {}
    }
  ],
  "scene_description": "string - one sentence describing the overall scene",
  "weather": "string - estimated conditions from image (clear/overcast/fog/etc)",
  "overall_confidence": 0.0,
  "notes": "string - any relevant observations"
}

If no wildlife or significant features are detected, return an empty detections list.
Confidence values must be between 0.0 and 1.0.
bbox values are pixel coordinates [x, y, width, height], or null if not applicable."""


def _call_vlm(b64_image: str) -> dict:
    """
    POST to OpenRouter with base64 image. Returns parsed JSON dict.
    Raises RuntimeError on API failure or unparseable response.
    """
    if not _api_key:
        raise RuntimeError("Vision agent not initialized. Call init_vision_agent() first.")

    payload = {
        "model": _model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": _build_vlm_prompt()
                    }
                ]
            }
        ],
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {_api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text[:300]}")

    content = response.json()["choices"][0]["message"]["content"]

    # Strip markdown fences if model wraps output anyway
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    return json.loads(cleaned)


def _build_observation_feature(
    vlm_result: dict,
    image_path: str,
    target_name: str,
    lat: float,
    lon: float,
) -> ObservationFeature:
    """Validate VLM output into an ObservationFeature Pydantic object."""

    detections = []
    for d in vlm_result.get("detections", []):
        detections.append(Detection(
            label=d.get("label", "unknown"),
            confidence=float(d.get("confidence", 0.0)),
            bbox=d.get("bbox"),
            attributes=d.get("attributes", {}),
        ))

    obs_props = ObservationProps(
        timestamp=datetime.now(timezone.utc).isoformat(),
        observer="vision_agent",
        detections=detections,
        image_path=image_path,
        camera_meta=CameraMeta(
            resolution="640x480",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
        weather=vlm_result.get("weather"),
        notes=vlm_result.get("notes", "") + " | " + vlm_result.get("scene_description", ""),
        confidence=float(vlm_result.get("overall_confidence", 0.0)),
    )

    return ObservationFeature(
        id=str(uuid.uuid4()),
        geometry=Geometry(coordinates=[lon, lat]),
        properties=obs_props,
    )



@tool
def capture_frame(target_name: str) -> str:
    """
    Capture a single frame from the active window grabber and save it to disk.

    Requires that init_vision_agent() was called with a running
    Threaded_Window_Grabber instance. The frame is saved as a JPEG under
    data/images/ with a timestamped filename.

    Args:
        target_name: Name of the conservation target being observed.
                     Used to label the saved image file.

    Returns:
        JSON string with 'image_path' key on success, 'error' key on failure.
    """
    if _grabber is None:
        return json.dumps({"error": "No grabber initialized. Call init_vision_agent(api_key, grabber=grabber)."})

    frame = _grabber.frame
    if frame is None:
        return json.dumps({"error": "Grabber has no frame yet. Wait a moment after instantiation."})

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = target_name.replace(" ", "_").lower()
    filename = f"{ts}_{safe_name}.jpg"
    save_path = _images_dir / filename

    ret = cv2.imwrite(str(save_path), frame)
    if not ret:
        return json.dumps({"error": f"cv2.imwrite failed for path {save_path}"})

    return json.dumps({"image_path": str(save_path), "filename": filename})


@tool
def analyze_image(image_path: str, target_name: str, lat: float, lon: float) -> str:
    """
    Run VLM inference on a saved image and return a structured observation.

    Loads the image from disk, sends it to OpenRouter with a conservation
    monitoring prompt, parses the JSON response, and validates it against
    the ObservationFeature schema.

    Args:
        image_path:  Absolute or relative path to the JPEG image file.
        target_name: Name of the conservation target this image is for.
        lat:         Latitude where the image was captured (decimal degrees).
        lon:         Longitude where the image was captured (decimal degrees).

    Returns:
        JSON string of ObservationFeature on success, 'error' key on failure.
    """
    try:
        b64 = _image_path_to_base64(image_path)
    except FileNotFoundError:
        return json.dumps({"error": f"Image not found: {image_path}"})

    try:
        vlm_result = _call_vlm(b64)
    except (RuntimeError, json.JSONDecodeError, KeyError) as e:
        return json.dumps({"error": f"VLM call failed: {str(e)}"})

    try:
        obs_feature = _build_observation_feature(vlm_result, image_path, target_name, lat, lon)
    except Exception as e:
        return json.dumps({"error": f"Schema validation failed: {str(e)}", "raw_vlm": vlm_result})

    return obs_feature.model_dump_json(indent=2)


@tool
def capture_and_analyze(target_name: str, lat: float, lon: float) -> str:
    """
    Capture a frame and immediately run VLM analysis on it.

    Combines capture_frame and analyze_image into a single operation.
    This is the primary tool the Coordinator Agent will call during a
    conservation monitoring flight.

    Args:
        target_name: Name of the conservation target being observed.
        lat:         Current drone latitude in decimal degrees.
        lon:         Current drone longitude in decimal degrees.

    Returns:
        JSON string of ObservationFeature on success, 'error' key on failure.
    """
    if _grabber is None:
        return json.dumps({"error": "No grabber initialized. Call init_vision_agent(api_key, grabber=grabber)."})

    frame = _grabber.frame
    if frame is None:
        return json.dumps({"error": "Grabber has no frame yet."})

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = target_name.replace(" ", "_").lower()
    filename = f"{ts}_{safe_name}.jpg"
    save_path = _images_dir / filename

    ret = cv2.imwrite(str(save_path), frame)
    if not ret:
        return json.dumps({"error": f"Frame save failed: {save_path}"})

    try:
        b64 = _frame_to_base64(frame)
    except RuntimeError as e:
        return json.dumps({"error": str(e)})

    try:
        vlm_result = _call_vlm(b64)
    except (RuntimeError, json.JSONDecodeError, KeyError) as e:
        return json.dumps({"error": f"VLM call failed: {str(e)}"})

    try:
        obs_feature = _build_observation_feature(vlm_result, str(save_path), target_name, lat, lon)
    except Exception as e:
        return json.dumps({"error": f"Schema validation failed: {str(e)}", "raw_vlm": vlm_result})

    return obs_feature.model_dump_json(indent=2)


# Tool list for Agno agent
vision_tools = [
    capture_frame,
    analyze_image,
    capture_and_analyze,
]
