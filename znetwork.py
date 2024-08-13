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
        - controllerID_port: bidi dict of controller_ID:network_port of each of the nodes involved in this network
        - delete_marker: dict that holds all the nodes which have expired sockets/sockets that aren't active and need to be cleaned/deleted
        - majority: the minimum number of nodes in the network that need to accept the new leader, currently set to 51%
        - total_rounds: the number of election rounds that are carried out, set to len(server_list) because every node elected as
        leader may fail the acceptance phase (worst case)
    
    - ZNode: This is the lowest level, a socket class which will the run the zmq server and the zmq clients for
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
import os
import zmq
import zmq.asyncio

# importing the object from the election class, since it is a singleton
# singleton object + DI of higher level class -> into N lower level classes
from election import ael
from typing import List, Dict, Tuple


# Constants belonging to the ZNode class
CONFIG_FILE = "server.config"
NO_QUEUE = 1
SO_LINGER = 0

ACK = "ACK"
DONTCARE = "DONTCARE"
LEADOK = "LEADOK"
NO = "NO"
NONE = "NONE"
PULSE = "PULSE"


class ZNode:
    

    def __init__(self, server_port: str, controller_id: str) -> None:
        self.server_port = server_port

        self.server_socket = None
        self.client_sockets = {}
        self.node_list = []
        
        self._parse_configuration(CONFIG_FILE)
        self._create_client_sockets(self.server_port, self.node_list)

        self.async_election = ael
        self.controller_id = controller_id

    
    def _parse_configuration(self, config_file: str):
        with open(config_file, "r") as config:
            for line in config:
                self.node_list.append(line.strip())    


    def _create_client_sockets(self, server_port: str, node_list: List[str]) -> None:
        context = zmq.asyncio.Context()
        for node in node_list:
            client_socket = context.socket(zmq.REQ)
            client_socket = self._apply_performance_optimizations(client_socket)
            client_socket.connect(f"tcp://localhost:{node}")
            self.client_sockets[node] = client_socket
    

    def _apply_performance_optimizations(self, csocket):
        # Socket performance optimizations
            
        # ZMQ related
        csocket.setsockopt(zmq.IMMEDIATE, NO_QUEUE) # no queueing

        # TCP related
        csocket.setsockopt(zmq.TCP_KEEPALIVE, 1)
        csocket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
        csocket.setsockopt(zmq.TCP_KEEPALIVE_CNT, 10)

        # Other
        csocket.setsockopt(zmq.LINGER, SO_LINGER) # disconnect immediately upon close

        return csocket


    def _process_server_message(self, message: str) -> str:
        switch = message[0]

        try:
            if switch == 'I':
                _, temp_leader, timestamp = switch.split(" ")
                # This is the IWON message, so we need to set a temp leader and the timestamp
                # at which this message was received (to sequence it correctly to this particular 3PC)
                self.async_election.set_temp_leader(temp_leader)
                self.async_election.set_timestamp(timestamp)
                return ACK
            
            elif switch == 'L':
                _, temp_leader, timestamp = switch.split(" ")
                # This is the LEADER message, which upon receipt, we need to use to either retrieve an exisitng
                # leader or if a current leader does not exist, meaning the election is in progress, then return no
                if self.async_election.get_temp_leader() == temp_leader and self.async_election.get_timestamp() == timestamp:
                    return LEADOK
                else:
                    # this is done to avoid out of sequence leaders, in case the above timestamp check condition fails,
                    # we need to reset the leader to none and start the election again
                    self.async_election.set_temp_leader(NONE)
                    self.async_election.set_leader(NONE)
                    return NO
            
            elif switch == 'S':
                _, temp_leader, timestamp = switch.split(" ")
                # This is the SETLEAD message, in this case we need to check if this controller id is not the leader, because
                # we only self set leader when a majority of acceptors have accepted it. This is only for the followers.
                if self.async_election.get_temp_leader() != self.controller_id:
                    # If both checks pass, this is the temp leader that was set by the previous phase, and it is in sequence,
                    # then set this temp leader as the leader
                    if self.async_election.get_temp_leader() == temp_leader and self.async_election.get_timestamp() == timestamp:
                        self.async_election.set_leader(temp_leader)
                        self.async_election.set_temp_leader(NONE)
                        return ACK
                    else:
                        # If one of the above checks fail, meaning it is not 3PC, or it is out of sequence, then reset the leader
                        self.async_election.set_temp_leader(NONE)
                        self.async_election.set_leader(NONE)
                        return NO
                else:
                    self.async_election.set_temp_leader(NONE)
                    self.async_election.set_leader(NONE)
                    return NO

            elif switch == 'Y':
                _, temp_leader, timestamp = switch.split(" ")
                # This is the YOU? message, which is used to query this instance if it is the leader, and its ID is appended 
                # with the temp leader ID that was set along with the YOU? message, and ideally these two should match if it is the leader
                if self.async_election.get_leader() == self.controller_id:
                    return self.controller_id + " " + temp_leader
                else:
                    return NO
                
            elif switch == 'H':
                _, temp_leader, timestamp = switch.split(" ")
                # This is the heartbeat message, the response to which is an ack plus the current timestamp, if a current leader
                # has been set, otherwise return no
                if self.async_election.get_leader() == temp_leader:
                    return ACK + timestamp
                else:
                    return NO
            
            elif switch == 'P':
                # Response to an incoming PULSE message, return ACK
                return ACK
            
            elif switch == 'M':
                # Response to an incoming M message, return ACK
                return ACK
            
        except Exception as e:
            print(f"Error while processing the message received by the server {message}: {str(e)}")
            return DONTCARE
    

    async def server_loop(self) -> None:
        context = zmq.asyncio.Context()
        self.server_socket = context.socket(zmq.REP)
        self.server_socket = self._apply_performance_optimizations(self.server_socket)
        self.server_socket.bind(f"tcp://*:{self.server_port}")
        print(f"Server started on port: {str(self.server_port)}")

        try:
            while True:

                try:
                    message = await self.server_socket.recv_string()
                    # print(f"Received message: {message}")
                except Exception as e:
                    print(f"Exception: {str(e)}")

                reply = self._process_server_message(message)

                try:
                    await self.server_socket.send_string(reply)
                except Exception as e:
                    print(f"Exception while sending from the server: {str(e)}")
                
        except Exception as e:
            print(f"Exiting server... {str(e)}")
        finally:
            self.server_socket.close()
    
    
    def node_send_message(self, to_node: str, message: str) -> bool:
        try:
            client_socket = self.client_sockets[to_node]
            client_socket.send_string(message)
            return True
        except Exception as e:
            print(f"Could not send message from {to_node}: {message}, {str(e)}")
        return False
    

    def node_recv_message(self, from_node: str) -> str:
        try:
            client_socket = self.client_sockets[from_node]
            return client_socket.recv_string()
        except Exception as e:
            print(f"Could not recv message from {from_node}: {str(e)}")
        return NONE
    

    def __delattr__(self):
        self.server_socket.close()
        for client_sock in self.client_sockets:
            try:
                client_sock.close()
            except Exception as e:
                print(f"Error closing client socket: {str(e)}")


async def main_node():
    try:
        # Test server loop run 5252, 5253
        node1 = ZNode("5252", "1")
        node2 = ZNode("5253", "2")
        
        asyncio.create_task(node1.server_loop()) 
        asyncio.create_task(node2.server_loop())

        # Test client socket, send a message to 5253
        node1.send_message("5253", "Mhello")
        rep = await node1.recv_message("5253")
        print(f"node1 to node2 reply: {str(rep)}")
        node2.send_message("5252", "Mhello")
        rep = await node2.recv_message("5252")
        print(f"node2 to node1 reply: {str(rep)}")

    except Exception as e:
        print(f"error starting server: {str(e)}")
        os._exit(1)


"""
The network uses the node class, and it implements convenience functions for the
election class that will maintain persistent mesh connections between all the nodes.

Over here, we read all the nodes from the config file and make a ZNode object for it, with its own 
controller ID and also insert this into the respective connection tracker mechanisms designed below.

Again, we can make this a singleton class, since we need only one object of this. These functions would
be fine on their own, but since they all relate to connection tracking, I've put them under this class.

In the above, we tightly coupled the election and ZNode objects, next we will export this class
which is the network through which messages are sent. 

The election class interacts with both the node class and the network class. It does command and 
control through the network class, and its state gets modified by the N node classes, specifically 
only the server sockets of the nodes during the election.

Therefore, there is very tight coupling between both the network and the node.

There is loose coupling between the node and the election algorithm, because if you wanted to 
change the election logic, you can do that independently by not touching the getters and setters of 
the election class. The election class only interacts with the node's server socket, and other parts of 
the node are largely untouched.

There is loose coupling between the network and the election algorithm, the network is just used. The
command and control still happens from the election class to the network, and this does not happen in the
reverse direction.


"""
from enum import Enum


class NetState(Enum):
    ON = 1
    OFF = 2


class ZNetwork:


    def __init__(self, task_group: object):
        
        # list of all the nodes
        self.server_list = []
        
        # set of nodes which are pending connection
        self.connect_set = set()

        # both are the same, one holds port:socket_object, another 
        # port:state(on/off), doing this for easy lookup without 
        # needing to store tuples and index them (performant)
        self.socket_dict = {}
        self.connect_dict = {}

        # this is to lookup the corresponding controllerID for a port/node
        self.controllerID_port = {}

        # to store expired connections that can be cleaned/deleted
        self.delete_marker = {}

        # to hold all the task objects created for each server loop
        self.server_tasks = []

        # parse the config file for the server ports
        self._parse_server_config(CONFIG_FILE)

        # hold the asyncio task group to spawn server loops
        self.task_group = task_group


    def _parse_server_config(self, config_file: str):
        with open(config_file, "r") as config:
            cid = 1
            for line in config:
                port = line.strip()
                self.server_list.append(port)
                self.controllerID_port[port] = cid
                cid += 1
    

    def send_message(self, to_node: str, message: str) -> bool:
        # This send message function is for the higher level classes to access,
        # and send messages through the network
        try:
            client_socket = self.socket_dict[to_node]
            client_socket.send_string(message)
            return True
        except Exception as e:
            print(f"Could not send message from {to_node}: {message}, {str(e)}")
        return False
    

    def recv_message(self, from_node: str) -> str:
        # This recv message function is for the higher level classes to access,
        # and receive messages from the network
        try:
            client_socket = self.socket_dict[from_node]
            return client_socket.recv_string()
        except Exception as e:
            print(f"Could not recv message from {from_node}: {str(e)}")
        return NONE


    async def check_for_new_connections(self) -> Dict[str, object]:
        _ = await self._expire_old_connections()
        self.connect_set = set([ port for port in self.server_list ])
        ret = await self._connect_clients()
        return ret


    async def block_until_connected(self) -> List[object]:
        await self._clean_state()

        # nothing is connected yet, fill the set with all ports/nodes
        self.connect_set = set([ port for port in self.server_list ])

        while True:
            try:
                _, server_tasks = await self.check_for_new_connections()
                asyncio.sleep(0)
            except Exception as e:
                print(f"Block Until Connected errored out: {str(e)}")
                return False
        
        # we call update again here, just to be sure
        await self._update_connection_dict()
        return server_tasks
    
    
    async def _clean_state(self):
        for port, socket in self.socket_dict.items():
            try:
                del socket
                self.delete_marker.append(port)
            except Exception as e:
                print(f"Could not delete client socket: {str(e)}")
        
        for port in self.delete_marker:
            del self.socket_dict[port]
        
        self.socket_dict = {}
        self.connect_dict = {}

        self.connect_set = set([ port for port in self.server_list ])

        self.delete_marker = []
    
    
    async def _connect_clients(self) -> Dict[str, object]:
        diff_set = self.connect_set.difference(set(self.socket_dict.keys()))
        print(f"diff_set: ", str(diff_set))


        for port in diff_set:
            cid = self.controllerID_port[port]
            client_sock = ZNode(port, cid)
            self.task_group.create_task(client_sock.server_loop())

            print(f"socket: {client_sock.__dict__}")
            print(f"controller ID: {client_sock.controller_id}")
            
            # check the connection
            try:
                # send a pulse to check for connectivity
                await client_sock.node_send_message(port, PULSE)
                reply = await client_sock.node_recv_message(port)

                # print(f"reply: {reply}")

                # verify the ack, and add it to the socket dict
                # and the connect dict, if not, delete the socket
                if reply == ACK:
                    if port not in self.socket_dict:
                        # store the connection
                        self.socket_dict[port] = client_sock
                    else:
                        del client_sock
                else:
                    del client_sock
            
            except Exception as e:
                print(f"Could not test/verify that the node {port} was connected: {str(e)}")
                del client_sock
        
        # delete already connected connections from connect_set
        for port in self.connect_dict.keys():
            self.connect_set.remove(port)
        
        await self._update_connection_dict()
        return self.connect_dict
    

    async def _expire_old_connections(self) -> Dict[str, object]:
        for port, sock in self.socket_dict.items():
            try:                
                # send a pulse to self to check for connectivity
                await sock.node_send_message(port, PULSE)
                reply = await sock.node_recv_message(port)

                if reply != ACK:
                    del sock
                    self.delete_marker.append(port)
            
            except Exception as e:
                print(f"Bad reply/no response from the client {port} : {str(e)}")
                self.delete_marker.append(port)
        
        try:
            for port in self.delete_marker:
                # ensure that the socket is closed
                if port in self.socket_dict:
                    sock = self.socket_dict[port]
                    del sock
                    del self.socket_dict[port]
            
        except Exception as e:
            print(f"Error while deleting old connections: {str(e)}")
        
        await self._update_connection_dict()
        return self.connect_dict
    

    async def _update_connection_dict(self):
        # clear the whole map
        self.connect_dict.clear()

        # mark all the connections to be made as OFF
        for port in self.connect_set:
            self.connect_dict[port] =  NetState.OFF
        
        # mark all the connections which have been made as ON
        for port in self.socket_dict.keys():
            self.connect_dict[port] = NetState.ON


async def main_network():
    try:
        async with asyncio.TaskGroup() as task_group:
            znet = ZNetwork(task_group)
            await znet.block_until_connected()
    except Exception as e:
        print(f"Could not start network: {str(e)}")


if __name__ == "__main__":
    # asyncio.run(main_node())
    asyncio.run(main_network())
    # test_bidi()
