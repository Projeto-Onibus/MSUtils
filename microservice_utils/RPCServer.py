import json
import uuid
import logging 

import pika

from .AppException import AppException
from .RPCClient import RPCClient
from .Logger import MSLogger

class RPCServer:
    def __init__(self,host="localhost",logger=None):

        if not logger or type(logger) != MSLogger:
            raise Exception("MSLogger object must be passed")
        
        self.logger = logger

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host))

        self.channel = self.connection.channel()
        
        self.client = RPCClient(host=host,logger=logger)

    def AddMethod(self,name,method):
        RPCMethod = RPCCall(name,self.logger,self.client,method) 
        CreateRPC(self.channel, name, RPCMethod)
    
    def Start(self):
        self.channel.start_consuming()


def RPCCall(name,logger,client,func):
    """
    Function to create a server response.
    """
    def on_call(ch, method, props, body):

        # Verifies for invalid data before passing arguments to function
        invalidData = False
        
        # Defines default value for transaction ID in logs
        logger.SetTransactionId(-1) 

        # Try to convert the message's body as JSON, 
        try:
            parameters = json.loads(body.decode('UTF-8'))
        except Exception as err:
            response = {
                    'status-code':400,
                    "message":"Invalid JSON message",
                    "python-exception-type":type(err).__name__,
                    "python-exception-message":str(err)
            }
            invalidData = True
            logger.error(f"Failed to convert data to JSON. Bad request from '{props.reply_to}'")
       
        # Process transaction id 
        if not 'transaction_id' in parameters.keys():
            response = {
                'status-code':400,
                'message':"No transaction id set"
            }
            invalidData = True
            logger.error(f"No transaction id was set by the request. Bad request from '{props.reply_to}'")
        
        if not invalidData:
            logger.SetTransactionId(parameters['transaction_id'])
            del parameters['transaction_id']

            logger.debug("Valid request. Start processing.")

            # Apply the function
            try:
                response = func(parameters,logger=logger,client=client)
                logger.debug("Function end")

            # Error given by function
            except AppException as err:
                logger.debug("App Exception")
                response = {
                        'status-code': err.statusCode,
                        "message": err.message
                }

            # Any other Error
            except Exception as err:
                logger.debug("Other exception")
                response = {
                    "status-code":502,
                    "python-exception-type":type(err).__name__,
                    "python-exception-message":str(err)
                } 
            response['status-code'] = 200
            response['transaction_id'] = logger.GetTransactionId()

        # Define response
        ch.basic_publish(exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id = \
                    props.correlation_id),
            body=json.dumps(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
        logger.EndTransaction()

    return on_call

def CreateRPC(channel, name, functionHandler):
    channel.queue_declare(queue=name)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=name,on_message_callback=functionHandler)


def InitiateMethods(channel,methodList):
    for item in methodList:
        logger.debug(f"Initiating method {item['name']}")
        CreateRPC(channel, item['name'], item['method'])
