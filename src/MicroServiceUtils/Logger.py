#
# Logger.py 
# Author: Fernando Dias
#
# Description: This module adds new functionality to the logger object. 
# 
# 
import logging
from multiprocessing import Queue

import logging_loki

class MSLogger:
    def __init__(self, host, tags):
        self.logger = logging.getLogger(name)
        self.transactionId = ""
        fh = logging_loki.LokiQueueHandler(
                Queue(-1),
                url=f"http://{host}/loki/api/v1/push",
                tags=tags,
                version="1"
        )
        fh_formatter = logging.Formatter('%(filename)s(%(lineno)d): %(message)s')
        fh.setFormatter(fh_formatter)
        self.logger.addHandler(fh)
    
    def SetTransactionId(self,newId):
        self.transactionId = str(newId)
    
    def debug(self,message):
        self.logger.debug(self.transactionId + message)
    
    def info(self,message):
        self.logger.info(self.transactionId + message)
    
    def warning(self,message):
        self.logger.warning(self.transactionId + message)

    def error(self,message):
        self.logger.error(self.transactionId + message)

    def critical(self,message):
        self.logger.critical(self.transactionId + message)

