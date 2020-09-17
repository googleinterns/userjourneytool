from typing import Dict, Any
foo: Dict[str, Any] = dict(junk=1, bar=dict(yo=3))
foo['bar']['yo'] = 5


bar: Dict[str, Any] = {
    "data": {"id": "name"},
    "classes": "node"
}
bar["data"]["id"] = "name2"
bar["data"]["parent"] = "parent"
