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
        RPCMethod = RPCCall(name,method, self.logger,self.client,self.cache) 
        CreateRPC(self.channel, name, RPCMethod)
    
    def Start(self):
        self.channel.start_consuming()


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

        requestData, response = ParseBodyToJSON(body)

        if not response:
            functionParameters, response = ParseTransactionParameters(requestData)

        # No logs before this
        logger.info('Received request')

        fromCache = False 
        if not response:
            fromCache = True 
            response = GetResponseFromCache(functionParameters)
            logger.info('Cached response')

        if not response:
            response = ApplyFunction(functionParameters)
            
        if response['status-code']==200 and not fromCache:
            SetCache(parameters,response)
        
        response = SetTransactionParameters(response)
        
        # No logs after this

        try:
            PublishResponse(response)
        except Exception as err:
            logger.critical("Unable to send response due to unkonwn error")
            logger.critical(f"{err}")

        logger.EndTransaction()

    def GetResponseFromCache(parameters):
        response = None
        if cache: 
            response = cache.GetResult(name,parameters)
            if response:
                logger.info(f"Cached result '{response}'")
                response['status-code'] = 200
        
        return response

    def SetCache(parameters,response):
        if cache: 
            cache.SetResult(name,parameters,response) 

    def ApplyFunction(parameters):
        try:
            logger.debug("Function start")
            response = func(parameters,logger=logger,client=client)
            logger.debug("Function end")
            response['status-code'] = 200
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
        return response 

    def PublishResponse(response):
        # Define response
        ch.basic_publish(exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id = \
                    props.correlation_id),
            body=json.dumps(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)


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

        return parameters, response 

    def ParseTransactionParameters(parameters): 
        """
        Parses the transaction data inside request.
        """
        response=None
        try: 
            if not 'transaction_id' in parameters.keys() or not 'transaction_counter' in parameters.keys():
                response = {
                    'status-code':400,
                    'error-message':"No transaction id or counter set"
                }
        
            logger.SetTransactionId(parameters['transaction_id'])
            logger.SetTransactionCounter(parameters['transaction_counter'])
        
            del parameters['transaction_id']
            del parameters['transaction_counter']
        except Exception as err:
            response = {'status-code':502,
                        'error-message': "Unexpected error",
                        'python-error-message':f"{err}"
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
    channel.basic_consume(queue=name,on_message_callback=functionHandler)


def InitiateMethods(channel,methodList):
    for item in methodList:
        logger.debug(f"Initiating method {item['name']}")
        CreateRPC(channel, item['name'], item['method'])
