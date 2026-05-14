
from rankine.rankine import Rankine, State
from rankine.improvements import Overpressure, Underpressure, Overheating
from rankine.specials import RankineReheating
from rankine.conversions import *
import json

cycle = RankineReheating.from_json("cycle.json")
cycle.resolve()

print(json.dumps(cycle.diagram, indent=2))

# print(cycle)
