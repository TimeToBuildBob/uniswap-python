from web3 import Web3
import eth_abi.abi
from web3.contract import Contract
from web3.contract.contract import ContractFunction
from eth_typing import AnyAddress
from eth_abi.codec import ABICodec
from eth_abi import encode
from eth_abi.packed import encode_packed
import os
import fnmatch
import configparser
import logging
from decimal import Decimal
from typing import List, Any, Optional, Callable, Union, Tuple, Dict
from web3.types import (
    TxParams,
    Wei,
    Address,
    ChecksumAddress,
    ENS,
    Nonce,
    HexBytes,
)
import json
import ctypes
from .uni4base import *
from .token import ERC20Token
from .types import AddressLike
from .util import (
    _addr_to_str,
    _load_contract,
    _load_contract_erc20,
    _load_abi,
    _str_to_addr,
    _validate_address,
    chunks,
    encode_sqrt_ratioX96,
    is_same_address,
    nearest_tick,
    realised_fee_percentage,
)


_netid_to_name = {1000: "mainnet", 1001: "nile"}
with open(os.path.abspath(f"assets\\erc20.abi")) as f:
        erc20_ABI : str = json.load(f)


class Uniswap4():
    def __init__(self,
        address: Union[str, AddressLike],
        private_key: str,
        provider: str=None,
        web3: Web3=None,
        version: int=4,
        max_slippage: float=0.1,
        max_gas: float=250000.0,
        max_gprice: float=1.80,
        london_fork: int=1,
        max_priorityfee: float=1.0,) -> None:

        self.address : AddressLike = _str_to_addr(address) if isinstance(address, str) else address
        self.private_key = private_key
        self.version = version

        self.max_slippage = max_slippage

        if web3:
            self.w3 = web3
        else:
            self.provider = provider or os.environ["PROVIDER"]
            self.w3 = Web3(Web3.HTTPProvider(self.provider, request_kwargs={"timeout": 60}))

        self.last_nonce : Nonce = self.w3.eth.get_transaction_count(self.address)

        # This code automatically approves you for trading on the exchange.
        # max_approval is to allow the contract to exchange on your behalf.
        # max_approval_check checks that current approval is above a reasonable
        # number
        # The program cannot check for max_approval each time because it
        # decreases
        # with each trade.
        self.max_approval_hex = f"0x{64 * 'f'}"
        self.max_approval_int = int(self.max_approval_hex, 16)
        self.max_approval_check_hex = f"0x{15 * '0'}{49 * 'f'}"
        self.max_approval_check_int = int(self.max_approval_check_hex, 16)
        self.gas_limit = max_gas
        self.gas_price = max_gprice
        self.london_style = london_fork
        self.london_priorityfee = max_priorityfee

        chain_id = self.w3.net.version
        config = configparser.ConfigParser()
        config.read("configs\\quoter.ini")
        quoter_address = config.get("settings",chain_id)
        config.read("configs\\router.ini")
        router_address = config.get("settings",chain_id)
        config.read("configs\\stateview.ini")
        stateview_address = config.get("settings",chain_id)
        config.read("configs\\permit2.ini")
        permit2_address = config.get("settings",chain_id)

        self.quoter_address = _str_to_addr(quoter_address)
        self.router_address = _str_to_addr(router_address)
        self.stateview_address = _str_to_addr(stateview_address)
        self.permit2_address = _str_to_addr(permit2_address)

        self.quoter = _load_contract(self.w3, abi_name = "uniswap-v4/quoter", address = self.quoter_address)
        self.router = _load_contract(self.w3, abi_name="uniswap-v4/router", address=self.router_address)
        self.stateview = _load_contract(self.w3, abi_name="uniswap-v4/stateview", address=self.stateview_address)
        self.permit2 = _load_contract(self.w3, abi_name="uniswap-v4/permit2", address=self.permit2_address)
        return

    def load_contract_with_abi(self,
                              abi_name: str,
                              address: AddressLike) -> Contract:
        return self.w3.eth.contract(address=address, abi=_load_abi(abi_name))

    def erc20_contract(self,
                      token_addr: AddressLike) -> Contract:
        return self.load_contract_with_abi(abi_name="erc20", address=token_addr)

    def approve(self, 
                token: AddressLike,
                max_approval: Optional[int]=None) -> HexBytes:
        """Give an PERMIT2 approval of a token."""
        if(token != ETH_ADDRESS):
            max_approval = self.max_approval_int if not max_approval else max_approval
            function = self.erc20_contract(token).functions.approve(_addr_to_str(self.permit2_address), max_approval)
            print(f"Approving {_addr_to_str(token)} for PERMIT2...")
            tx = self._build_and_send_tx(function)
            time.sleep(7)
        #Give an exchange/router max approval of a token.
        max_approval :int = 2 ** 100 - 1
        expiration :int = int(10 ** 12)
        print(f"Setting permit for {_addr_to_str(token)} at router contract...")
        function = self.permit2.functions.approve(_str_to_addr(token), self.router_address, max_approval, expiration)
        tx = self._build_and_send_tx(function)

        return tx

    def approval(self,
                 token: AddressLike):
        #[0]=current allowance, [1]=allowance expiration [2]=current nonce
        result = int(self.permit2.functions.allowance(self.address, token, self.router.address).call()[0])
        return result

    def _get_tx_params(self, 
                       value: int=0 ,
                       gas: int=250000) -> dict:
        """Get generic transaction parameters."""
        if self.london_style == 0:
            return {
                "from": _addr_to_str(self.address),
                "value": value,
                "gas": int(self.gas_limit),
                "gasPrice": Web3.to_wei(self.gas_price, 'gwei'),
                "nonce": max(self.last_nonce, 0),
            }
        else:
            return {
                "from": _addr_to_str(self.address),
                "gas": int(self.gas_limit),
                "maxPriorityFeePerGas": Web3.to_wei(self.london_priorityfee, 'gwei'),
                "maxFeePerGas": Web3.to_wei(self.gas_price, 'gwei'),
                "type": 2,
                "chainId": self.w3.eth.chain_id,
                "value": value,
                "nonce": max(self.last_nonce, 0),
            }
    #Gas customization
    #Gas limit
    def get_gas_limit(self) -> float:
        return self.gas_limit

    def set_gas_limit(self, gas_limit: float):
        self.gas_limit = gas_limit

    #Gas price in GWei
    def get_gas_price(self) -> float:
        return self.gas_price

    def set_gas_price(self, gas_price: float):
        self.gas_price = gas_price

    #Priority fee in GWei
    def get_gas_priorityfee(self) -> float:
        return self.london_priorityfee

    def set_gas_priorityfee(self, gas_priorityfee: float):
        self.london_priorityfee = gas_priorityfee

    #Tokens price functions
    def get_token_token_spot_price(self, 
                                   token0: AddressLike, 
                                   token1: AddressLike,
                                   fee: int=500,
                                   tick_spacing: int=10,
                                   hooks: AddressLike=ZERO_HOOK,) -> int:
        """Current spot price for token to token trades."""
        if token0 > token1:
            (token1, token0) = (token0, token1)

        pool = pool_key()
        pool.currency0 = token0
        pool.currency1 = token1
        pool.fee = fee
        pool.tick_spacing = tick_spacing
        pool.hooks = hooks
        pool_id = self.get_pool_id(pool)

        if self.version == 4:
            price : int = self.stateview.functions.getSlot0(pool_id.hex()).call()[0]
        else:
            raise ValueError("Function is not supported for this version")
        return price

    def get_quote_exact_input_single(self, 
                                     token0: AddressLike, 
                                     token1: AddressLike, 
                                     qty: int, 
                                     fee: int=500, 
                                     tick_spacing: int=10, 
                                     hooks: AddressLike=ZERO_HOOK, 
                                     hook_data:bytes=bytes()) -> int:
        """Quote for token to token single hop trades with an exact input."""
        if self.version == 4:
            if(token0 < token1):
                zero_for_one = True
            else:
                zero_for_one = False
                (token1, token0) = (token0, token1)
            pool_key = (token0,
                        token1,
                        fee,
                        tick_spacing,
                        hooks)
            #[0]=The output quote [1]=estimated gas units used for the swap
            price : int = self.quoter.functions.quoteExactInputSingle((pool_key, zero_for_one,qty, hook_data)).call()[0]
        else:
            raise ValueError("Function is not supported for this version")
        return price

    def get_pool_id(self, pool: pool_key):
        pool_data = eth_abi.abi.encode(types=["address", "address", "uint24", "int24", "address"],
                    args=[pool.currency0,
                        pool.currency1,
                        pool.fee,
                        pool.tick_spacing,
                        pool.hooks,],)
        pool_id = Web3.keccak(pool_data)
        return pool_id


    def get_token(self, 
                  address: AddressLike,
                  abi_name: str="erc20") -> ERC20Token:
        """
        Retrieves metadata from the ERC20 contract of a given token, like its name, symbol, and decimals.
        """
        # FIXME: This function should always return the same output for the
        # same input
        #        and would therefore benefit from caching
        if address == "0x0000000000000000000000000000000000000000":
            # This isn't exactly right, but for all intents and purposes,
            # ETH is treated as a ERC20 by Uniswap.
            return ERC20Token(address=address,
                name="ETH",
                symbol="ETH",
                decimals=18,)
        token_contract = _load_contract(self.w3, abi_name, address=address)
        try:
            _name = token_contract.functions.name().call()
            _symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
        except Exception as e:
            logger.warning(f"Exception occurred while trying to get token {_addr_to_str(address)}: {e}")
            raise InvalidToken(address)
        try:
            name = _name.decode()
        except Exception:
            name = _name
        try:
            symbol = _symbol.decode()
        except Exception:
            symbol = _symbol
        return ERC20Token(symbol, address, name, decimals)

    #Estimates slippage for the given amount of token0
    def estimate_price_impact(self,
        token0: AddressLike,
        token1: AddressLike,
        qty: int,
        fee: int=500,
        tick_spacing: int=10,
        hooks: AddressLike=ZERO_HOOK,
        hook_data:bytes=bytes(),
        route: Optional[List[AddressLike]]=None,) -> float:
        """
        Returns the estimated price impact as a positive float (0.01 = 1%).

        NOTE: Work-in-progress.

        See ``examples/price_impact.py`` for an example which uses this.
        """

        try:
            spot_price = self.get_token_token_spot_price(token0,
                token1,
                fee,
                tick_spacing,
                hooks)
        except (ArithmeticError, BadFunctionCallOutput):
            # ArithmeticError is raised when `token0` amount in the pool
            # equals 0.
            # BadFunctionCallOutput is raised when the pool for
            # given `(token0, token1, fee)` doesn't exist
            return 1

        if spot_price == 0:
            # Occurs when `token1` amount in the pool equals 0
            return 1
        try:
            quote_amount = self.get_quote_exact_input_single(token0,
                token1,
                fee,
                tick_spacing,
                hooks,
                hook_data)
        except ContractLogicError:
            # ContractLogicError is raised when the pool's contract for given
            # `(token0, token1, fee)` hasn't been deployed.
            return 1
        price = (quote_amount / (qty / (10 ** self.get_token(token0).decimals))) / 10 ** self.get_token(token1).decimals

        # calculate and subtract the realised fees from the price impact.  See:
        # https://github.com/uniswap-python/uniswap-python/issues/310
        price_impact_with_fees = float((spot_price - price) / spot_price)
        fee_realised_percentage = realised_fee_percentage(fee, qty)
        price_impact_real = price_impact_with_fees - fee_realised_percentage


    def get_quote_exact_output_single(self,
                                     token0: AddressLike,
                                     token1: AddressLike,
                                     qty: int,
                                     fee: int=500,
                                     tick_spacing: int=10,
                                     hooks: AddressLike=ZERO_HOOK,
                                     hook_data:bytes=bytes()) -> int:
        """Quote for token to token single hop trades with an exact output."""
        if self.version == 4:
            if(token0 < token1):
                zero_for_one = True
            else:
                zero_for_one = False
                (token1, token0) = (token0, token1)

            pool_key = (token0,
                        token1,
                        fee,
                        tick_spacing,
                        hooks,)
            #[0]=The input quote [1]=estimated gas units used for the swap
            price : int = self.quoter.functions.quoteExactOutputSingle((pool_key, zero_for_one,qty, hook_data)).call()[0]
        else:
            raise ValueError("Function is not supported for this version")
        return price


    def build_execute_params(self,):
        """
        Generic parameters builder for universal router execute() call.
        WIP
        """
        pass

    #Swap functions
    def _token_to_token_swap_input(self,
        input_token: str,
        qty: int,
        qtycap: int,
        output_token: str,
        recipient: Optional[AddressLike],
        fee: int,
        tick_spacing: int,
        hooks: str,) -> HexBytes:
        if self.version == 4:
            if recipient is None:
                recipient = self.address

            min_tokens_bought = int((1 - self.max_slippage) * qtycap)
            
            ether_amount = 0
            if(input_token == ETH_ADDRESS):
                ether_amount = qty

            #V4_SWAP // Encode swap actions
            commands = encode_packed(["uint8"], args=[0x10],)

            #SWAP_EXACT_IN_SINGLE, SETTLE_ALL, TAKE_ALL
            actions = encode_packed(["uint8","uint8","uint8"], [0x06, 0x0C, 0x0F],)

            #SETTING PARAMS
            pool_key = (input_token,
                        output_token,
                        fee,
                        tick_spacing,
                        hooks)
            if input_token < output_token:
                zero_for_one = True
                (token0, token1) = (input_token, output_token)
            else:
                zero_for_one = False
                (token0, token1) = (output_token,input_token)
            exact_input_single_params = encode(['((address,address,uint24,int24,address),bool,int128,uint128,bytes)'],
                                              [((token0, token1, fee, tick_spacing, hooks), zero_for_one, qty, min_tokens_bought, bytes(0))],)
            settle_all_params = encode(['address','uint128'], [input_token, qty],)
            take_all_params = encode(['address','uint128'], [output_token, min_tokens_bought],)

            #ENCODING DATA
            params = [exact_input_single_params, settle_all_params, take_all_params]
            inputs = []
            inputs.append(encode(['bytes','bytes[]'], [actions, params],))

            return self._build_and_send_tx(self.router.functions.execute(commands, inputs, self._deadline()), self._get_tx_params(value=ether_amount))
        else:
            raise ValueError("Function is not supported for this version")


    def _token_to_token_swap_output(self,
        input_token: AddressLike,
        qty: int,
        qtycap: int,
        output_token: AddressLike,
        recipient: Optional[AddressLike],
        fee: int,
        tick_spacing,
        hooks: AddressLike,) -> HexBytes:
        if self.version == 4:
            if recipient is None:
                recipient = self.address

            amount_in_max = int((1 + self.max_slippage) * qtycap)

            ether_amount = 0
            if(input_token == ETH_ADDRESS):
                ether_amount = qty

            #V4_SWAP // Encode swap actions
            commands = encode_packed(["uint8"],
                args=[0x10],)

            #SWAP_EXACT_OUT_SINGLE, SETTLE_ALL, TAKE_ALL
            actions = encode_packed(["uint8","uint8","uint8"],
                args=[0x09, 0x0C, 0x0F],)
            #SETTING PARAMS
            pool_key = (input_token,
                        output_token,
                        fee,
                        tick_spacing,
                        hooks,)
            if input_token < output_token:
                zero_for_one = True
                (token0, token1) = (input_token, output_token)
            else:
                zero_for_one = False
                (token0, token1) = (output_token,input_token)
            exact_output_single_params = encode(['((address,address,uint24,int24,address),bool,int128,uint128,bytes)'],
                                                [((token0, token1,fee,tick_spacing,hooks,), zero_for_one, qty, amount_in_max, bytes(0))],)
            settle_all_params = encode(["address","uint128"], [input_token, amount_in_max],)
            take_all_params = encode(["address","uint128"], [output_token, qty],)

            #ENCODING DATA
            params = (exact_output_single_params, settle_all_params, take_all_params)
            inputs = []
            inputs.append(encode(["bytes","bytes[]"], [actions, params],))

            return self._build_and_send_tx(self.router.functions.execute(commands, inputs, self._deadline()), self._get_tx_params(value=ether_amount))
        else:
            raise ValueError("Function is not supported for this version")


    #Replaces pending transaction with zero-value ETH transfer
    def drop_txn(self,
        address_to: AddressLike,
        gwei: float,
        gasv: float,
        priorityfee: int=10) -> HexBytes:

        #This one is for legacy transactions
        signed_txn = self.w3.eth.account.sign_transaction(dict(chainId=int(self.w3.net.version),
                                                              nonce=self.last_nonce,
                                                              gasPrice = Web3.to_wei(self.gas_price, 'gwei'),
                                                              gas = int(self.gas_limit),
                                                              to = Web3.to_checksum_address(address_to),
                                                              value = Web3.to_wei(0,'wei')), self.private_key)
        #This one is for post-Merge
        signed_txn_london = self.w3.eth.account.sign_transaction(dict(chainId=int(self.w3.net.version),
                                                              type=2,
                                                              nonce=self.last_nonce,
                                                              maxFeePerGas = Web3.to_wei(int(gwei), 'gwei'),
                                                              maxPriorityFeePerGas = Web3.to_wei(priorityfee, 'gwei'),
                                                              gas = int(21000),
                                                              to = Web3.to_checksum_address(address_to),
                                                              value = Web3.to_wei(0,'wei')), self.private_key)
        if self.london_style == 1:
            return self.w3.eth.send_raw_transaction(signed_txn_london.rawTransaction)  
        else:
            return self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)  

    def make_swap_input(self,
        input_token: AddressLike,
        output_token: AddressLike,
        qty: int,
        qtycap: int,
        swap_pool_key: pool_key,
        recipient: AddressLike=None,
        fee: int=3000) -> HexBytes:
        
        return self._token_to_token_swap_input(input_token, qty, qtycap, output_token, recipient, swap_pool_key.fee, swap_pool_key.tick_spacing, swap_pool_key.hooks)

    def make_swap_output(self,
        input_token: AddressLike,
        output_token: AddressLike,
        qty: int,
        qtycap: int,
        swap_pool_key: pool_key,
        recipient: AddressLike=None,
        fee: int=3000) -> HexBytes:
        
        return self._token_to_token_swap_output(swap_pool_key.currency0, qty, qtycap, swap_pool_key.currency1, recipient, swap_pool_key.fee, swap_pool_key.tick_spacing, swap_pool_key.hooks)
    
    def get_token_balance(self,
                         erc20: AddressLike) -> Decimal:

        contract = _load_contract(self.w3, abi_name = "erc20", address = erc20)
        decimals = contract.functions.decimals().call()
        try:
            balance = contract.functions.balanceOf(self.address).call()
        except:
            balance = 0
        balance = Decimal(balance) / (10 ** decimals)
        return balance

    def get_balance(self) -> Decimal:
        """Get the balance of ETH for your address."""
        try:
            balance = self.w3.eth.get_balance(self.address)
        except:
            balance = 0
        return balance

    def _deadline(self) -> int:
        """Get a predefined deadline. 10min by default."""
        return int(time.time()) + 10 * 60

    def _build_and_send_tx(self, 
                           function: ContractFunction, 
                           tx_params: Optional[dict]=None) -> HexBytes:
        """Build and send a transaction."""
        if not tx_params:
            tx_params = self._get_tx_params()
        transaction = function.build_transaction(tx_params)
        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.private_key)
        # TODO: This needs to get more complicated if we want to support
        # replacing a transaction
        # FIXME: This does not play nice if transactions are sent from other
        # places using the same wallet.
        try:
            return self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        finally:
            #logger.debug(f"nonce: {tx_params['nonce']}")
            self.last_nonce = Nonce(tx_params["nonce"] + 1)


