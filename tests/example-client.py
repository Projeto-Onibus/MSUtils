import sys
import time 
import uuid
sys.path.append('..')

import logging

# 
# Set-up phase 
# 

# Import libraries
from microservice_utils.RPCClient import RPCClient
from microservice_utils.RPCCache import RPCCache
from microservice_utils.Logger import MSLogger

# Start logger to log data in loki server
logger = MSLogger("client",host='localhost',port=3100)
cache = RPCCache(host='localhost',port=6379)
logger.setLevel(logging.DEBUG)

#
# Main usage
# 

logger.info("Starting client example")

# Start a client object
client = RPCClient(host='localhost',logger=logger)

# Create parameters to send in request
# Dict must be JSONfiable
parameters = {"matrix":[
    [1,2,3],
    [4,5,6],
    [7,8,9]
]}

for i in range(5):
    # Make a request
    logger.info("Making call")
    result = client.StartTransaction("sum_diagonal",parameters)
    logger.info("Received result")

    # Get results
    print('results',result)
