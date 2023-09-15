from .AppException import AppException

def CreateRPC(func):

    def RPCCall(ch, method, props, body):
    
        # Try to convert the message's body as JSON, 
        try:
            kwargs = json.loads(body.decode('UTF-8'))
        except Exception as err:
            response = {
                    'status-code':400,
                    "message":"Invalid JSON message"
            }

        try:
            reponse = func(kwargs)
        except AppException as err:
            response = {
                    'status-code':err.statusCode,
                    "message":err.message
            }
        except Exception as err:
            response = {
                    "status-code":"502",
                    "message":err.message,
                    "python-exception-type":type(err).__name__
            }

        ch.basic_publish(exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id = \
                    props.correlation_id),
            body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)
    return RPCCall

