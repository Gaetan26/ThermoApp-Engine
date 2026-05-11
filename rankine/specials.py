
from rankine.rankine import Rankine, State
import CoolProp.CoolProp as CP

class RankineReheating(Rankine):
    def __init__(self, 
        fluid: str = "Water", pumping: State = None, heating_HP: State = None, 
        relaxation_HP: State = None, heating_LP: State = None, relaxation_LP: State = None, 
        condensation: State = None, eta_pump: float = 1.0, eta_turbine: float = 1.0, **kwargs
    ):
        
        super().__init__(
            fluid=fluid, 
            pumping=pumping, 
            condensation=condensation, 
            eta_pump=eta_pump, 
            eta_turbine=eta_turbine, 
            **kwargs
        )
        
        self.heating_HP = heating_HP or State()
        self.relaxation_HP = relaxation_HP or State()
        self.heating_LP = heating_LP or State()
        self.relaxation_LP = relaxation_LP or State()

        self.states = [
            self.pumping, 
            self.heating_HP, 
            self.relaxation_HP, 
            self.heating_LP, 
            self.relaxation_LP, 
            self.condensation
        ]
        
        self.diagram = self.create_diagram()

    def complete_structural_parameters(self):
        if self.pumping.P: self.condensation.P = self.pumping.P
        elif self.condensation.P: self.pumping.P = self.condensation.P
        if self.heating_HP.P: self.relaxation_HP.P = self.heating_HP.P
        if self.heating_LP.P: self.relaxation_LP.P = self.heating_LP.P
    
    def check_minimal_data(self):
        critical_vars = {
            "Pression Basse (Condenseur)": self.condensation.P,
            "Pression Haute (Chaudière HP)": self.heating_HP.P,
            "Pression de Resurchauffe (LP)": self.heating_LP.P,
            "Température Entrée Turbine HP": self.relaxation_HP.T,
            "Température Entrée Turbine BP (Sortie resurchauffeur)": self.relaxation_LP.T
        }
        
        missing = [k for k, v in critical_vars.items() if v is None]
        
        if missing:
            print("[bold red]Erreur de compatibilité : Données insuffisantes pour la resurchauffe[/bold red]")
            print(f"[yellow]Variables manquantes : {', '.join(missing)}[/yellow]")
            raise ValueError(f"Données manquantes : {', '.join(missing)}")
            
        return True

    def calculate_state_variables(self):
        f = self.fluid

        # 1. ÉTAT 1 : Sortie Condenseur (Liquide saturé)
        self.pumping.H = CP.PropsSI('H', 'P', self.pumping.P, 'Q', 0, f)
        self.pumping.S = CP.PropsSI('S', 'P', self.pumping.P, 'Q', 0, f)
        self.pumping.V = 1 / CP.PropsSI('D', 'P', self.pumping.P, 'Q', 0, f)
        self.pumping.T = CP.PropsSI('T', 'P', self.pumping.P, 'Q', 0, f)

        # 2. ÉTAT 2 : Sortie Pompe (Compression)
        w_p_ideal = self.pumping.V * (self.heating_HP.P - self.pumping.P)
        self.heating_HP.H = self.pumping.H + (w_p_ideal / self.eta_pump)
        self.heating_HP.S = CP.PropsSI('S', 'P', self.heating_HP.P, 'H', self.heating_HP.H, f)
        self.heating_HP.T = CP.PropsSI('T', 'P', self.heating_HP.P, 'H', self.heating_HP.H, f)

        # 3. ÉTAT 3 : Sortie Chaudière HP (Vapeur surchauffée)
        # On assume que T est fournie pour l'entrée turbine
        self.relaxation_HP.H = CP.PropsSI('H', 'T', self.relaxation_HP.T, 'P', self.relaxation_HP.P, f)
        self.relaxation_HP.S = CP.PropsSI('S', 'T', self.relaxation_HP.T, 'P', self.relaxation_HP.P, f)

        # 4. ÉTAT 4 : Sortie Turbine HP (Détente 1)
        h4_ideal = CP.PropsSI('H', 'P', self.heating_LP.P, 'S', self.relaxation_HP.S, f)
        self.heating_LP.H = self.relaxation_HP.H - (self.relaxation_HP.H - h4_ideal) * self.eta_turbine
        self.heating_LP.T = CP.PropsSI('T', 'P', self.heating_LP.P, 'H', self.heating_LP.H, f)
        self.heating_LP.S = CP.PropsSI('S', 'P', self.heating_LP.P, 'H', self.heating_LP.H, f)

        # 5. ÉTAT 5 : Sortie Resurchauffeur (Vapeur resurchauffée)
        self.relaxation_LP.H = CP.PropsSI('H', 'T', self.relaxation_LP.T, 'P', self.relaxation_LP.P, f)
        self.relaxation_LP.S = CP.PropsSI('S', 'T', self.relaxation_LP.T, 'P', self.relaxation_LP.P, f)

        # 6. ÉTAT 6 : Sortie Turbine BP (Détente 2)
        h6_ideal = CP.PropsSI('H', 'P', self.condensation.P, 'S', self.relaxation_LP.S, f)
        self.condensation.H = self.relaxation_LP.H - (self.relaxation_LP.H - h6_ideal) * self.eta_turbine
        self.condensation.T = CP.PropsSI('T', 'P', self.condensation.P, 'H', self.condensation.H, f)
        self.condensation.S = CP.PropsSI('S', 'P', self.condensation.P, 'H', self.condensation.H, f)
        
        # Calcul du titre en vapeur X pour la sortie finale
        try:
            x = CP.PropsSI('Q', 'P', self.condensation.P, 'H', self.condensation.H, f)
            self.condensation.X = x if 0 <= x <= 1 else 1.0
        except: self.condensation.X = None

    def calculate_W(self):
        self.Win = self.heating_HP.H - self.pumping.H
        self.Wout = (self.relaxation_HP.H - self.heating_LP.H) + (self.relaxation_LP.H - self.condensation.H)
        self.Wnet = self.Wout - self.Win

    def calculate_Q(self):
        self.Qin = (self.relaxation_HP.H - self.heating_HP.H) + (self.relaxation_LP.H - self.heating_LP.H)
        self.Qout = abs(self.pumping.H - self.condensation.H)

    def calculate_performance_metrics(self):
        self.Nth = self.Wnet / self.Qin

