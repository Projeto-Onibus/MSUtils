import pika

from .RPCDecorator import CreateRPC, RPCCall
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
        RPCMethod = RPCCall(name,self.logger,self.client)(method) 
        CreateRPC(self.channel, name, RPCMethod)
    
    def Start(self):
        self.channel.start_consuming()

