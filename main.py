
from rankine.rankine import Rankine, State
from rankine.improvements import Overpressure, Underpressure, Overheating
from rankine.specials import RankineReheating
from rankine.conversions import *

cycle = Rankine(
    heating=State( P=MPa(8),  T=Kelvin(480)),
    condensation=State( P=kPa(10) ),
)
