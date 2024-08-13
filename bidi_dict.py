from collections import OrderedDict
import weakref


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


"""
class BidiDict:


    def __init__(self):
        self.forward = OrderedDict()
        self.reverse = OrderedDict()
    

    def put(self, key: object, value: object):
        self.forward[key] = value
        self.reverse[value] = key
    

    def get_key(self, key: object) -> object:
        if key in self.forward:
            return self.forward[key]
        else:
            raise Exception("Value for the corresponding key not present in map!")
    

    def get_value(self, value: object) -> object:
        if value in self.reverse:
            return self.reverse[value]
        else:
            raise Exception("Key for the corresponding value not present in map!")
    
    
    def delete_key(self, key: object):
        if key in self.forward:
            value = self.forward[key]
            del self.forward[key]
            del self.reverse[value]
        else:
            raise Exception("Key not present in map!")
    

    def delete_value(self, value: object):
        if value in self.reverse:
            key = self.reverse[value]
            del self.reverse[value]
            del self.forward[key]
        else:
            raise Exception("Key not present in map!")
"""
class String:
    

    def __init__(self, s):
        self.str = s
    

    def access(self):
        return self.str
    

    def change(self, s):
        self.str = s
    

    def __repr__(self):
        return self.str

MAX_INDEX = 10


class BidiDict:
    """
    A new data structure that I made to hold the connection: controllerID associations.
    """


    def __init__(self):
        self.map = {}
        self.lookup = []
        self.index = 0
    

    def put(self, key: object, value: object):
        self.map[key] = self.index
        self.index += 1
        self.map[value] = self.index
        self.index += 1
        self.lookup.append(weakref.ref(value))
        self.lookup.append(weakref.ref(key))
        
        if len(self.lookup) > MAX_INDEX:
            self._reindex()
    

    def get_value_using_key(self, key: object) -> object:
        if key in self.map:
            return self.lookup[self.map[key]]()
        else:
            raise Exception("Value for the corresponding key not present in map!")
    

    def get_key_using_value(self, value: object) -> object:
        if value in self.map:
            return self.lookup[self.map[value]]()
        else:
            raise Exception("Key for the corresponding value not present in map!")
    
    
    def delete_using_key(self, key: object):
        if key in self.map:
            index = self.map[key]
            value = self.get_value_using_key(key)
            del self.map[key]
            del self.map[value]
        else:
            raise Exception("Key not present in map!")
        
        if len(self.lookup) > MAX_INDEX:
            self._reindex()
    

    def delete_using_value(self, value: object):
        if value in self.map:
            index = self.map[value]
            key = self.get_key_using_value(value)
            del self.map[value]
            del self.map[key]
        else:
            raise Exception("Key not present in map!")
        
        if len(self.lookup) > MAX_INDEX:
            self._reindex()
    

    def _reindex(self):
        lookup_new = []
        # print("before reindex: ", str(self.map))

        for k, v in self.map.items():
            # print("key val", k, v)
            lookup_new.append(self.lookup[v])
        
        index = 0
        for k in self.map.keys():
            self.map[k] = index
            index += 1

        # print("reindexed: ", str(self.map))

        self.lookup.clear()
        self.lookup = [ x for x in lookup_new ]
        del lookup_new
    

    def __repr__(self):
        return str(self.map)


def test_bidi():
    # put in bidi map
    bd = BidiDict()

    a = String("a")
    b = String("b")
    c = String("c")
    d = String("d")
    e = String("e")
    f = String("f")

    bd.put(a, b)
    bd.put(c, d)
    bd.put(e, f)

    # get using key
    print("get a: ", bd.get_value_using_key(a))
    print("get c: ", bd.get_value_using_key(c))
    print("get e: ", bd.get_value_using_key(e))

    print("map: ", str(bd))

    # get using value
    print("get b: ", bd.get_key_using_value(b))
    print("get d: ", bd.get_key_using_value(d))

    print("map: ", str(bd))

    # delete using key
    print("delete c: ", bd.delete_using_key(c))

    print("map: ", str(bd))

    # delete using value
    print("delete f: ", bd.delete_using_key(f))

    print("map: ", str(bd))
    print("lookup: ", str(bd.lookup))


    A = String("A")
    B = String("B")
    C = String("C")
    D = String("D")
    E = String("E")
    F = String("F")

    # test reindex
    bd.put(B, A)
    bd.put(D, C)

    print("map: ", str(bd))
    print("lookup: ", str(bd.lookup))

    bd.put(F, E)

    print("map: ", str(bd))
    print("lookup: ", str(bd.lookup))

    # get using key
    print("get a: ", bd.get_value_using_key(B))
    print("get c: ", bd.get_value_using_key(D))
    print("get e: ", bd.get_value_using_key(F))

    print("map: ", str(bd))

    # get using value
    print("get b: ", bd.get_key_using_value(A))
    print("get d: ", bd.get_key_using_value(C))

    print("map: ", str(bd))

    # delete using key
    print("delete c: ", bd.delete_using_key(F))

    print("map: ", str(bd))

    # delete using value
    print("delete f: ", bd.delete_using_key(C))

    print("map: ", str(bd))
