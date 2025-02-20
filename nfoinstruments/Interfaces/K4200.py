from pprint import pprint
from enum import Enum, auto
from abc import ABC, abstractmethod
from time import sleep

class K4200:
    def __init__(self, address, resman):
        self.address = address
        self.resource = resman.open_resource(self.address, query_delay=0.1)