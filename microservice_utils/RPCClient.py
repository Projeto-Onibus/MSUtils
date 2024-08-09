import uuid
import pika
import json

import logging 
from .Logger import MSLogger 

class RPCClient(object):
    

    def __init__(self,host='localhost',logger=None):
        
        # Defaults to normal 
        if not logger:
            logger = logging.Logger()
            logger.setLevel(logging.DEBUG)

        self.logger = logger
        if type(self.logger) is MSLogger:
            self.logger.SetTransactionId("000000000000")

        self.logger.info("Initializing client")

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
        self.timeout = 120 # Default timeout value

        self.logger.info(f"Client initialized")
        self.logger.debug(f"Callback queue set as '{self.callback_queue}'")

    def __del__(self):
        
        if type(self.logger) is MSLogger:
            self.logger.SetTransactionId("FFFFFFFFFFFF")
        
        self.logger.info("Exiting client")

        self.channel.basic_cancel(self.callback_queue)
        self.channel.close()
        self.connection.close()

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            # receives the correct message
            self.response = json.loads(body.decode('UTF-8'))

    def MakeCall(self, name, n):
        """
        Makes a call for the broker.

        This function should be used by servers acting as client only. It assumes that there's a current transaction id set and fails otherwise.

        Clients should use the StartTransaction function that manages the transaction id seamless.
        """
        self.response = None
        self.corr_id = str(uuid.uuid4())
        
        self.channel.basic_publish(
            exchange='',
            routing_key=name,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(n))
        
        while self.response == None:
            self.connection.process_data_events(time_limit=None)

        return self.response.copy()
    
    def StartTransaction(self,name,n):
        """
        Starts a new transaction in the MS environment.
        
        This function should be used by clients only. It works as an encapsulation of the MakeCall function in order to manage the transaction id. 
        
        Servers wanting to interact as clients should use the MakeCall directly.
        """

        # Uma nova transação deve ter um novo ID 
        # Apenas verifica se uma transação antiga estava salva no logger
        
        if type(self.logger) is MSLogger:
            self.logger.NewTransaction()
            n['transaction_id'] = self.logger.GetTransactionId()
            n['transaction_counter'] = self.logger.GetTransactionCounter()
        else:
            n['transaction_id'] = str(uuid.uuid4())[-12]
            n['transaction_counter'] = 0

        # Sends the message
        self.logger.debug(f"Making call")
        results = self.MakeCall(name,n)
        self.logger.debug(f"Result: {results}")
        # Checks if response has required fields: transaction_id, transaction_counter and status_code
        if not 'transaction_counter' in results.keys():
            self.logger.critical("No transaction_counter in response")
            self.logger.debug(f"keys in response: {self.response.keys()}")
            raise Exception("Malformed server response on transaction_counter")
        if not 'transaction_id' in results.keys():
            self.logger.critical("No transaction id on response")
            self.logger.debug(f"keys in response: {self.response.keys()}")
            raise Exception("Malformed server response on transaction_id")
        if not 'status_code' in results.keys():
            self.logger.critical("No status_code in response")
            self.logger.debug(f"keys in response: {self.response.keys()}")
            raise Exception("Malformed server response on status_code")

        if type(self.logger) is MSLogger:
            if self.logger.GetTransactionId() != results['transaction_id']:
                self.logger.critical("Response from another transaction")
                self.logger.debug(f"mismatched ids: [{self.logger.GetTransactionId()}] sent <-> received [{results['transaction_id']}]")
                raise Exception("Returned transaction_id is different from when the request was made")
            self.logger.SetTransactionCounter(results['transaction_counter'])     
        else:
            if n['transaction_id'] != results['transaction_id']:
                self.logger.critical("Response from another transaction")
                self.logger.debug(f"mismatched ids: [{n['transaction_id']}] sent <-> received [{results['transaction_id']}]")
                raise Exception("Returned transaction_id is different from when the request was made")

        return results
