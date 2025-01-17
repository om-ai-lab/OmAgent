import os

env = os.getenv("OMAGENT_MODE", "lite").lower()

if env == "lite":
    print ("importing lite client") 
    from .lite_client import ProgrammaticClient
else:
    print ("importing pro client")
    from .client import ProgrammaticClient

