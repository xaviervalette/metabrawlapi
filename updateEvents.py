from functions import *
from dotenv import load_dotenv

"""
SETTING GLOBAL VARIABLES
"""
if(platform.system() == "Windows"):
    path_separator = "\\"
else:
    path_separator = "/"

load_dotenv()
token = os.environ["BRAWL_COACH_TOKEN"]

print(token)

getCurrentEvents(token)