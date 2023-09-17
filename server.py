import time 
import json
import pika

from MSUtils.RPCDecorator import RPCCall, InitiateMethods
from MSUtils.AppException import AppException

methodList = []

@RPCCall(methodList,"test_queue")
def testQueue(obj):
    obj['test'] += 30
    obj['response'] = "yes"
    time.sleep(1)
    return obj


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

InitiateMethods(channel,methodList)

channel.start_consuming()
