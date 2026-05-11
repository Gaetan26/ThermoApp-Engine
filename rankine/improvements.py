
from rankine.rankine import Rankine
from rich import print

class Underpressure:
    @classmethod 
    def underpressure(cls, rankine: Rankine, P: int | float, verbose=True):
        if isinstance(rankine, Rankine) and rankine.resolved:
            rankine.resolved = False
            rankine.condensation.P = P
            rankine.pumping.P = P
            rankine.nature = "underpressure"
            rankine.resolve()
            if verbose:
                print("[bold cyan]Underpressure cycle successful[/bold cyan]")
            return rankine

        else:
            print("[bold red]You must provide a resolved Rankine cycle[/bold red]")
            raise ValueError("You must provide a resolved Rankine cycle")

class Overpressure:
    @classmethod
    def overpressure(cls, rankine: Rankine, P: int | float, verbose=True):
        if isinstance(rankine, Rankine) and rankine.resolved:
            rankine.resolved = False
            rankine.heating.P = P
            rankine.relaxation.P = P
            rankine.nature = "overpressure"
            rankine.resolve()
            if verbose:
                print("[bold cyan]Overpressure cycle successful[/bold cyan]")
            return rankine

        else:
            print("[bold red]You must provide a resolved Rankine cycle[/bold red]")
            raise ValueError("You must provide a resolved Rankine cycle")

class Overheating:
    @classmethod
    def overheating(cls, rankine: Rankine, T: int| float, verbose=True):
        if isinstance(rankine, Rankine) and rankine.resolved:
            rankine.resolved = False
            rankine.heating.T = T
            rankine.relaxation.T = T
            rankine.nature = "overheating"
            rankine.resolve()
            if verbose:
                print("[bold cyan]Superheated cycle successful[/bold cyan]")
            return rankine

        else:
            print("[bold red]You must provide a resolved Rankine cycle[/bold red]")
            raise ValueError("You must provide a resolved Rankine cycle")
