import os

env = os.getenv("OMAGENT_MODE", "lite").lower()

if env == "lite":
    print ("importing lite DefaultClient client") 
    from .lite_client import DefaultClient
else:
    print ("importing pro DefaultClient client")
    from .client import DefaultClient

