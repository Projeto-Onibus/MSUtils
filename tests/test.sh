#!/bin/bash

cd .. && python3 -m pip install . && cd tests

echo "\n\n\n\n\n\n"

python3 example-server-get-diagonals.py & 
python3 example-server-sum-diagonals.py & 

sleep 1

python3 example-client.py


killall "python3 example-server"
