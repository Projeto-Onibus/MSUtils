#!/usr/bin/env python
import pika
import uuid

import json

class FibonacciRpcClient(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='test_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(n))
        self.connection.process_data_events(time_limit=20)
        if not self.response:
            return -1
        return self.response


fibonacci_rpc = FibonacciRpcClient()

print(" [x] Requesting fib(30)")
response = fibonacci_rpc.call({"test":80,"name":"value"})
print(f" [.] Got {json.loads(response)}")
response = fibonacci_rpc.call({"test":70,"name":"value2"})
print(f" [.] Got {json.loads(response)}")
response = fibonacci_rpc.call({"test":60,"name":"value3"})
print(f" [.] Got {json.loads(response)}")
response = fibonacci_rpc.call({"test":0,"name":"valu4e"})
print(f" [.] Got {json.loads(response)}")
