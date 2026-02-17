from typing import Set, cast

from web3.types import RPCEndpoint  # noqa: F401

# look at web3/middleware/cache.py for reference
# RPC methods that will be cached inside _get_eth_simple_cache_middleware
SIMPLE_CACHE_RPC_WHITELIST = cast(
    Set[RPCEndpoint],
    {
        "eth_chainId",
    },
)

ETH_ADDRESS = "0x0000000000000000000000000000000000000000"
WETH9_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
ZERO_HOOK = "0x0000000000000000000000000000000000000000"
WRAPPED_ETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

# see: https://chainid.network/chains/
_netid_to_name = {
    1: "mainnet",
    3: "ropsten",
    4: "rinkeby",
    5: "görli",
    10: "optimism",
    42: "kovan",
    56: "binance",
    97: "binance_testnet",
    100: "xdai",
    130: "unichain",
    137: "polygon",
    143: "monad",
    250: "fantom",
    480: "worldchain",
    1868: "soneium",
    4326: "megaeth",
    8453: "base",
    42161: "arbitrum",
    42220: "celo",
    43114: "avalanche",
    57073: "ink",
    81457: "blast",
    421611: "arbitrum_testnet",
    7777777: "zora",
    1666600000: "harmony_mainnet",
    1666700000: "harmony_testnet",
    11155111: "sepolia",
}

_factory_contract_addresses_v1 = {
    "mainnet": "0xc0a47dFe034B400B47bDaD5FecDa2621de6c4d95",
    "ropsten": "0x9c83dCE8CA20E9aAF9D3efc003b2ea62aBC08351",
    "rinkeby": "0xf5D915570BC477f9B8D6C0E980aA81757A3AaC36",
    "kovan": "0xD3E51Ef092B2845f10401a0159B2B96e8B6c3D30",
    "görli": "0x6Ce570d02D73d4c384b46135E87f8C592A8c86dA",
}


# For v2 the address is the same on mainnet, Ropsten, Rinkeby, Görli, and Kovan
# https://uniswap.org/docs/v2/smart-contracts/factory
_factory_contract_addresses_v2 = {
    "mainnet": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    "ropsten": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    "rinkeby": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    "görli": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    "xdai": "0xA818b4F111Ccac7AA31D0BCc0806d64F2E0737D7",
    "binance": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73",
    "binance_testnet": "0x6725F303b657a9451d8BA641348b6761A6CC7a17",
    # SushiSwap on Harmony
    "harmony_mainnet": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
    "harmony_testnet": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
    "sepolia": "0x7E0987E5b3a30e3f2828572Bb659A548460a3003",
}

_router_contract_addresses_v2 = {
    "mainnet": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "ropsten": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "rinkeby": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "görli": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "sepolia": "0xC532a74256D3Db42D0Bf7a0400fEFDbad7694008",
    "xdai": "0x1C232F01118CB8B424793ae03F870aa7D0ac7f77",
    "binance": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
    "binance_testnet": "0xD99D1c33F9fC3444f8101754aBC46c52416550D1",
    # SushiSwap on Harmony
    "harmony_mainnet": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
    "harmony_testnet": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
}

MAX_UINT_128 = (2**128) - 1

# Source:
# https://github.com/Uniswap/v3-core/blob/v1.0.0/contracts/libraries/TickMath.sol#L8-L11
MIN_TICK = -887272
MAX_TICK = -MIN_TICK

# Source:
# https://github.com/Uniswap/v3-core/blob/v1.0.0/contracts/UniswapV3Factory.sol#L26-L31
_tick_spacing = {100: 1, 500: 10, 3_000: 60, 10_000: 200}

# Derived from (MIN_TICK//tick_spacing) >> 8 and (MAX_TICK//tick_spacing) >> 8
_tick_bitmap_range = {
    100: (-3466, 3465),
    500: (-347, 346),
    3_000: (-58, 57),
    10_000: (-18, 17),
}

# Source:
# https://docs.uniswap.org/contracts/v4/deployments
_router_contract_addresses_v4 = {
    "mainnet": "0x66a9893cc07d91d95644aedd05d03f95e1dba8af",
    "unichain": "0xef740bf23acae26f6492b10de645d6b98dc8eaf3",
    "optimism": "0x851116d9223fabed8e56c0e6b8ad0c31d98b3507",
    "base": "0x6ff5693b99212da76ad316178a184ab56d299b43",
    "arbitrum": "0xa51afafe0263b40edaef0df8781ea9aa03e381a3",
    "polygon": "0x1095692a6237d83c6a72f3f5efedb9a670c49223",
    "blast": "0xeabbcb3e8e415306207ef514f660a3f820025be3",
    "zora": "0x3315ef7ca28db74abadc6c44570efdf06b04b020",
    "worldchain": "0x8ac7bee993bb44dab564ea4bc9ea67bf9eb5e743",
    "ink": "0x112908dac86e20e7241b0927479ea3bf935d1fa0",
    "soneium": "0x4cded7edf52c8aa5259a54ec6a3ce7c6d2a455df",
    "avalanche": "0x94b75331ae8d42c1b61065089b7d48fe14aa73b7",
    "binance": "0x1906c1d672b88cd1b9ac7593301ca990f94eae07",
    "celo": "0xcb695bc5d3aa22cad1e6df07801b061a05a0233a",
    "monad": "0x0d97dc33264bfc1c226207428a79b26757fb9dc3",
    "megaeth": "0x48fd03529d2a91be835f07f6b72f53b4aad6093d",
}

_quoter_contract_addresses_v4 = {
    "mainnet": "0x52f0e24d1c21c8a0cb1e5a5dd6198556bd9e1203",
    "unichain": "0x333e3c607b141b18ff6de9f258db6e77fe7491e0",
    "optimism": "0x1f3131a13296fb91c90870043742c3cdbff1a8d7",
    "base": "0x0d5e0f971ed27fbff6c2837bf31316121532048d",
    "arbitrum": "0x3972c00f7ed4885e145823eb7c655375d275a1c5",
    "polygon": "0xb3d5c3dfc3a7aebff71895a7191796bffc2c81b9",
    "blast": "0x6f71cdcb0d119ff72c6eb501abceb576fbf62bcf",
    "zora": "0x5edaccc0660e0a2c44b06e07ce8b915e625dc2c6",
    "worldchain": "0x55d235b3ff2daf7c3ede0defc9521f1d6fe6c5c0",
    "ink": "0x3972c00f7ed4885e145823eb7c655375d275a1c5",
    "soneium": "0x3972c00f7ed4885e145823eb7c655375d275a1c5",
    "avalanche": "0xbe40675bb704506a3c2ccfb762dcfd1e979845c2",
    "binance": "0x9f75dd27d6664c475b90e105573e550ff69437b0",
    "celo": "0x28566da1093609182dff2cb2a91cfd72e61d66cd",
    "monad": "0xa222dd357a9076d1091ed6aa2e16c9742dd26891",
    "megaeth": "0x94bdc671f0c35f44a1daa53143fd1f868d1623b9",
}

_stateview_contract_addresses_v4 = {
    "mainnet": "0x7ffe42c4a5deea5b0fec41c94c136cf115597227",
    "unichain": "0x86e8631a016f9068c3f085faf484ee3f5fdee8f2",
    "optimism": "0xc18a3169788f4f75a170290584eca6395c75ecdb",
    "base": "0xa3c0c9b65bad0b08107aa264b0f3db444b867a71",
    "arbitrum": "0x76fd297e2d437cd7f76d50f01afe6160f86e9990",
    "polygon": "0x5ea1bd7974c8a611cbab0bdcafcb1d9cc9b3ba5a",
    "blast": "0x12a88ae16f46dce4e8b15368008ab3380885df30",
    "zora": "0x385785af07d63b50d0a0ea57c4ff89d06adf7328",
    "worldchain": "0x51d394718bc09297262e368c1a481217fdeb71eb",
    "ink": "0x76fd297e2d437cd7f76d50f01afe6160f86e9990",
    "soneium": "0x76fd297e2d437cd7f76d50f01afe6160f86e9990",
    "avalanche": "0xc3c9e198c735a4b97e3e683f391ccbdd60b69286",
    "binance": "0xd13dd3d6e93f276fafc9db9e6bb47c1180aee0c4",
    "celo": "0xbc21f8720babf4b20d195ee5c6e99c52b76f2bfb",
    "monad": "0x77395f3b2e73ae90843717371294fa97cc419d64",
    "megaeth": "0x726f84e1dfb8d375a365e0808282f40d52d3e4e8",
}

_permit2_contract_addresses_v4 = {
    "mainnet": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "unichain": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "optimism": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "base": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "arbitrum": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "polygon": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "blast": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "zora": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "worldchain": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "ink": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "soneium": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "avalanche": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "binance": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "celo": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "monad": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
    "megaeth": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
}

_poolmanager_contract_addresses_v4 = {
    "mainnet": "0x000000000004444c5dc75cB358380D2e3dE08A90",
    "unichain": "0x1f98400000000000000000000000000000000004",
    "optimism": "0x9a13f98cb987694c9f086b1f5eb990eea8264ec3",
    "base": "0x498581ff718922c3f8e6a244956af099b2652b2b",
    "arbitrum": "0x360e68faccca8ca495c1b759fd9eee466db9fb32",
    "polygon": "0x67366782805870060151383f4bbff9dab53e5cd6",
    "blast": "0x1631559198a9e474033433b2958dabc135ab6446",
    "zora": "0x0575338e4c17006ae181b47900a84404247ca30f",
    "worldchain": "0xb1860d529182ac3bc1f51fa2abd56662b7d13f33",
    "ink": "0x360e68faccca8ca495c1b759fd9eee466db9fb32",
    "soneium": "0x360e68faccca8ca495c1b759fd9eee466db9fb32",
    "avalanche": "0x06380c0e0912312b5150364b9dc4542ba0dbbc85",
    "binance": "0x28e2ea090877bf75740558f6bfb36a5ffee9e9df",
    "celo": "0x288dc841A52FCA2707c6947B3A777c5E56cd87BC",
    "monad": "0x188d586ddcf52439676ca21a244753fa19f9ea8e",
    "megaeth": "0xacb7e78fa05d562e0a5d3089ec896d57d057d38e",
}
