FROM 

RUN apt-get update && apt-get upgrade -y

RUN apt-get install python3-pip 

RUN python3 -m pip install numpy scipy 
