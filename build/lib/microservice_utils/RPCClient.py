import uuid
import pika
import json

from .Logger import MSLogger

class RPCClient(object):
    

    def __init__(self,host='localhost',logger=None):
        
        if not logger or type(logger) != MSLogger:
            raise Exception("MSLogger class must be passed")
        
        self.logger = logger
        # Remove any previous transactions when creating client
        self.logger.EndTransaction()

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

        self.logger.info(f"Client initialized. Callback queue set as '{self.callback_queue}'")
        self.transactionLog = []

    def on_response(self, ch, method, props, body):
        self.logger.info("Got response!")

        if self.corr_id == props.correlation_id:
            # receives the correct message
            self.response = json.loads(body.decode('UTF-8'))
            
            # Assures that the transaction id is saved in the logger object
            if self.response['transaction_id'] != self.logger.GetTransactionId():
                self.logger.critical("Response from another transaction")
                raise Exception("Invalid transaction id for received process")

            # removes transaction id from answer
            del self.response['transaction_id']

    def MakeCall(self, name, n):
        """
        Makes a call for the broker.

        This function should be used by servers acting as client only. It assumes that there's a current transaction id set and fails otherwise.

        Clients should use the StartTransaction function that manages the transaction id seamless.
        """
        self.response = None
        self.corr_id = str(uuid.uuid4())
        
        if not self.logger.HasTransactionId():
            raise Exception("Cannot use MakeCall without transaction id")
        
        n['transaction_id'] = self.logger.GetTransactionId()

        self.channel.basic_publish(
            exchange='',
            routing_key=name,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(n))

        self.connection.process_data_events(time_limit=self.timeout)
        
        if not self.response:
            raise Exception("No response from broker")
        
        return self.response.copy()
    
    def StartTransaction(self,name,n):
        """
        Starts a new transaction in the MS environment.
        
        This function should be used by clients only. It works as an encapsulation of the MakeCall function in order to manage the transaction id. 
        
        Servers wanting to interact as clients should use the MakeCall directly.
        """

        # Uma nova transação deve ter um novo ID 
        # Apenas verifica se uma transação antiga estava salva no logger
        hasTransactionId = False
        if self.logger.HasTransactionId():
            hasTransactionId = True
            oldTransactionId = self.logger.transactionId
        
        # Creates a new transaction id before warning of overwrite with previous transaction
        self.logger.NewTransaction()
        if hasTransactionId:
            self.logger.warning(f"Started from previously unresolved transaction: [{oldTransactionId}]")
        self.logger.info(f"Started new transaction of type '{name}'")

        executionFailed = False
        try:
            results = self.MakeCall(name,n)
        except Exception as err:
            executionFailed = True
            exceptionRaised = err
        finally:
            # Finalizes the transaction before raising the exception
            self.transactionLog.append(self.logger.GetTransactionId())
            self.logger.EndTransaction()
        
        if executionFailed:
            raise exceptionRaised

        return results
