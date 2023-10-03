#
# Logger.py 
# Author: Fernando Dias
#
# Description: This module adds new functionality to the logger object. 
# 
# 
import uuid
import logging
from multiprocessing import Queue

import logging_loki

class MSLogger:
    """
    This class adds extra functionality for the logging's Logger class in order to better function in the MS environment set for FAS-Bus.

    This class adds two main functionalities: Transaction ids and counters.

    The transaction id is an identifier that tags along every log message in order to aggregate messages that came from a single transaction.

    """
    def __init__(self, loggerName=None, host='localhost',port=80, tags={}):
        
        if not loggerName:
            raise Exception("MSLogger must be declared as MSLogger(__name__)")
        
        self.logger = logging.getLogger(loggerName)
        self.transactionId = ""
        
        fh = logging_loki.LokiQueueHandler(
                Queue(-1),
                url=f"http://{host}:{port}/loki/api/v1/push",
                tags=tags,
                version="1"
        )
        
        fh_formatter = logging.Formatter('%(message)s')
        fh.setFormatter(fh_formatter)
        self.logger.addHandler(fh)
        
        self.counter = 0

    # Transaction Id 
    def NewTransaction(self):
        self.transactionId = str(uuid.uuid4())

    def SetTransactionId(self,newId):
        self.transactionId = str(newId)
   
    def GetTransactionId(self):
        return self.transactionId

    def EndTransaction(self):
        self.transactionId = ""
    
    def HasTransactionId(self):
        return len(self.transactionId)>0

    def ResetGlobalCounter(self):
        self.globalCounter = 0

    def GetGlobalCounter(self):
        return self.globalCounter

    def SetGo

    # Logs
    def debug(self,message):
        self.logger.debug(f"[{self.transactionId}]#{self.counter}:" + message)
        self.counter += 1

    def info(self,message):
        self.logger.info(f"[{self.transactionId}]#{self.counter}:" + message)
        self.counter += 1

    def warning(self,message):
        self.logger.warning(f"[{self.transactionId}]#{self.counter}:" + message)
        self.counter += 1

    def error(self,message):
        self.logger.error(f"[{self.transactionId}]#{self.counter}:" + message)
        self.counter += 1

    def critical(self,message):
        self.logger.critical(f"[{self.transactionId}]#{self.counter}:" + message)
        self.counter += 1

    def setLevel(self,logLevel):
        self.logger.setLevel(logLevel)

