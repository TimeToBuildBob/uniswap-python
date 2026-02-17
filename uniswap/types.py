from typing import Union
from eth_typing.evm import Address, ChecksumAddress
from dataclasses import dataclass

AddressLike = Union[Address, ChecksumAddress]

@dataclass
class pool_key:
    currency0 : str
    currency1 : str
    fee : int
    tick_spacing : int
    hooks : str