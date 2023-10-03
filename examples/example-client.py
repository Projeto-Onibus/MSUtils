import sys
import uuid
sys.path.append('..')

import logging

# 
# Set-up phase 
# 

# Import libraries
from MicroServiceUtils.RPCClient import RPCClient
from MicroServiceUtils.Logger import MSLogger

# Start logger to log data in loki server
logger = MSLogger("client",host='localhost',port=3100)

logger.setLevel(logging.DEBUG)
#
# Main usage
# 

logger.info("Starting client example")

# Start a client object
client = RPCClient(host='localhost',logger=logger)

# Create parameters
parameters = {"matrix":[
    [1,2,3],
    [4,5,6],
    [7,8,9]
]}


# Make a request
try:
    logger.info("Making call")
    result = client.StartTransaction("get_diagonal",parameters)
    logger.info("Received result")
except Exception as err:
    print(f"Request failed due to exception: {err}")
    result = None

# Get results
print(result)
