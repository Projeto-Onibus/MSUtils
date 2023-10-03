import sys
import logging
sys.path.append('..')

from MicroServiceUtils.RPCServer import RPCServer
from MicroServiceUtils.Logger import MSLogger

logger = MSLogger("get_diagonals",host='localhost',port=3100)
logger.setLevel(logging.DEBUG)

# Function definitions
def GetDiagonals(parameters,logger,client):
    result = {}
    
    logger.info("Inside function defined")

    # Parameters is always dict as json object
    for key in parameters.keys():
        result[key] = []
        for index in range(len(parameters[key])):
            result[key].append(parameters[key][index][index])
    
    # Makes a call for another RPC
    return client.MakeCall('sum_values',result)



server = RPCServer(host='localhost',logger=logger)

server.AddMethod('get_diagonal',GetDiagonals)

server.Start()
