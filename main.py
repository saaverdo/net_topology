#!/usr/env python3
# -*- coding: utf-8 -*-
# 
# 

"""
Inventory file contains list of dictionaries with device parameters and connection credentials.
For security reasons recommended way to set up credentials is to use 
environment variables SSH_USER, SSH_PASSWD, SSH_ENABLE.

example:

- device_type: cisco_ios
  hostname: sw-dc-2-asw-1
  ip: 192.168.128.8
  username: cisco
  password: cisco
  secret: cisco
  skip: false
- device_type: cisco_s300
  hostname: sw-dc-2-asw-3
  ip: 192.168.128.10
  skip: false
"""

import os
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException, ReadTimeout
from concurrent.futures import ThreadPoolExecutor
from textfsm import clitable
import yaml
from datetime import datetime
import logging
import argparse

from topology import Topology
from draw_network_graph import draw_topology


logging.getLogger("netmiko").setLevel(logging.WARNING)
logging.basicConfig(
    format="%(threadName)s %(levelname)s: %(message)s",
    level=logging.INFO,
)


ssh_username = os.environ.get('SSH_USER')
ssh_passwd = os.environ.get('SSH_PASSWD')
ssh_secret = os.environ.get('SSH_ENABLE', ssh_passwd)

raw_links = {}
dev_check = {}


cli_commands={'lldp':{'cisco_ios': 'show lldp neighbors',
                    'dlink_ds': 'show lldp remote_ports',
                    'cisco_s300': 'show lldp neighbors',
                    'ubiquiti_edgeswitch':'show lldp remote-device all'},
            'cdp':{'cisco_ios': 'show cdp neighbors',
                    'cisco_s300': 'show cdp neighbors'},
            'use_fsm':{'cisco_ios': True,
                    'dlink_ds': False,
                    'cisco_s300': True,
                    'ubiquiti_edgeswitch': False},
        }

# parse cli arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "-i",
    "--inventory",
    dest="inventory_file",
    default="inventory.yml",
    help="Name of inventory file in yaml format",
    )
parser.add_argument(
    "-p",
    "--parallel",
    dest="parallel",
    type = int,
    default=0,
    help="run with 'n' parallel connections to devices, 0 = no parallelism",
    )
parser.add_argument(
    "-proto",
    "-cdp",
    dest="discovery_proto",
    choices=['cdp', 'lldp'],
    default='cdp',
    help="use 'cdp' or 'lldp' discovery protocol",
    )
parser.add_argument(
    "--dry-run",
    dest="dry_run",
    type=bool,
    default=False,
    help="Dry-run flag: if True, runs only 'sh ver' command to check conection, no topology build",
    )
args = parser.parse_args()

def parse_command_fsm(data, attributes_dict, index_file='index', templates_dir='templates'):
    '''
    Parses command output with TextFSM templates and CliTable
    attributes_dict : {'Command': command, 'Vendor': 'cisco_ios'}
    '''
    templates_path = os.path.abspath(templates_dir)
    cli_parser = clitable.CliTable(index_file, templates_path)
    cli_parser.ParseCmd(data, attributes_dict)
    header = list(cli_parser.header)
    return [dict(zip([item.lower() for item in header], row)) for row in cli_parser]

def run_lldp_command(device: dict, dry_run=False):
    """
    device: dictionary of device parameters:
        {'device_type': 'cisco_ios',
        'ip': '192.168.128.8',
        'hostname': 'sw-dc-2-asw-1',
        'skip': False}
    
        device_type: device type according to netmico's dispatcher
        ip: device ip address or domain name
        hostname: (optional) device hostname, if not provided, 'ip' will be used instead
        username: (optional) ssh user name. if not set, will be used SSH_USER env variable
        password: (optional) ssh user password. if not set, will be used SSH_PASSWD env variable
        secret: (optional) enable password. if not set, will be used SSH_ENABLE (if set) or (SSH_PASSWD) env variable
        skip: (optional) skip the device
    """
    skip = device.get('skip', False)

    if skip:
        return

    ssh_username = os.environ.get('SSH_USER')
    ssh_passwd = os.environ.get('SSH_PASSWD')
    ssh_secret = os.environ.get('SSH_ENABLE', ssh_passwd)

    device_type = device['device_type']
    host = device.get('ip')
    hostname = device.get('hostname', host)
    dev_user = device.get('username', ssh_username)
    dev_pass = device.get('password', ssh_passwd)
    dev_secret = device.get('secret', ssh_secret)

    device_params = {'host': host,
                    'device_type': device_type,
                    'username': dev_user,
                    'password': dev_pass,
                    'secret': dev_secret}

    logging.info(f'Connecting to {hostname}')

    try:
        with ConnectHandler(**device_params) as ssh:
            if args.dry_run:
                command = 'show ver'
                logging.info(f'Dry run mode for {hostname}')
                cmd_output = ssh.send_command(command, use_textfsm=True)
                # nothing more to do in dry-run mode
                return
            else:
                command = cli_commands[args.discovery_proto][device_type]
                cmd_output = ssh.send_command(command, use_textfsm=True)
                if type(cmd_output) is str:
                    attributes_dict = {'Command': command, 'Vendor': device_type}
                    cmd_output = parse_command_fsm(cmd_output, attributes_dict, index_file='index', templates_dir='templates')
                raw_links[hostname] = cmd_output
    except (NetmikoAuthenticationException, NetmikoTimeoutException, ReadTimeout) as err:
        dev_check[hostname] = "Failed"
        logging.error(f'Error occured while running command on {hostname}')
        logging.error(f'Error: \n{err}')
        return
    else:
        dev_check[hostname] = "Ok"
        logging.info(f'Successfully recieved data from {hostname}')

if __name__ == '__main__':
    start_time = datetime.now()

    with open( os.path.abspath(args.inventory_file)) as f:
        devices = yaml.safe_load(f)

    logging.info(f'Start gathering info')
    if args.parallel:
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            results = executor.map(run_lldp_command, devices)
    else:
        for device in devices:
            run_lldp_command(device)
    if args.dry_run: exit()
    print(raw_links)
    net_topology = Topology(raw_links, raw=True)
    logging.info(f'Topology: \n{net_topology.topology}')
    draw_topology(net_topology.topology)

    print(f'Started at {start_time}')
    print(f'Finished at {datetime.now()}')
