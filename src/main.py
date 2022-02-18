from functions import *
import time
from datetime import datetime
import configparser

"""
READ CONFIG
"""
config = configparser.ConfigParser()
config.read('config.ini')

"""
GLOBAL VARIABLES
"""
config = configparser.ConfigParser()
config.read('config.ini')
player_limit = int(config['DEFAULT']['playerLimit'])
limitNumberOfBattles = int(config['DEFAULT']['limitNumberOfBattles'])
countries_list = json.loads(config['DEFAULT']['countryList'])
expectedModes = json.loads(config['DEFAULT']['expectedModes'])
logFileName = logPath+path_separator+"timeLog.txt"

"""
MAIN
"""
start2 = time.time()
getCurrentEvents(token)
delOldEvents("battles")
delOldEvents("stats")

print("\n***getRankings***\n")
ranks = getRankings(token, countries_list, player_limit)

print("\n***getBattlelogs***\n")
battlelogs = getBattlelogs(token, ranks)
end2 = time.time()
callTime = end2 - start2

print("\n***STORE BATTLES***\n")
start3 = time.time()
newBattle, interestingBattle, totalBattle = storeBattles(
    battlelogs, limitNumberOfBattles, expectedModes)
end3 = time.time()
storeBattleTime = end3 - start3

print("\n***COMPUTE BEST BRAWLER***\n")
start4 = time.time()
storeBestTeam()
end4 = time.time()
computeBestBrawler = end4 - start4

now = datetime.now()
dateTime = now.strftime("%Y-%m-%d %H:%M:%S")
processHistory = {"datetime": dateTime,
                  "callTime": callTime,
                  "storeBattleTime": storeBattleTime,
                  "computeBestBrawler": computeBestBrawler,
                  "countryNumber": len(countries_list),
                  "playerNumber": player_limit,
                  "newBattle": newBattle,
                  "dupBattle": interestingBattle,
                  "interestingBattle": interestingBattle,
                  "totalBattle": totalBattle,
                  "countryList": countries_list
                  }

print(processHistory)
# WRITE LOGS
try:
    with open(logFileName) as fp:
        timeLog = json.load(fp)
except:
    timeLog = []

timeLog.append(processHistory)
with open(logFileName, 'w') as json_file:
    json.dump(timeLog, json_file,
              indent=4)