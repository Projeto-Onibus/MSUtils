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
        self.logger = logger

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host))

        self.channel = self.connection.channel()
        
        self.client = RPCClient(host=host,logger=logger)
        
        self.cache = cache 

    def AddMethod(self,name,method):
        RPCMethod = RPCCall(name,method, self.logger,self,self.cache) 
        CreateRPC(self.channel, name, RPCMethod)
    
    def Start(self):
        self.channel.start_consuming()

    def MakeCall(self, name, parameters):
        """
        Makes call from the server
        """
        # Add transaction parameters 
        parameters['transaction_id'] = self.logger.GetTransactionId()
        parameters['transaction_counter'] = self.logger.GetTransactionCounter()

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
        
        # Adds exception if 
        if response['status_code'] != 200:
            logger.error("Received error from service")
            if 'error_message' in response.keys():
                logger.error(f"Error message: {response['error_message']}")

        del response['transaction_id']
        del response['transaction_counter']
        
        return response

def RPCCall(name:str, func, logger: MSLogger, client:RPCClient, cache:RPCCache):
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
            
            response = SetTransactionParameters(response)
            
        except Exception as err:
            logger.error("Caught exception from the server's callback function")
            logger.LogException(err)
            response = {
                'status_code':502,
                'error_message':"Internal server error"
            }

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
        response['transaction_id'] = logger.GetTransactionId()
        response['transaction_counter'] = logger.GetTransactionCounter()
        return response 

    return on_call

def CreateRPC(channel, name, functionHandler):
    channel.queue_declare(queue=name)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=name,on_message_callback=functionHandler,auto_ack=True)


def InitiateMethods(channel,methodList):
    for item in methodList:
        logger.debug(f"Initiating method {item['name']}")
        CreateRPC(channel, item['name'], item['method'])
