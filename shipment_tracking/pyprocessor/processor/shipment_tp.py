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
Transaction family class for shipment.
'''

import traceback
import sys
import hashlib
import logging
import pickle

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_sdk.processor.core import TransactionProcessor

LOGGER = logging.getLogger(__name__)

FAMILY_NAME = "shipment"

def _hash(data):
    '''Compute the SHA-512 hash and return the result as hex characters.'''
    return hashlib.sha512(data).hexdigest()

# Prefix for simplewallet is the first six hex digits of SHA-512(TF name).
sw_namespace = _hash(FAMILY_NAME.encode('utf-8'))[0:6]

class ShipmentTransactionHandler(TransactionHandler):
    '''                                                       
    Transaction Processor class for the shipment transaction family.       
                                                              
    This with the validator using the accept/get/set functions.
    It implements functions to deposit, withdraw, and transfer money.
    '''

    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return FAMILY_NAME

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def namespaces(self):
        return [self._namespace_prefix]

    def apply(self, transaction, context):
        '''This implements the apply function for this transaction handler.
                                                              
           This function does most of the work for this class by processing
           a single transaction for the simplewallet transaction family.   
        '''                                                   
        
        # Get the payload and extract simplewallet-specific information.
        header = transaction.header
        payload_list = transaction.payload.decode().split(",")
        operation = payload_list[0]
        # amount = payload_list[1]

        # Get the public key sent from the client.
        from_key = header.signer_public_key

        # Perform the operation.
        LOGGER.info("Operation = "+ operation)

        if operation == "add":
            # print(len(payload_list))
            # for x in payload_list:
            shipmentID = payload_list[1]
            N = int(payload_list[2])
            items = []
            print((payload_list[3][2:-1]))
            items.append(payload_list[3][2:-1])
            for i in range(1,2*N-1):
                items.append(payload_list[i+3][2:-1])
            items.append(payload_list[3+2*N-1][2:-2])
            print(items)
            place= payload_list[2*N+3]
            print(place,type(place))
            # count = payload_list[2]
            self._make_add(context, shipmentID, N,items,place,from_key)

        elif operation == "remove":
            shipmentID = payload_list[1]
            N = int(payload_list[2])
            items = []
            print((payload_list[3][2:-1]))
            items.append(payload_list[3][2:-1])
            for i in range(1,2*N-1):
                items.append(payload_list[i+3][2:-1])
            items.append(payload_list[3+2*N-1][2:-2])
            print(items)
            self._make_remove(context, shipmentID, N,items, from_key)

        elif operation == "transfer":
            print(len(payload_list),"HOORAY")
            if len(payload_list) == 4:
                shipmentID = payload_list[1]
                placeTo = payload_list[2]
                to_key = payload_list[3]
            self._make_transfer(context, shipmentID,placeTo, to_key, from_key)

        else:
            LOGGER.info("Unhandled action. " +
                "Operation should be deposit, withdraw or transfer")

    def _make_add(self, context, shipmentID, N,items,place,from_key):
        wallet_address = self._get_wallet_address(from_key)
        LOGGER.info('Got the key {} and the wallet address {} '.format(
            from_key, wallet_address))
        current_state = context.get_state([wallet_address])
        new_state = {}
        if current_state == []:
            LOGGER.info('No previous deposits, creating new deposit {} '
                .format(from_key))
            new_state[shipmentID]={}
            new_state[shipmentID]['path']=place
            N = int(N)
            for x in range(0,2*N,2):
                    new_state[shipmentID][items[x]]=int(items[x+1])
        else:
            new_state = pickle.loads(current_state[0].data)
            if shipmentID in new_state:
                for x in range(0,2*N,2):
                    if items[x] in  new_state[shipmentID]:
                        new_state[shipmentID][items[x]]+=int(items[x+1])
                    else:
                        new_state[shipmentID][items[x]]=int(items[x+1])
            else:
                new_state[shipmentID]={}
                new_state[shipmentID]['path']=place
                for x in range(0,2*N,2):
                    new_state[shipmentID][items[x]]=int(items[x+1])
        print(new_state)
        state_data = pickle.dumps(new_state)
        addresses = context.set_state({wallet_address: state_data})

        if len(addresses) < 1:
            raise InternalError("State Error")

    def _make_remove(self, context,shipmentID, N,items, from_key):
        wallet_address = self._get_wallet_address(from_key)
        LOGGER.info('Got the key {} and the wallet address {} '.format(
            from_key, wallet_address))
        current_state = context.get_state([wallet_address])
        new_state = {}
        
        if current_state == []:
            LOGGER.info('No user with the key {} '.format(from_key))
            return
        else:
            old_state = pickle.loads(current_state[0].data)
            if shipmentID in old_state:
                flag = True
                for x in range(0,2*N,2):
                    if(items[x] not in old_state[shipmentID] or  old_state[shipmentID][items[x]]<int(items[x+1])):
                        flag = False
                        break
                if flag:
                    for x in range(0,2*N,2):
                        old_state[shipmentID][items[x]]-=int(items[x+1])
                else:
                    LOGGER.info('Remove failed since one of the items mentioned has low balance than given')
            
            else:
                LOGGER.info('Remove failed shipment ID not found')
            new_state = old_state
        print(new_state)
        state_data = pickle.dumps(new_state)
        addresses = context.set_state({wallet_address: state_data})

        if len(addresses) < 1:
            raise InternalError("State Error")

    def _make_transfer(self, context, shipmentID, placeTo, to_key, from_key):
        wallet_address = self._get_wallet_address(from_key)
        wallet_to_address = self._get_wallet_address(to_key)
        LOGGER.info('Got the from key {} and the from wallet address {} '.format(
            from_key, wallet_address))
        LOGGER.info('Got the to key {} and the to wallet address {} '.format(
            to_key, wallet_to_address))
        current_state = context.get_state([wallet_address])
        current_state_to = context.get_state([wallet_to_address])
        if current_state == []:
            LOGGER.info('No user (debtor) with the key {} '.format(from_key))
            return
        print(current_state,current_state_to)
        new_state = pickle.loads(current_state[0].data)
        new_state_to={}
        if current_state_to != []:
            new_state_to = pickle.loads(current_state_to[0].data)

        if shipmentID in new_state:
            tmp = new_state[shipmentID]
            tmp['path']= tmp['path']+"->"+placeTo
            new_state.pop(shipmentID)
            new_state_to[shipmentID]=tmp
        else:
            LOGGER.info('Shipment ID is not present')
        print(new_state)
        print(new_state_to)
        state_data = pickle.dumps(new_state)
        context.set_state({wallet_address: state_data})
        state_data_to = pickle.dumps(new_state_to)
        context.set_state({wallet_to_address: state_data_to})

    def _get_wallet_address(self, from_key):
        return _hash(FAMILY_NAME.encode('utf-8'))[0:6] + _hash(from_key.encode('utf-8'))[0:64]

def setup_loggers():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

def main():
    '''Entry-point function for the shipment transaction processor.'''
    setup_loggers()
    try:
        # Register the transaction handler and start it.
        processor = TransactionProcessor(url='tcp://validator:4004')

        handler = ShipmentTransactionHandler(sw_namespace)

        processor.add_handler(handler)

        processor.start()

    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)