"""
This script modifies the DroneKit __init__.py file to replace deprecated
'collections.MutableMapping' with 'collections.abc.MutableMapping'.
"""
from pathlib import Path

p = Path('Lib/site-packages/dronekit/__init__.py')
data = p.read_text()
data = data.replace('collections.MutableMapping', 'collections.abc.MutableMapping')

p.write_text(data)
print("Dronekit __init__.py patched successfully.")