Day 2: Spatial Agent Implementation (Updated for Team Integration)

CHANGES FROM ORIGINAL:
----------------------
Refactored for compatibility with Jiayi's analysis_agent.py:

1. NEW FILE: tools/geojson_db.py
   - TargetStore class with methods Jiayi's code expects:
     * nearest(lat, lon) - returns target dict with distance_m field
     * find_by_name(name) - returns target dict or None
     * list_all(filters) - returns list of target dicts
   - ObservationStore class (stubbed for Day 4)

2. UPDATED: spatial_agent.py
   - Now imports and uses TargetStore instance
   - Tools call TargetStore methods instead of inline JSON loading
   - Jiayi can import from geojson_db and call same methods

3. UPDATED: schemas/geojson_schema.py
   - Added Detection class (VLM detection result)
   - Added CameraMeta class (camera metadata)
   - Added ObservationProps class (detailed observation with VLM data)
   - Added ObservationFeature class (GeoJSON feature wrapper)
   - Jiayi's analysis_agent.py can now import these classes

File Structure:
--------------
spatial_tools.py              Core spatial calculations (Haversine, validation)
geojson_db.py                 NEW: TargetStore and ObservationStore classes
spatial_agent.py              Agno tools (now uses TargetStore)
geojson_schema.py             Extended with VLM observation schemas
test_spatial_agent.py         Standalone test script
spatial_agent_integration.ipynb   Full integration notebook

Installation:
------------
No additional dependencies needed.

File Placement:
--------------
dronekit3/
├── tools/
│   ├── spatial_tools.py
│   ├── geojson_db.py          <- NEW
│   └── spatial_agent.py
├── schemas/
│   └── geojson_schema.py      <- UPDATED with 4 new classes
├── tests/
│   └── test_spatial_agent.py
└── notebooks/
    └── spatial_agent_integration.ipynb

Integration Points with Jiayi's Code:
------------------------------------
Jiayi's analysis_agent.py can now:

from geojson_db import TargetStore, ObservationStore
from schemas import ObservationFeature, ObservationProps, Detection, CameraMeta

target_store = TargetStore('data/targets.geojson')
nearest = target_store.nearest(40.0150, -105.2050)
target = target_store.find_by_name('Rocky Ridge')

The method signatures match what her code expects.

Testing:
-------
1. Test TargetStore directly:
   python
   >>> from geojson_db import TargetStore
   >>> store = TargetStore('data/targets.geojson')
   >>> nearest = store.nearest(40.0150, -105.2050)
   >>> print(nearest['properties']['name'])

2. Test with Agno agent:
   python tests/test_spatial_agent.py

3. Full integration:
   Open spatial_agent_integration.ipynb

Next Steps (Day 3):
------------------
- Build Vision Agent with VLM (coordinate model choice with Jiayi)
- Use ObservationProps and Detection schemas for structured output
- Integrate with Jiayi's analysis logic
- Day 4: Implement ObservationStore.add_observation() in Data Agent
