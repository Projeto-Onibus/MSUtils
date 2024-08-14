import json
import uuid
import logging 

import pika

from .AppException import AppException, ClientException
from .RPCClient import RPCClient
from .Logger import MSLogger
from .RPCCache import RPCCache

class RPCServer:
    def __init__(self,host,logger:MSLogger,cache=None):
        """
        Initializes the server class. 
        Needs the host for the RabbitMQ server and an MSLogger class
        """
        # Receives a python logger 
        self.logger = logger

        # RabbitMQ server connection
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host))
        self.channel = self.connection.channel()

        # Redis cache initialization
        self.cache = cache 

    def _CreateConsumerRPC(self, name, functionHandler):
        """
        Internal function that creates an RPC consumer based on a queue name and a function handler for the current broker.
        """
        self.channel.queue_declare(queue=name)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=name,on_message_callback=functionHandler,auto_ack=True)

    def AddMethod(self,name,method):
        """
        Register the server to consume from the queue `name` and process the data with `method`.
        The method must receive a single JSON object as paramter (can validate with schema) and return a JSON object.
        """
        RPCMethod = CreateRPCCall(name,method, self.logger,self,self.cache) 
        self._CreateConsumerRPC(name, RPCMethod)
    
    def Start(self):
        """
        Initializes the server after all methods are declared. Stays on an infinite loop.
        """
        self.channel.start_consuming()

    def MakeRPCCall(self, name, parameters):
        """
        Makes an RPC call for another MS. It raises an exception based on the request
        """
        
        parameters = self.SetTransactionParameters(parameters)

        self.logger.debug(f"Requesting {name} with parameters {parameters}")

        # Make a call 
        response = self.client.MakeCall(name,parameters)
    
        if not 'transaction_counter' in response.keys():
            raise Exception("Malformed response from service")

        if parameters['transaction_id'] != response['transaction_id']:
            raise Exception("Invalid transaction id received from service")
            
        # Sets the new transaction counter
        self.logger.SetTransactionCounter(response['transaction_counter']+1)
        
        logger.debug('Received response')
        
        # Adds exception that returns the original message in status code
        if response['status_code'] != 200:
            logger.error("Received error from service")
            if 'error_message' in response.keys():
                logger.error(f"Error message: {response['error_message']}")

        del response['transaction_id']
        del response['transaction_counter']
        
        return response

def CreateRPCCall(name:str, func, logger: MSLogger, client:RPCClient, cache:RPCCache):
    """
    Function to create function handler to serve a query.
    Creates numerous auxiliary functions that use other classes defined in the function.
    Creates a 'on_call' function handler to pass to the RabbitMQ consumer method.
    """
    def on_call(ch, method, props, body):

        # Verifies for invalid data before passing arguments to function
        invalidData = False

        # Defines default value for transaction ID in logs
        logger.SetTransactionId("None") 
        
        try: 
            requestData, response = ParseBodyToJSON(body)

            if not response:
                functionParameters, response = ParseTransactionParameters(requestData)
            
            # No logs before this
            logger.info("Request successfuly received")
            logger.debug(f"Parameters sent: {functionParameters}")

            fromCache = False 
            response = GetResponseFromCache(functionParameters)
            if response:
                fromCache = True
                logger.info('Cached response')
            else:
                response = ApplyFunction(functionParameters)
                
            if response['status_code']==200 and not fromCache:
                SetCache(parameters,response)
            
        except Exception as err:
            logger.error("Caught exception from the server's callback function")
            logger.LogException(err)
            response = {
                'status_code':502,
                'error_message':"Internal server error"
            }

        response = SetTransactionParameters(response)

        try:
            ch.basic_publish(exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id = \
                        props.correlation_id),
                body=json.dumps(response))
        except Exception as err:
            logger.critical("Unable to send response through basic_publish")
            logger.LogException(err)

        logger.EndTransaction()

    def GetResponseFromCache(parameters):
        response = None
        if cache: 
            response = cache.GetResult(name,parameters)
            if response:
                logger.info(f"Cached result '{response}'")
                response['status_code'] = 200
        
        return response

    def SetCache(parameters,response):
        if cache: 
            cache.SetResult(name,parameters,response) 

    def ApplyFunction(parameters):
        if 'status_code' in parameters.keys():
            del parameters['status_code']
        try:
            logger.debug("Function start")
            response = func(parameters,logger=logger,client=client)
            logger.debug("Function end")
            response['status_code'] = 200
        # Error given by function
        except ClientException as err:
            logger.info("Caught client exception")
            response = {
                    'status_code': 400,
                    "error_message": err.message
            }
        return response 

    def ParseBodyToJSON(body):
        """
        Parses the body to JSON
        """
        response = None
        parameters = None
        try:
            parameters = json.loads(body.decode('UTF-8'))
        except Exception as err:
            response = {
                    'status_code':400,
                    "error_message":"Invalid JSON message",
                    "python_exception-type":type(err).__name__,
                    "python_exception-message":str(err)
            }

        return parameters, response 

    def ParseTransactionParameters(parameters): 
        """
        Parses the transaction data inside request.
        """
        response=None
        try: 
            if not 'transaction_id' in parameters.keys() or not 'transaction_counter' in parameters.keys():
                response = {
                    'status_code':400,
                    'error_message':"No transaction id or counter set"
                }
        
            logger.SetTransactionId(parameters['transaction_id'])
            logger.SetTransactionCounter(parameters['transaction_counter']+1)
        
            del parameters['transaction_id']
            del parameters['transaction_counter']

            if 'status_code' in parameters.keys():
                del parameters['status_code']

        except Exception as err:
            logger.error("Exception caught when parsing transaction parameters")
            logger.LogException(err)
            response = {'status_code':502,
                        'error_message': "Unexpected error",
                        'python_error_message':f"{err}"
            }

        return parameters, response 
    
    def SetTransactionParameters(response):
        """
        Function that writes the `transaction_id` and `transaction_counter` in a JSON object 
        """
        response['transaction_id'] = logger.GetTransactionId()
        response['transaction_counter'] = logger.GetTransactionCounter()
        return response 

    return on_call


