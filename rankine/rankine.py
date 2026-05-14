
from rich import print
from rich.table import Table
import CoolProp.CoolProp as CP
import json

class State:    
    def __init__(self, **kwargs):
        self.T = kwargs.get("T")
        self.P = kwargs.get("P")
        self.H = kwargs.get("H")
        self.S = kwargs.get("S")
        self.W = kwargs.get("W")
        self.Q = kwargs.get("Q")
        self.V = kwargs.get("V")
        self.X = kwargs.get("X")
    
    def to_dict(self):
        return {
            key: value for key, value in self.__dict__.items() if value is not None
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class Rankine:
    def __init__(self, fluid: str = "Water", pumping: State = None , heating: State = None, relaxation: State = None, condensation: State = None, eta_pump: float = 1.0, eta_turbine: float = 1.0, **kwargs):
        self.fluid = fluid
        self.pumping = pumping or State()
        self.heating = heating or State()
        self.relaxation = relaxation or State()
        self.condensation = condensation or State()
        self.states = [
            self.pumping, 
            self.heating, 
            self.relaxation, 
            self.condensation
        ]

        self.eta_pump = eta_pump
        self.eta_turbine = eta_turbine

        self.Qin = kwargs.get("Qin")
        self.Qout = kwargs.get("Qout")
        self.Win = kwargs.get("Win")
        self.Wout = kwargs.get("Wout")
        self.Wnet = kwargs.get("Wnet")
        self.Nth = kwargs.get("Nth")

        self.resolved = kwargs.get("resolved", False)
        self.verbose = kwargs.get("verbose", True)
        self.nature = kwargs.get("nature", "ideal")
        
        self.diagram = self.create_diagram()


    @classmethod
    def from_diagram(cls, data: dict, verbose=True):
        try:
            metadata = data.get("metadata", {})
            fluid = metadata.get("fluid", "Water")
            resolved = metadata.get("resolved", False)
            nature = metadata.get("nature", "ideal")

            eta_pump = data.get("eta_pump", 1)
            eta_turbine = data.get("eta_turbine", 1)

            states_data = data.get("states", {})
            states = {k: State.from_dict(v) for k, v in states_data.items()}
            metrics = data.get("metrics", {})

            if verbose:
                print(f"[bold cyan]Data successfully loaded from diagram[/bold cyan]")

            return cls(
                fluid=fluid,
                pumping=states.get("pumping"),
                heating=states.get("heating"),
                relaxation=states.get("relaxation"),
                condensation=states.get("condensation"),
                **metrics,
                resolved=resolved,
                nature=nature,
                eta_pump=eta_pump,
                eta_turbine=eta_turbine
            )
        except Exception as exc:
            print(f"[bold red]Error: Unable to load data from the diagram[/bold red]")
            raise exc
    
    @classmethod
    def from_json(cls, filename="rankine_results.json", verbose=True):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[bold cyan]Data successfully loaded from {filename}[/bold cyan]")
            return cls.from_diagram(data, verbose)
        except FileNotFoundError:
            print(f"[bold red]Error: The file {filename} cannot be found.[/bold red]")
            return None
        except json.JSONDecodeError:
            print(f"[bold red]Error: The file {filename} is not valid JSON.[/bold red]")
            return None

    def copy(self):
        return Rankine.from_diagram(self.diagram)

    def resolve(self):
        try:
            self.complete_structural_parameters()
            self.check_minimal_data() 
            self.calculate_state_variables()
            self.calculate_W()
            self.calculate_Q()
            self.calculate_performance_metrics()
            
            self.resolved = True
            self.diagram = self.create_diagram()

            if self.verbose:
                print("[bold cyan]Rankine cycle successfully solved[/bold cyan]")

        except Exception as exc:
            print("[bold red]Unable to resolve this Rankine cycle[/bold red]")
            raise exc

    def display_results(self):
        if not self.resolved:
            print("[bold red]Please complete the cycle before viewing the results[/bold red]")
            return

        table = Table(title="États Thermodynamiques du Cycle de Rankine", header_style="bold cyan")
        table.add_column("État", justify="center")
        table.add_column("Pression (Pa)", justify="right")
        table.add_column("Température (K)", justify="right")
        table.add_column("Enthalpie (J/kg)", justify="right")
        table.add_column("Entropie (J/kg.K)", justify="right")
        table.add_column("Titre (X)", justify="right")

        def fmt(val): return f"{val:.2f}" if val is not None else "-"

        states_names = ["1 (Pompe in)", "2 (Chaudière in)", "3 (Turbine in)", "4 (Condenseur in)"]
        for name, state in zip(states_names, self.states):
            table.add_row(name, fmt(state.P), fmt(state.T), fmt(state.H), fmt(state.S), fmt(state.X))

        print(table)

        perf_table = Table(title="Performances Globales", show_header=False, box=None)
        perf_table.add_row("[bold]Travail Net (Wnet):[/bold]", f"{self.Wnet:.2f} J/kg")
        perf_table.add_row("[bold]Chaleur Entrante (Qin):[/bold]", f"{self.Qin:.2f} J/kg")
        perf_table.add_row("[bold]Rendement Thermique:[/bold]", f"[bold green]{self.Nth * 100:.2f} %[/bold green]")
        
        print(perf_table)

    def create_diagram(self):
        metrics_keys = ("Qin", "Qout", "Win", "Wout", "Wnet", "Nth")
        schema = {
            "metadata": {
                "fluid": self.fluid,
                "resolved": self.resolved,
                "nature": self.nature
            },
            "states": {
                name: attr.to_dict() 
                for name, attr in self.__dict__.items() 
                if isinstance(attr, State)
            },
            "eta_pump": self.eta_pump,
            "eta_turbine": self.eta_turbine,
            "metrics": {k: getattr(self, k, None) for k in metrics_keys}
        }
        return schema

    def check_minimal_data(self):
        critical_vars = {
            "Pression Basse (P1 ou P4)": self.pumping.P,
            "Pression Haute (P2 ou P3)": self.heating.P
        }
        missing = [k for k, v in critical_vars.items() if v is None]
        if missing:
            print("[bold red]Important values are missing to complete the cycle[/bold red]")
            raise ValueError(f"Missing data: {', '.join(missing)}")
        return True
    
    def complete_structural_parameters(self):
        if self.pumping.P and not self.condensation.P:
            self.condensation.P = self.pumping.P
        elif self.condensation.P and not self.pumping.P:
            self.pumping.P = self.condensation.P

        if self.heating.P and not self.relaxation.P:
            self.relaxation.P = self.heating.P
        elif self.relaxation.P and not self.heating.P:
            self.heating.P = self.relaxation.P

        if self.heating.T and not self.relaxation.T:
            self.relaxation.T = self.heating.T
        elif self.relaxation.T and not self.heating.T:
            self.heating.T = self.relaxation.T

    def calculate_state_variables(self):
        fluid = self.fluid

        self.pumping.H = CP.PropsSI('H', 'P', self.pumping.P, 'Q', 0, fluid)
        self.pumping.S = CP.PropsSI('S', 'P', self.pumping.P, 'Q', 0, fluid)
        self.pumping.V = 1 / CP.PropsSI('D', 'P', self.pumping.P, 'Q', 0, fluid)
        self.pumping.T = CP.PropsSI('T', 'P', self.pumping.P, 'Q', 0, fluid)

        w_pump_ideal = self.pumping.V * (self.heating.P - self.pumping.P)
        w_pump_real = w_pump_ideal / self.eta_pump
        
        self.heating.H = self.pumping.H + w_pump_real
        self.heating.S = CP.PropsSI('S', 'P', self.heating.P, 'H', self.heating.H, fluid)

        self.relaxation.H = CP.PropsSI('H', 'T', self.relaxation.T, 'P', self.relaxation.P, fluid)
        self.relaxation.S = CP.PropsSI('S', 'T', self.relaxation.T, 'P', self.relaxation.P, fluid)
        
        s4_ideal = self.relaxation.S
        h4_ideal = CP.PropsSI('H', 'P', self.condensation.P, 'S', s4_ideal, fluid)
        
        w_turb_ideal = self.relaxation.H - h4_ideal
        w_turb_real = w_turb_ideal * self.eta_turbine
        
        self.condensation.H = self.relaxation.H - w_turb_real
        self.condensation.S = CP.PropsSI('S', 'P', self.condensation.P, 'H', self.condensation.H, fluid)
        self.condensation.T = CP.PropsSI('T', 'P', self.condensation.P, 'H', self.condensation.H, fluid)
        
        try:
            x_val = CP.PropsSI('Q', 'P', self.condensation.P, 'H', self.condensation.H, fluid)
            self.condensation.X = x_val if 0 <= x_val <= 1 else None
        except ValueError:
            self.condensation.X = None

    def calculate_W(self):
        self.pumping.W = self.heating.H - self.pumping.H
        self.relaxation.W = self.relaxation.H - self.condensation.H
    
    def calculate_Q(self):
        self.heating.Q = self.relaxation.H - self.heating.H
        self.condensation.Q = self.pumping.H - self.condensation.H

    def calculate_performance_metrics(self):
        self.Qin = self.heating.Q
        self.Qout = abs(self.condensation.Q)
        self.Win = self.pumping.W
        self.Wout = abs(self.relaxation.W)
        self.Wnet = self.Wout - self.Win
        self.Nth = self.Wnet / self.Qin

    def __str__(self):
        if self.resolved:
            self.display_results()
            return ""
        return json.dumps(self.diagram, indent=2)
