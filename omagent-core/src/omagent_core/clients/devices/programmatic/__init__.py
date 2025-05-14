import os

env = os.getenv("OMAGENT_MODE", "lite").lower()

if env == "lite":
    print ("importing lite ProgrammaticClient client") 
    from .lite_client import ProgrammaticClient
else:
    print ("importing pro ProgrammaticClient client")
    from .client import ProgrammaticClient

