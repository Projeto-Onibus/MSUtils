import sys
import logging
sys.path.append('..')

from MicroServiceUtils.RPCServer import RPCServer
from MicroServiceUtils.Logger import MSLogger

logger = MSLogger("sum_values",host='localhost',port=3100)
logger.setLevel(logging.DEBUG)

# Function definitions
def SumValues(parameters,logger,client):
    result = {}
    
    logger.info("Inside function defined")

    # Parameters is always dict as json object
    for key in parameters.keys():
        result[key] = sum(parameters[key])
    
    return result

server = RPCServer(host='localhost',logger=logger)

server.AddMethod('sum_values',SumValues)

server.Start()
