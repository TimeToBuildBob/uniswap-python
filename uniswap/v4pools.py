from typing import List, Any, Optional, Callable, Union, Tuple, Dict
from xml.etree import ElementTree
import configparser
from web3 import Web3
import eth_abi.abi
from .uni4base import *
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
        self.poolkeys_list = List()
        self.web3 = web3
        self.last_block = 0


    def get_last_block(self,) -> int:
        return self.last_block

    def set_last_block(self, value: int):
        self.last_block = value

    def fetch_poolkey_data(self, first_block_number: int, chunk_size: int=500):
       """
        :param pool_manager_contract_address PoolManager address on the network specified by w3 param
        :param chunk_size defines amount of blocks per log request
       """
       #Scans PoolManager contract initialize() logs in order to get list of
       #all pools.See documentation for suggested starting blocks
       #
       #chunk_size default value should be suitable for public nodes; increase
       #on private nodes for better performance

       chain_id = self.web3.net.version
       config = configparser.ConfigParser()
       config.read("configs\\poolmanager.ini")
       pool_manager_contract_address = config.get("settings",chain_id)
       pool_manager_contract = _load_contract(self.web3, "uniswap-v4/poolmanager", _str_to_addr(pool_manager_contract_address))
       last_block_number = this.web3.eth.get_block_number()

       chunks_amount = int((last_block_number - first_block_number) // chunk_size)
       start_block = first_block_number
       end_block = 0

       print("Logs proccessing started.")

       for i  in range(0, chunks_amount + 1):
        #{
        print(f"Processing chunk {i}/{chunks_amount}",end='\r',flush=True)
        if i < chunksAmount:
            end_block = start_block + chunk_size
        else:
            end_block = this.web3.eth.get_block_number()
        logs = pool_manager_contract.events.initialize().get_logs(fromBlock=start_block, toBlock=end_block,)
        for log_item in logs:
            txn = this.web3.eth.get_transaction_receipt(log_item["TransactionHash"])
            if txn["to"].lower() != pool_manager_contract_address.lower() or txn["status"] == 0:
                continue
            pool : pool_key = pool_key()
            pool.currency0 = log_item["event"]["currency0"]
            pool.currency1 = log_item["event"]["currency1"]
            pool.fee = log_item["event"]["fee"]
            pool.tick_spacing = log_item["event"]["tickSpacing"]
            pool.hooks = log_item["event"]["hooks"]
            self.poolkeys_list.append(pool)
        start_block = start_block + chunk_size

       print(f"Logs proccessing completed. Last block processed {end_block}")
       self.set_last_block(end_block)
       return
    
    def save_poolkeys_list(self, poolkey_data_filename: str):
        """Saves poolKey list to specified file (XML format supposed)"""
        element_tree = ElementTree()
        pool_data = element_tree.Element('PoolData')

        for item in self.poolkeys_list:
            pool = element_tree.SubElement(pool_data, 'Pool')

            currency0 = element_tree.SubElement(pool, 'Currency0')
            currency0.text = str(item[0])

            currency1 = element_tree.SubElement(pool, 'Currency1')
            currency1.text = str(item[1])

            fee = element_tree.SubElement(pool, 'Fee')
            fee.text = str(item[2])

            tick_spacing = element_tree.SubElement(pool, 'TickSpacing')
            tick_spacing.text = str(item[3])

            hooks = element_tree.SubElement(pool, 'Hooks')
            hooks.text = str(item[4])

        final_data = element_tree.ElementTree(pool_data)
        final_data.write(poolkey_data_filename)
        return
    
    def load_poolkeys_list(self, poolkey_data_filename: str):
        """Loads poolKey list from specified file (XML format supposed)"""
        if(os.path.isfile(poolkey_data_filename)):
            try:
                element_tree = ElementTree()
                tree = element_tree.parse(poolkey_data_filename)
            except ParseError:
                raise ValueError("Parse error, file seems to be corrupted (" + poolkey_data_filename + ")")
            self.poolkeys_list.clear()
            root = tree.getroot()
            for item in root:
                pool : pool_key = pool_key()
                pool.currency0 = item[0].text
                pool.currency1 = item[1].text
                pool.fee = int(item[2].text)
                pool.tick_spacing = int(item[3].text)
                pool.hooks = item[4].text
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


