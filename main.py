
from rankine.rankine import Rankine, State
from rankine.improvements import Overpressure, Underpressure, Overheating
from rankine.specials import RankineReheating
from rankine.conversions import *

cycle = RankineReheating(
    heating_HP=State(P=MPa(12), T=Kelvin(520)),
    heating_LP=State(P=MPa(2), T=Kelvin(500)),
    condensation=State(P=kPa(8))
)

cycle.resolve()

print(cycle)