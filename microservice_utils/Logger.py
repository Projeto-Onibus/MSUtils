#
# Logger.py 
# Author: Fernando Dias
#
# Description: This module adds new functionality to the logger object. 
# 
# 
import uuid
import logging
import requests
import traceback
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
        self.post_url = f"http://{host}:{port}/loki/api/v1/push"
        fh = logging_loki.LokiQueueHandler(
                Queue(-1),
                url=self.post_url,
                tags=tags,
                version="1"
        )
        
        fh_formatter = logging.Formatter('%(message)s')
        fh.setFormatter(fh_formatter)
        self.logger.addHandler(fh)
        self.tags = {} 
        self.transactionCounter = 0

    # Transaction Id 
    def NewTransaction(self):
        self.transactionId = str(uuid.uuid4())[-12:]
        self.ResetTransactionCounter()

    def SetTransactionId(self,newId):
        self.transactionId = str(newId)
   
    def GetTransactionId(self):
        return self.transactionId

    def EndTransaction(self):
        self.transactionId = ""

    def HasTransactionId(self):
        return len(self.transactionId)>0

    def ResetTransactionCounter(self):
        self.transactionCounter = 0

    def GetTransactionCounter(self):
        return self.transactionCounter

    def SetTransactionCounter(self,value):
        self.transactionCounter = value 

    def LogException(self, exception, status='error'):
        self.error(f"({0:03d}) Exception caught during execution")
        self.error(f"({1:03d}) Exception {exception}")
        if exception.__traceback__:
            for idx, tracebackItem in enumerate(traceback.format_list(traceback.extract_tb(exception.__traceback__))):
                self.error(f"({2+idx:03d}) Traceback {traceback.format_exception(exception)[idx]}")

    # Logs
    def debug(self,message):
        self.logger.debug(f"[{self.transactionId}]#{self.transactionCounter}:" + message,extra=self.tags)
        self.transactionCounter += 1

    def info(self,message):
        self.logger.info(f"[{self.transactionId}]#{self.transactionCounter}:" + message,extra=self.tags)
        self.transactionCounter += 1

    def warning(self,message):
        self.logger.warning(f"[{self.transactionId}]#{self.transactionCounter}:" + message,extra=self.tags)
        self.transactionCounter += 1

    def error(self,message):
        self.logger.error(f"[{self.transactionId}]#{self.transactionCounter}:" + message,extra=self.tags)
        self.transactionCounter += 1

    def critical(self,message):
        self.logger.critical(f"[{self.transactionId}]#{self.transactionCounter}:" + message,extra=self.tags)
        self.transactionCounter += 1

    def setLevel(self,logLevel):
        self.logger.setLevel(logLevel)

