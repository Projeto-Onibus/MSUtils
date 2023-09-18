import json
import uuid

import pika

from .AppException import AppException
from .Logger import CreateLogger


def RPCCall(methodList, name):

    def RPCCallFunction(func):
        def on_call(ch, method, props, body):

            response = {
                "status-code":502,
                "message": "Nothing was processed."
            }
            
            invalidData = False
            # Try to convert the message's body as JSON, 
            try:
                kwargs = json.loads(body.decode('UTF-8'))
            except Exception as err:
                response = {
                        'status-code':400,
                        "message":"Invalid JSON message",
                        "python-exception-type":type(err).__name__,
                        "python-exception-message":str(err)
                }
                invalidData = True
                logger.warning("Failed to convert data to JSON")
            
            if not invalidData:
                logger.debug("Valid data, trying to process")
                # Apply the function
                try:
                    response = func(kwargs)
                    logger.debug("Data processed")
                # Error given by function
                except AppException as err:
                    logger.debug("App Exception")
                    response = {
                            'status-code':err.statusCode,
                            "message":err.message
                    }
                # Any other Error
                except Exception as err:
                    logger.debug("Other exception")
                    response = {
                            "status-code":"502",
                            "message":err.message,
                            "python-exception-type":type(err).__name__
                    } 
            logger.debug("Sending message")
            # Define response
            ch.basic_publish(exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id = \
                        props.correlation_id),
                body=json.dumps(response))
            ch.basic_ack(delivery_tag=method.delivery_tag)

        methodList.append({'name':name,'method':on_call})
        return on_call
    return RPCCallFunction


def CreateRPC(channel, name, functionHandler):
    channel.queue_declare(queue=name)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=name,on_message_callback=functionHandler)


def InitiateMethods(channel,methodList):
    for item in methodList:
        logger.debug(f"Initiating method {item['name']}")
        CreateRPC(channel, item['name'], item['method'])
