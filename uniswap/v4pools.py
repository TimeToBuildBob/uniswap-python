from typing import List, Any, Optional, Callable, Union, Tuple, Dict
from xml.etree import ElementTree as ET
import os
from web3 import Web3
import eth_abi.abi
from .v4types import *
from .v4constants import (
    _netid_to_name,
    _poolmanager_contract_addresses_v4,
)
from .util import (
    _addr_to_str,
    _load_contract,
    _load_contract_erc20,
    _str_to_addr,
)


class V4pools():
    """Uniswap V4 pools handler"""
    def __init__(self,
                 web3: Web3,):
        self.poolkeys_list = list()
        self.web3 = web3
        self.last_block = 0


    def get_last_block(self,) -> int:
        return self.last_block

    def set_last_block(self, value: int):
        self.last_block = value

    def fetch_poolkey_data(self, first_block_number: int, chunk_size: int=500, clear_list: bool=True,):
       """
        :param pool_manager_contract_address PoolManager address on the network specified by w3 param
        :param chunk_size defines amount of blocks per log request
       """
       #Scans PoolManager contract initialize() logs in order to get list of
       #all pools.  See documentation for suggested starting blocks.
       #chunk_size default value should be suitable for public nodes; increase
       #on private nodes for better performance

       chain_id = int(self.web3.net.version)
       net_name = _netid_to_name[chain_id]
       pool_manager_contract_address = _poolmanager_contract_addresses_v4[net_name]
       pool_manager_contract = _load_contract(self.web3, "uniswap-v4/poolmanager", _str_to_addr(pool_manager_contract_address))
       last_block_number = self.web3.eth.get_block_number()

       chunks_amount = int((last_block_number - first_block_number) // chunk_size)
       start_block = first_block_number
       end_block = 0

       print(f"Logs proccessing started, start block = {start_block}; end block = {last_block_number}.")
       if clear_list:
            self.poolkeys_list.clear()

       for i  in range(0, chunks_amount):
        if start_block + chunk_size <= last_block_number:
            end_block = start_block + chunk_size
        else:
            end_block = last_block_number
        print(f"Processing chunk {i}/{chunks_amount}; (start block = {start_block}; end block = {end_block})",end='\r',flush=True)
        logs = pool_manager_contract.events.Initialize().get_logs(from_block=start_block, to_block=end_block,)
        for log_item in logs:
            txn = self.web3.eth.get_transaction_receipt(log_item.transactionHash)
            if txn.to.lower() != pool_manager_contract_address.lower() or int(txn.status) == 0:
                continue
            try:
                pool_currency0 = log_item.args.currency0
                pool_currency1 = log_item.args.currency1
                pool_fee = int(log_item.args.fee)
                pool_tick_spacing = int(log_item.args.tickSpacing)
                pool_hooks = log_item.args.hooks
                pool : pool_key = pool_key(pool_currency0,
                                           pool_currency1,
                                           pool_fee,
                                           pool_tick_spacing,
                                           pool_hooks)
                self.poolkeys_list.append(pool)
            except:
                continue
        if end_block == last_block_number:
            break
        start_block = start_block + chunk_size

       print(f"---------------------------------------------------------------------------------------------")
       print(f"Logs proccessing completed. Last block processed {last_block_number}")
       self.set_last_block(last_block_number)
       return
    
    def save_poolkeys_list(self, poolkey_data_filename: str):
        """Saves poolKey list to specified file (XML format supposed)"""
        pool_data = ET.Element('PoolData')

        for pool_item in self.poolkeys_list:
            pool = ET.SubElement(pool_data, 'Pool')

            currency0 = ET.SubElement(pool, 'Currency0')
            currency0.text = str(pool_item.currency0)

            currency1 = ET.SubElement(pool, 'Currency1')
            currency1.text = str(pool_item.currency1)

            fee = ET.SubElement(pool, 'Fee')
            fee.text = str(pool_item.fee)

            tick_spacing = ET.SubElement(pool, 'TickSpacing')
            tick_spacing.text = str(pool_item.tick_spacing)

            hooks = ET.SubElement(pool, 'Hooks')
            hooks.text = str(pool_item.hooks)

        ET.ElementTree(pool_data).write(poolkey_data_filename)
        return
    
    def load_poolkeys_list(self, poolkey_data_filename: str):
        """Loads poolKey list from specified file (XML format supposed)"""
        if(os.path.isfile(poolkey_data_filename)):
            try:
                tree = ET.parse(poolkey_data_filename)
            except ParseError:
                raise ValueError("Parse error, file seems to be corrupted (" + poolkey_data_filename + ")")
            self.poolkeys_list.clear()
            root = tree.getroot()
            for item in root:
                pool_currency0 = item[0].text
                pool_currency1 = item[1].text
                pool_fee = int(item[2].text)
                pool_tick_spacing = int(item[3].text)
                pool_hooks = item[4].text
                pool : pool_key = pool_key(pool_currency0,
                                           pool_currency1,
                                           pool_fee,
                                           pool_tick_spacing,
                                           pool_hooks)
                self.poolkeys_list.append(pool)
        else:
            raise ValueError("Couldn't locate file " + poolkey_data_filename)

        
    def get_poolkeys_sublist(self, currency0: str, currency1: str) -> List:
        """Returns all pools for the (currency0, currency1) pair"""
        if(currency0 < currency1):
            (c0, c1) = (currency0, currency1)
        else:
            (c0, c1) = (currency1, currency0)
        result_list = [x for x in self.poolkeys_list if c0 == x.currency0 and c1 == x.currency1]
        return result_list


