import sys
import logging
sys.path.append('..')

# Import Server utils and Logger utils
from microservice_utils.RPCServer import RPCServer
from microservice_utils.Logger import MSLogger

# Create a logger that indicates the name of the MS
logger = MSLogger("sum_diagonal",host='localhost',port=3100)
logger.setLevel(logging.DEBUG)

def SumDiagonals(parameters,logger,client):
    result = {}
    
    # Log any relevant information as if it is using the pyhton's logging module
    logger.info("Inside function defined")

    # Makes a request to the 'sum_diagonal' MS 
    partials = client.MakeCall('get_diagonal',parameters)

    logger.info(f"Received data from MS: {partials.keys()}")

    # Parameters is always dict as json object
    for key in partials.keys():
        logger.info(f"Summing {partials[key]}")
        result[key] = sum(partials[key])
    
    logger.info("Summed data, returning")
    # returns dict object that can be "JSONfied"
    return result

# Create a server object
server = RPCServer(host='localhost',logger=logger)

# Add its methods
server.AddMethod('sum_diagonal',SumDiagonals)

# Starts the server
server.Start()
