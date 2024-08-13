"""
This module implements a simple self healing leader election algorithm which is a modded version
of the RAFT distributed consensus algorithm, which is fully fault tolerant upto N nodes.

I added a constraint such that a majority variable is used and is set to 51% of acceptors that need 
to accept this node as the new leader before it is set to be so. The number of total rounds for election will 
also be set equal to the total number of nodes participating in the election, so that the failure
of a node does not affect the process and it is fully fault tolerant.

A failure detector is also implemented which sends periodic heartbeats (PULSE messages) from each of the
FOLLOWERS to the LEADER, and checks if the LEADER successfully responds to a majority of them. If this fails 
it indicates that the LEADER is dead, and the entire system is switched back to the ELECT state to pick a new LEADER

Note that each node has its own controllerID but this election state is synchronized across all the nodes in the network,
this is a bit of a design glitch, I'll try to correct this.

    - znetwork: an object which contains an abstraction of the underlying network mesh containing all the nodes
    - async_ election: an object of this class containing the state of the entire election system
    - election_priorities: list which can be used to CHEAT/OVERRIDE the LEADER elected democratically by the system, in case
    of emergencies (HITLER mode)
    
    Election Variables:
    - controller_id: string which contains the controller ID of this application 
    - leader: string which contains the controllerID of the leader of the system
    - temp_leader: string which contains the elected leader before the acceptance phase
    - connection_dict: dict which holds controllerID:NetState mapping for all the participants of the election
    - current_state: variable which holds the current ElectionState of the system
    - relax: int which holds the time for which it should be spinning in the rest state
    
    Election Messages:
    - ACK: string message to acknowledge any message received
    - PULSE: string message which is used to send a heartbeat message
    - YOU?: string message which is used in the check for leader function to check if a node is the leader
    - NO: string message which is used in case of a failure or exception'
    - IWON: string message which is sent by the recently elected leader to all the followers (phase I)
    - LEADER: string message which is sent by the leader which won the election to all the followers (phase II)
    - LEADOK: string message which is sent by each of the acceptors/followers to ack the leader (phase II)
    - SETLEAD: string message which is sent by the leader at the end of the three phase commit to indicate that it will set itself
    as the network wide leader (phase III)
    

"""

__author__ = "Bhargav Srinivasan"
__copyright__ = "Copyright 2024, Earth"
__email__ = "bhargav.srinivasan92@gmail.com"
__version__ = "1.1.0"


import logging
import os

from typing import List


MAJORITY_PERCENT = 0.51


# Message that can be sent as is
NONE = "NONE"
LEADER = NONE
TEMP_LEADER = NONE
ACK = "ACK"
PULSE = "PULSE"
YOU = "YOU?"
NO = "NO"
LEADOK = "LEADOK"


# Messages to be appended with a timestamp
IWON = "IWON "
SETLEAD = "SETLEAD "
LEADERMSG = "LEADER "
HEARTBEAT = "HEARTBEAT "


from enum import Enum
class ElectionState:
    CONNECT = 1
    ELECT = 2
    COORDINATE = 3
    SPIN = 4


class AsyncElection:

    _instance = None


    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AsyncElection, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    

    def __init__(self):
        pass


    def max_raft():
        pass
    
    
    def get_temp_leader(self) -> str:
        pass
    
    
    def set_temp_leader(self, temp_leader: str):
        pass
    

    def get_timestamp(self) -> str:
        pass
    

    def set_timestamp(self, timestamp: str):
        pass


    def get_leader(self) -> str:
        pass
    

    def set_leader(self):
        pass


ael = AsyncElection()
