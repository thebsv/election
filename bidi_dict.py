from collections import OrderedDict
import weakref


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
