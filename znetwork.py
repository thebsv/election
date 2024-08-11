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
# singleton DI of higher level class -> into N lower level classes (that's the pattern)
from election import ael


from typing import List


"""
import concurrent.futures
class ZNode1:

    def __init__(self, send_timeout: int, so_linger: int, server_port: str) -> None:
        self.send_timeout = send_timeout
        self.so_linger = so_linger
        self.server_port = server_port

        self.server_socket = None
        self.client_sockets = {}
        
        self.node_list = self._parse_configuration(CONFIG_FILE)
        print("servers: ", self.node_list)
        self._create_client_sockets(self.server_port, self.node_list)

    
    def _parse_configuration(self, config_file: str) -> List[str]:
        servers = []
        with open(config_file, "r") as config:
            for line in config:
                line = line.strip()
                servers.append(line)
        return servers


    def _create_client_sockets(self, server_port: str, node_list: List[str]) -> None:
        context = zmq.Context()
        for node in node_list:
            if node != server_port:
                client_socket = context.socket(zmq.REQ)
                client_socket.connect(f"tcp://localhost:{node}")
                self.client_sockets[node] = client_socket
    
    
    def server_loop(self) -> None:
        context = zmq.Context()
        self.server_socket = context.socket(zmq.REP)
        self.server_socket.bind(f"tcp://*:{self.server_port}")
        print(f"Server started on port: {str(self.server_port)}")

        try:
            while True:
                try:
                    message = self.server_socket.recv_string()
                    print(f"Received message: {message}")
                except Exception as e:
                    print(f"Exception: {str(e)}")

                try:
                    self.server_socket.send_string("ACK")
                except Exception as e:
                    print(f"Exception: {str(e)}")
        except Exception as e:
            print(f"Exiting server... {str(e)}")
    
    
    def send_message(self, node: str, message: str) -> str:
        try:
            client_socket = self.client_sockets[node]
            client_socket.send(message.encode('utf-8'))
            return client_socket.recv_string()
        except Exception as e:
            print(f"Could not send message from {node}: {message}, {str(e)}")
    

def main1():
    try:
        # Test server loop run 5252, 5253
        node1 = ZNode1(1, 1, "5252")
        node2 = ZNode1(1, 1, "5253")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = { 
                executor.submit(node1.server_loop) : node1, 
                executor.submit(node2.server_loop): node2
            }

            # Test client socket, send a message to 5253
            rep = node1.send_message("5253", "hello")
            print(f"node1 to node2 reply: {str(rep)}")
            rep = node2.send_message("5252", "hello")
            print(f"node2 to node1 reply: {str(rep)}")

    except Exception as e:
        print(f"error starting server: {str(e)}")
        os._exit(1)
"""

# Constants belonging to the ZNode class
CONFIG_FILE = "server.config"
NO_QUEUE = 1
SO_LINGER = 0

ACK = "ACK"
NO = "NO"
LEADOK = "LEADOK"
DONTCARE = "DONTCARE"
NONE = "NONE"


class ZNode:
    

    def __init__(self, server_port: str, controller_id: str) -> None:
        self.server_port = server_port

        self.server_socket = None
        self.client_sockets = {}
        
        self.node_list = self._parse_configuration(CONFIG_FILE)
        self._create_client_sockets(self.server_port, self.node_list)

        self.async_election = ael
        self.controller_id = controller_id

    
    def _parse_configuration(self, config_file: str) -> List[str]:
        servers = []
        with open(config_file, "r") as config:
            for line in config:
                servers.append(line.strip())
        return servers


    def _create_client_sockets(self, server_port: str, node_list: List[str]) -> None:
        context = zmq.asyncio.Context()
        for node in node_list:
            if node != server_port:
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
            
            elif switch == 'm':
                # Response to an incoming m message, test message, return ACK
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
                    print(f"Received message: {message}")
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
    
    
    def send_message(self, node: str, message: str) -> str:
        try:
            client_socket = self.client_sockets[node]
            client_socket.send_string(message)
            return client_socket.recv_string()
        except Exception as e:
            print(f"Could not send message from {node}: {message}, {str(e)}")
    

    def __delattr__(self):
        for client_sock in self.client_sockets:
            try:
                client_sock.close()
            except Exception as e:
                print(f"Error closing client socket: {str(e)}")


async def main():
    try:
        # Test server loop run 5252, 5253
        node1 = ZNode("5252", "1")
        node2 = ZNode("5253", "2")
        
        t1 = asyncio.create_task(node1.server_loop()) 
        t2 = asyncio.create_task(node2.server_loop())

        # Test client socket, send a message to 5253
        rep = await node1.send_message("5253", "mhello")
        print(f"node1 to node2 reply: {str(rep)}")
        rep = await node2.send_message("5252", "mhello")
        print(f"node2 to node1 reply: {str(rep)}")

        await t1
        await t2

    except Exception as e:
        print(f"error starting server: {str(e)}")
        os._exit(1)


if __name__ == "__main__":
    asyncio.run(main())
