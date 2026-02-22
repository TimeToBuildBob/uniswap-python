from dataclasses import dataclass
from typing import Union

from eth_typing.evm import Address, ChecksumAddress

AddressLike = Union[Address, ChecksumAddress]


@dataclass
class PoolKey:
    currency0: str
    currency1: str
    fee: int
    tick_spacing: int
    hooks: str
