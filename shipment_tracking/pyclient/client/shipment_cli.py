# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------
'''     
Command line interface for the shipment transaction family.

Parses command line arguments and passes it to the Shipment class
to process.
''' 

import argparse
import getpass
import logging
import os
import sys
import traceback
import pkg_resources

from colorlog import ColoredFormatter

from client.shipment_client import ShipmentClient

DISTRIBUTION_NAME = 'shipment'

DEFAULT_URL = 'http://rest-api:8008'

def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)
    clog.setLevel(logging.DEBUG)
    return clog

def setup_loggers(verbose_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))
    
def add_shipment_parser(subparser,parent_parser):
    parser = subparser.add_parser(
        'add',
        help='adds specified count of item of specified type at specified place',
        parents=[parent_parser])
    parser.add_argument('shipmentID',type=str, help='shipmentID')
    parser.add_argument('placeName', type=str, help='place')
    parser.add_argument('N', type=str, help='no of different item types')
    # parser.add_argument('itemName', type=str, help='item to be added')
    # parser.add_argument('itemCount', type=str, help='count to be added')
    parser.add_argument('items', nargs='*', help='item names followed by their corresponding counts')

def remove_items_shipment_parser(subparser,parent_parser):
    parser = subparser.add_parser(
        'remove',
        help='removes specified count of item of specified type at specified place',
        parents=[parent_parser])
    parser.add_argument('shipmentID',type=str, help='shipmentID')
    parser.add_argument('placeName', type=str, help='place')
    parser.add_argument('N', type=str, help='no of different item types')
    # parser.add_argument('itemName', type=str, help='item to be removed')
    # parser.add_argument('itemCount', type=str, help='count to be removed')
    parser.add_argument('items', nargs='*', help='item names followed by their corresponding counts')

def item_count_parser(subparsers,parent_parser):
    parser = subparsers.add_parser('getcount',help='shows count of items of specified type at a particular place',parents=[parent_parser])
    parser.add_argument('itemName',type=str,help='the name of the item')
    parser.add_argument('placeName',type=str,help='the name of the place')

def shipment_path_parser(subparsers,parent_parser):
    parser = subparsers.add_parser('path',help='shows path of the shipment',parents=[parent_parser])
    parser.add_argument('shipmentID',type=str,help='the ID of the shipment')
    parser.add_argument('placeName',type=str,help='the name of the place') 



def transfer_shipment_parser(subparsers, parent_parser):
    parser =  subparsers.add_parser('transfer',help='to transfer shipment of given ID from one place to other',
                                    parents=[parent_parser])
    parser.add_argument('shipmentID',type=str,help='id of the shipment to be transfered')
    parser.add_argument('placeFrom',type=str,help='Name of the start place')
    parser.add_argument('placeTo',type=str,help='Name of the Destination')


def create_parent_parser(prog_name):
    '''Define the -V/--version command line options.'''
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parent_parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='display version information')

    return parent_parser


def create_parser(prog_name):
    '''Define the command line parsing for all the options and subcommands.'''
    parent_parser = create_parent_parser(prog_name)

    parser = argparse.ArgumentParser(
        description='Provides subcommands to manage your simple wallet',
        parents=[parent_parser])

    subparsers = parser.add_subparsers(title='subcommands', dest='command')

    subparsers.required = True

    add_shipment_parser(subparsers, parent_parser)
    remove_items_shipment_parser(subparsers, parent_parser)
    transfer_shipment_parser(subparsers, parent_parser)
    item_count_parser(subparsers, parent_parser)
    shipment_path_parser(subparsers,parent_parser)
    return parser

def _get_keyfile(placeName):
    '''Get the private key for a place.'''
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.priv'.format(key_dir, placeName)

def _get_pubkeyfile(placeName):
    '''Get the public key for a place.'''
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.pub'.format(key_dir, placeName)

def do_add(args):
    '''Implements the "deposit" subcommand by calling the client class.'''
    keyfile = _get_keyfile(args.placeName)

    client = ShipmentClient(baseUrl=DEFAULT_URL, keyFile=keyfile)

    response = client.add_item(args.shipmentID, args.N, args.items,args.placeName)

    # print("Response: {}".format(response))
    print("Add operation completed")

def do_remove(args):
    '''Implements the "withdraw" subcommand by calling the client class.'''
    keyfile = _get_keyfile(args.placeName)

    client = ShipmentClient(baseUrl=DEFAULT_URL, keyFile=keyfile)

    response = client.remove_item(args.shipmentID, args.N, args.items)

    print("Remove operation completed")
    # print("Response: {}".format(response))

def do_getcount(args):
    '''Implements the "balance" subcommand by calling the client class.'''
    keyfile = _get_keyfile(args.placeName)

    client = ShipmentClient(baseUrl=DEFAULT_URL, keyFile=keyfile)

    data = client.get_data()
    # ans = 0
    # print(data[args.itemName])
    # print(data,type(data))

    ans = 0
    for shipmentID,info in data.items():
        for item,count in info.items():
            if(item==args.itemName):
                ans += count
    print("No of items of type {} is {}".format(args.itemName,ans))

def do_transfer(args):
    '''Implements the "transfer" subcommand by calling the client class.'''
    keyfileFrom = _get_keyfile(args.placeFrom)
    keyfileTo = _get_pubkeyfile(args.placeTo)
    clientFrom = ShipmentClient(baseUrl=DEFAULT_URL, keyFile=keyfileFrom)
    response = clientFrom.transfer(args.shipmentID,args.placeTo,keyfileTo)
    # print("Response: {}".format(response))
    print("Transfer completed")

def do_getpath(args):
    keyfile = _get_keyfile(args.placeName)
    client = ShipmentClient(baseUrl=DEFAULT_URL, keyFile=keyfile)
    data = client.get_data()
    # print(data)
    if args.shipmentID in data:
        print("Path of the shipment {} is {}".format(args.shipmentID, data[args.shipmentID]['path']))
    else:
        print("Shipment is not found at the mentioned place")


def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    '''Entry point function for the client CLI.'''
    if args is None:
        args = sys.argv[1:]
    parser = create_parser(prog_name)
    args = parser.parse_args(args)
    verbose_level = 0
    setup_loggers(verbose_level=verbose_level)

    if args.command == 'add':
        do_add(args)
    elif args.command == 'remove':
        do_remove(args)
    elif args.command == 'getcount':
        do_getcount(args)
    elif args.command == 'transfer':
        if args.placeFrom == args.placeTo:
            raise Exception("Cannot transfer item to self: {}"
                                        .format(args.placeFrom))
        do_transfer(args)
    elif args.command == 'path':
        do_getpath(args)
    else:
        raise Exception("Invalid command: {}".format(args.command))


def main_wrapper():
    try:
        main()
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)