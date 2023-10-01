from .RPCDecorator import CreateRPC, RPCCall

class RPCServer:
    def __init__(self,host="localhost"):
    
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()
        
    def AddMethod(self,name,method):
        RPCMethod = RPCCall(name)(method) 
        CreateRPC(self.channel, name, RPCMethod)
    
    def Start(self):
        self.channel.start_consuming()

