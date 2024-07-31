import json
import uuid
import logging 

import pika

from .AppException import AppException
from .RPCClient import RPCClient
from .Logger import MSLogger

class RPCServer:
    def __init__(self,host="localhost",logger,cache=None):

        self.logger = logger

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host))

        self.channel = self.connection.channel()
        
        self.client = RPCClient(host=host,logger=logger)
        
        self.cache = cache 

    def AddMethod(self,name,method):
        RPCMethod = RPCCall(name,self.logger,self.client,self.cache,method) 
        CreateRPC(self.channel, name, RPCMethod)
    
    def Start(self):
        self.channel.start_consuming()


def RPCCall(name,logger,client,cache,func):
    """
    Function to create a server response.
    """
    def on_call(ch, method, props, body):

        # Verifies for invalid data before passing arguments to function
        invalidData = False
        
        # Defines default value for transaction ID in logs
        logger.SetTransactionId(-1) 

        requestData, response = ParseBodyToJSON(body)
        if response:
            return response

        functionParameters, response = ParseTransactionParameters(requestData)
        if response:
            return response

        response = GetResponseFromCache(functionParameters)


    def GetResponseFromCache(parameters):
        cacheKey =f'{name},{json.dumps(parameters)}'

        response = cache.get(key)
        if response:
            logger.debug(f"Cached result '{response}'")
            response = json.loads(response)
            response['status-code'] = 200
        
        return response

    def GenerateResponse(parameters):
        try:
            response = func(parameters,logger=logger,client=client)
            if cache:
            logger.debug("Function end")
        # Error given by function
        except ClientException as err:
            logger.debug("Client exception")
            response = {
                    'status-code': 400,
                    "error-message": err.message
            }
        # Any other Error
        except Exception as err:
            logger.debug("Other exception")
            response = {
                "status-code":502,
                "error-message":"Internal server error",
                "python-exception-type":type(err).__name__,
                "python-exception-message":str(err)
            } 
        response['status-code'] = 200
        response['transaction_id'] = logger.GetTransactionId()
        response['transaction_counter'] = logger.GetTransactionCounter()

        # Define response
        ch.basic_publish(exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id = \
                    props.correlation_id),
            body=json.dumps(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
        logger.EndTransaction()


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
                    'status-code':400,
                    "error-message":"Invalid JSON message",
                    "python-exception-type":type(err).__name__,
                    "python-exception-message":str(err)
            }
            logger.error(f"Failed to convert data to JSON. Bad request from '{props.reply_to}'")
             
        return parameters, response 

    def ParseTransactionParameters(parameters): 
        """
        Parses the transaction data inside request.
        """
        if not 'transaction_id' in parameters.keys() or not 'transaction_counter' in parameters.keys():
            response = {
                'status-code':400,
                'error-message':"No transaction id or counter set"
            }
            logger.error(f"No transaction id was set by the request. Bad request from '{props.reply_to}'")
        
        logger.SetTransactionId(parameters['transaction_id'])
        logger.SetTransactionCounter(parameters['transaction_counter'])

        del parameters['transaction_id']
        del parameters['transaction_counter']
        
        return parameters, response 
            
    return on_call

def CreateRPC(channel, name, functionHandler):
    channel.queue_declare(queue=name)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=name,on_message_callback=functionHandler)


def InitiateMethods(channel,methodList):
    for item in methodList:
        logger.debug(f"Initiating method {item['name']}")
        CreateRPC(channel, item['name'], item['method'])
