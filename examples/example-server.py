import sys
import logging
sys.path.append('..')

# Import Server utils and Logger utils
from MicroServiceUtils.RPCServer import RPCServer
from MicroServiceUtils.Logger import MSLogger

# Create a logger that indicates the name of the MS
logger = MSLogger("get_diagonals",host='localhost',port=3100)
logger.setLevel(logging.DEBUG)

# Define functions that are associated with services
def GetDiagonals(parameters,logger,client):
    result = {}
    
    # Log any relevant information as if it is using the pyhton's logging module
    logger.info("Inside function defined")

    # Parameters is always dict as json object
    for key in parameters.keys():
        result[key] = []
        for index in range(len(parameters[key])):
            result[key].append(parameters[key][index][index])
    
    # returns dict object that can be "JSONfied"
    return result

# Create a server object
server = RPCServer(host='localhost',logger=logger)

# Add its methods
server.AddMethod('get_diagonal',GetDiagonals)

# Starts the server
server.Start()
