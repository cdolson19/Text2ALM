"""
A config python file to store run-time variables.
"""
# System Setup:
# Part 1:
# This host address must be replaced with your IP address or host name.
CORE_NLP_HOST = 'http://leelavati.ist.unomaha.edu'

# Part 2:
# This port must match the port used for the Stanford CoreNLP system.
CORE_NLP_PORT = 9001

# Part 3:
# This port must match the port used for the LTH system.
LTH_PORT = 8071

# Part 4:
# This host name must be replaced with your IP address or host name.
LTH_HOST = f'http://leelavati.ist.unomaha.edu:{LTH_PORT}/parse'
