"""Bake the floor visualizer data for each room: python3 tools/viz/run.py [room ...]"""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import build, rooms, evening
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'img', 'viz')
os.makedirs(OUT, exist_ok=True)
build.OUT = OUT
keys = sys.argv[1:] or ['garage_solid', 'garage_storage', 'basement', 'patio']
data = {}
if os.path.exists(OUT + '/rooms.json'):
    data = {r['key']: r for r in json.load(open(OUT + '/rooms.json'))}
for k in keys:
    R = getattr(rooms, k)()
    info = build.build(R, evening.make)
    data[info['key']] = info
    print(info['key'], 'ok')
order = ['garage', 'garage2', 'basement', 'patio']
json.dump([data[k] for k in order if k in data], open(OUT + '/rooms.json', 'w'), indent=1)
