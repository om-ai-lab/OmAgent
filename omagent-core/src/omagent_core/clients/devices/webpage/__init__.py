import os

env = os.getenv("OMAGENT_MODE", "lite").lower()

if env == "lite":
    print ("importing lite client") 
    from .lite_client import WebpageClient
else:
    print ("importing pro client")
    from .client import WebpageClient