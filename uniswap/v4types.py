from dataclasses import dataclass


@dataclass
class pool_key:
    currency0 : str
    currency1 : str
    fee : int
    tick_spacing : int
    hooks : str

