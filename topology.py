class Topology:
    '''
    Class represents network topology in format:
    {('<Hostname>', '<Local port>'): ('<Remote Hostname>', '<Remote port>'),
    ('R2', 'Eth0/0'): ('SW1', 'Eth0/2'),}

    Input data expected in the same format, but cat contain duplicates.
    '''
    def __init__(self, topology_dict, raw=False):
        if raw:
            topology_dict = self._transform_topology(topology_dict)
        self.topology = self._normalize(topology_dict)

    def __add__(self, other):
        if not isinstance(other, Topology):
            raise TypeError(f'unsupported operand type(s) for +: "Topology" and "{type(other).__name__}"')
        new_topology = self.topology.copy()
        new_topology.update(other.topology)
        return Topology(new_topology)
    
    def __iter__(self):
        return iter(self.topology.items())
         

    def _normalize(self, raw_topology):
        result = {}
        for src, dst in raw_topology.items():
            if not result.get(dst):
                result[src] = dst
        return result

    def _transform_topology(self, topology_dict):
        """transforms topology, recieved with netmiko's use_textfsm parameter like:
        {'sw-dc-2-asw-1':[
             {'neighbor_name': 'sw-dc-2-dsw-2',
            'local_interface': 'Gig 0/1',
            'capabilities': 'S I',
            'platform': 'SF300-24',
            'neighbor_interface': 'gi4'},
           ]
        }
        
        to topology dict of link tuples

        Keyword arguments:
        topology_dict -- 'raw' topology dict
        Return: dict of tuples of links {('R2', 'Eth0/0'): ('SW1', 'Eth0/2'),}
        """
        formatted_topology = {}
        for l_host, links in topology_dict.items():
            for link in links:
                l_int, r_host, r_int = link['local_interface'], link['neighbor_name'], link['neighbor_interface']
                # l_int, r_host, r_int = link['local_interface'], link['neighbor'], link['neighbor_interface']
                print(l_host, l_int, r_host, r_int)
                if 'sw-' in r_host:
                    if not (r_host, r_int) in formatted_topology:
                        formatted_topology[(l_host, l_int)] = (r_host, r_int)
        return formatted_topology 

    def delete_link(self, link_src, link_dst):
        if self.topology.get(link_src):
            del self.topology[link_src]
        elif self.topology.get(link_dst):
            del self.topology[link_dst]
        else:
            print("No such link")

    def delete_node(self, node_name):
        node_not_found = True
        topology_dict = self.topology.copy()
        for src, dst in self.topology.items():
            if node_name in src or node_name in dst:
                del topology_dict[src]
                node_not_found = False
        if node_not_found:
            print("No such node")
        else:
            self.topology = topology_dict
    
    def add_link(self, link_src, link_dst):
        if any (item in self.topology for item in [link_src, link_dst]) or any (item in self.topology.values() for item in [link_src, link_dst]):
            if self.topology.get(link_src) == link_dst or self.topology.get(link_dst) == link_src:
                print('Link already exists')
            else:
                print('Link with one of ports already exists')
        else:
            print(self.topology.get(link_src))
            print(self.topology.get(link_dst))
            self.topology[link_src] = link_dst
