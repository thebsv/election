"""
The underlying network topology, this a mesh of network 'Node's that
are used to connect all the entities that participate in the election process.

    
    - ZNetwork: class which performs all the low level networking functions such as connecting to
    to all other nodes, refreshing the state of the sockets, checking for new connections, blocking until
    the majority of the nodes are connected.
        - ElectionState: class enum which holds an enum that has the election state (CONNECT, ELECT, COORDINATE, SPIN)
        - server_list: list which will hold all the other servers to connect to
        - connect_set: set which contains all the other connected nodes (which will be tested periodically)
        - socket_dict: ordered dict of port:Socket objects of all the nodes, irrespective of if they are active or not
        - connect_dict: ordered dict of port:NetState which tells me if each of the nodes in the socket_dict are active or not
        - controllerid_net: bidi dict of controller_ID:network_port of each of the nodes involved in this network
        - delmark: dict that holds all the nodes which have expired sockets/sockets that aren't active and need to be cleaned/deleted
        - majority: the minimum number of nodes in the network that need to accept the new leader, currently set to 51%
        - total_rounds: the number of election rounds that are carried out, set to len(server_list) because every node elected as
        leader may fail the acceptance phase (worst case)
    
    - ZNode: This is the lowest level socket class which will the run the zmq server and the zmq clients for
    each node in the 
        - NetState: class which holds an enum that contains the ON/OFF state
        Socket Properties:
        - timeout: int which specifies the connection timeout
        - linger: int used to set the SO_LINGER property for a socket which allows the socket to perform a graceful shutdown,
        remains active until all clients have closed their connection.
        - poll_time: int which determines the number of times a heartbeat pulse should be sent to validate another node
        - no_pulses: int number of heartbeat pulses that need to be sent to validate if a node is active or not

        
        Client Messages:
        - PULSE: string which is used as a heartbeat message from each client to the server
        - ACK: string which is used to send a reply to a heartbeat message
        - NONE: string which is used when nothing is received or an exception is encountered while recv

        Server Messages:
        - ACK: string which is used to acknowledge a any message
        - NO: string which is used as an opposite of ACK, something failed
        - LEADOK: string which is used as an acceptance message for the new leader
        - DONTCARE: string which is used as a reply to any other garbage that is received or when the server encounters an exception
"""

__author__ = "Bhargav Srinivasan"
__copyright__ = "Copyright 2024, Earth"
__email__ = "bhargav.srinivasan92@gmail.com"
__version__ = "1.1.0"


import asyncio
import logging
import os
import zmq



