import json
import requests
from battle import Battle
from datetime import datetime
import os
from pathlib import Path
from collections import Counter
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import platform
from datetime import datetime, timezone
from dotenv import load_dotenv

"""
SETTING GLOBAL VARIABLES
"""
if(platform.system() == "Windows"):
    path_separator = "\\"
else:
    path_separator = "/"

load_dotenv()

dataPath = os.environ["BRAWL_COACH_DATAPATH"]
backPath = os.environ["BRAWL_COACH_BACKPATH"]
logPath = os.environ["BRAWL_COACH_LOGPATH"]
token = os.environ["BRAWL_COACH_TOKEN"]
baseUrl = os.environ["BRAWL_STARS_API_BASE_URL"]
currentBattlePath = dataPath+"/battles/current"
allBattlePath = dataPath+"/battles/all"

"""
MAKE REST API GET CALL TO RETRIEVE BRAWL STARS SPECIFIC PLAYER STATS USING PLAYER TAG
"""
def getPlayerStats(token, tag):
    headers = {'Authorization': 'Bearer '+token}
    data = {}
    urlTag = tag.replace("#", "%23")
    response = requests.request(
        "GET", baseUrl+"/players/"+urlTag+"/battlelog", headers=headers, data=data)
    battlelogs = response.json()
    return battlelogs

"""
MAKE REST API GET CALL TO RETRIEVE BRAWL STARS CURRENT EVENTS
"""
def getCurrentEvents(token):

    headers = {'Authorization': 'Bearer '+token}
    data = {}
    response = requests.request(
        "GET", "https://api.brawlstars.com/v1/events/rotation", headers=headers, data=data)
    current_events = response.json()
    i = 0
    for event in current_events:
        event["currentEventNumber"] = i
        i = i+1
    with open(dataPath+'/events/current_events.json', 'w') as f:
        json.dump(current_events, f)
    return

"""
READ AND RETURN BRAWL STARS CURRENT EVENTS
"""
def readCurrentEvents(filepath):
    with open(dataPath+'/events/current_events.json') as f:
        current_events = json.load(f)
    return current_events

"""
DELETE OUTDATED EVENT FILES
"""
def delOldCurrentBattles():
    currentEventsId = []
    currentEvents = readCurrentEvents("todo")
    for event in currentEvents:
        currentEventsId.append(event["event"]["id"])

    for (dirpath, dirnames, filenames) in os.walk(currentBattlePath):
        for filename in filenames:
            fn = filename.split(".")
            oldEventId = int(fn[0])
            if oldEventId not in currentEventsId:
                os.remove(currentBattlePath+"/"+str(oldEventId)+".json")

"""
ROTATE OUTDATED EVENT FILES
"""
def rotateEvents(maxBattlesPerEvent):
    currentEventsId = []
    currentEvents = readCurrentEvents("todo")
    for event in currentEvents:
        currentEventsId.append(event["event"]["id"])

    for (dirpath, dirnames, filenames) in os.walk(currentBattlePath):
        for filename in filenames:
            fn = filename.split(".")
            oldEventId = int(fn[0])
            if oldEventId not in currentEventsId:
                try:
                    with open(currentBattlePath+"/"+str(oldEventId)+".json", 'r+') as f:
                        print(currentBattlePath+"/"+str(oldEventId)+".json")
                        data=json.load(f)
                    
                    if len(data)>maxBattlesPerEvent:
                        data=data[-maxBattlesPerEvent:]

                    with open(allBattlePath+"/"+str(oldEventId)+".json", 'w') as f:
                        json.dump(data[-maxBattlesPerEvent:], f, indent=4)
                except:
                    print("NO EVENT FILE")

                if len(data)>maxBattlesPerEvent:
                        data=data[-maxBattlesPerEvent:]
                with open(allBattlePath+"/"+str(oldEventId)+".json", 'w') as f:
                    json.dump(data[-maxBattlesPerEvent:], f, indent=4)
                try:
                    os.remove(currentBattlePath+"/"+str(oldEventId)+".json")
                except:
                    print("NO FILE TO REMOVE")

"""
READ AND RETURN BRAWL STARS EVENTS STATS
"""
def readEventsStats(event, soloOrTeams):
    with open(dataPath+'/stats/'+str(event["event"]["id"])+'.json') as f:
        events_stats = json.load(f)
    return events_stats[soloOrTeams], events_stats["battlesNumber"]

"""
MAKE REST API GET CALL TO RETRIEVE BRAWL STARS RANKINGS BASED ON COUNTRY LIST
"""
def getRankings(token, countries_list, player_limit):
    ranks_list = {}
    headers = {'Authorization': 'Bearer '+token}
    data = {}
    for country in countries_list:
        url = "https://api.brawlstars.com/v1/rankings/" + \
            country+"/players?limit="+str(player_limit)
        response = requests.request("GET", url, headers=headers, data=data)
        ranks_list[country] = response.json()
        print("Country:" + country + ", Response code: " +
              str(response.status_code))
    return ranks_list

"""
MAKE REST API GET CALL TO RETRIEVE BRAWL STARS RANKINGS BASED ON COUNTRY LIST
"""
def getBattlelogs(token, ranks_list):
    battlelogs_list = {}
    battlelogs = {}
    threads = []
    with ThreadPoolExecutor(max_workers=40) as executor:

        for country in ranks_list:
            battlelogs.clear()
            threads.append(executor.submit(getBattlelogsApiCalls,
                           country, ranks_list, battlelogs, token))

        for task in as_completed(threads):
            done = True
        battlelogs_list[country] = battlelogs
    return battlelogs_list

"""
MAKE REST API GET CALL TO RETRIEVE BRAWL STARS RANKINGS BASED ON COUNTRY LIST - THREAD
"""
def getBattlelogsApiCalls(country, ranks_list, battlelogs, token):
    headers = {'Authorization': 'Bearer '+token}
    data = {}
    for player in ranks_list[country]['items']:
        tag = player["tag"]
        url_tag = tag.replace("#", "%23")
        response = requests.request(
            "GET", "https://api.brawlstars.com/v1/players/"+url_tag+"/battlelog", headers=headers, data=data)
        battlelog = response.json()

        for battle in battlelog["items"]:
            # add the tag of the corresponding player in order to handle showdown
            battle["playerTag"] = tag
        battlelogs[tag] = battlelog
    return battlelogs

"""
RETURN SORTED WIN AND LOSE TEAM BASED ON BATTLE
"""
def extractTeamBattles(battle):
    winTeam = []
    loseTeam = []

    b = Battle(battle)
    if b.mode == "duoShowdown":
        if b.rank <= 2:
            for brawler in b.get_team_of_player():
                winTeam.append(brawler["brawler"]["name"])
        else:
            for brawler in b.get_team_of_player():
                loseTeam.append(brawler["brawler"]["name"])
    elif b.mode != "soloShowdown":
        # FIND INDEX WIN AND LOSE TEAM
        winTeamIndex = 1
        loseTeamIndex = 0
        for game_player in b.teams[0]:
            if (str(b.starTag) == str(game_player["tag"])):
                winTeamIndex = 0
                loseTeamIndex = 1

        # COLLECT BRAWLERS IN EACH TEAM
        for brawler in b.teams[winTeamIndex]:
            winTeam.append(brawler["brawler"]["name"])
        for brawler in b.teams[loseTeamIndex]:
            loseTeam.append(brawler["brawler"]["name"])

    # SORT AND RETURN TEAMS
    winTeam = sorted(winTeam)
    loseTeam = sorted(loseTeam)
    return winTeam, loseTeam

"""
RETURN SORTED WIN AND LOSE BRAWLER BASED ON BATTLE
"""
def extractSoloBattles(battle):
    winTeam = []
    loseTeam = []

    b = Battle(battle)
    if b.mode == "duoShowdown":
        if b.rank <= 2:
            for brawler in b.get_team_of_player():
                winTeam.append(brawler["brawler"]["name"])
        else:
            for brawler in b.get_team_of_player():
                loseTeam.append(brawler["brawler"]["name"])
    elif b.mode == "soloShowdown":
        if b.rank <= 4:
            winTeam.append(b.get_team_of_player()["brawler"]["name"])
        else:
            loseTeam.append(b.get_team_of_player()["brawler"]["name"])

    elif b.mode != "soloShowdown":
        # FIND INDEX WIN AND LOSE TEAM
        winTeamIndex = 1
        loseTeamIndex = 0
        for game_player in b.teams[0]:
            if (str(b.starTag) == str(game_player["tag"])):
                winTeamIndex = 0
                loseTeamIndex = 1

        # COLLECT BRAWLERS IN EACH TEAM
        for brawler in b.teams[winTeamIndex]:
            winTeam.append(brawler["brawler"]["name"])
        for brawler in b.teams[loseTeamIndex]:
            loseTeam.append(brawler["brawler"]["name"])

    # SORT AND RETURN TEAMS
    winTeam = sorted(winTeam)
    loseTeam = sorted(loseTeam)
    return winTeam, loseTeam

"""
REMOVE SAME TEAM IN A LIST FOR THE STATS
"""
def remove_team_duplicate(team):
    team_no_dupplicate = []
    for elem in team:
        if elem not in team_no_dupplicate:
            team_no_dupplicate.append(elem)
    return team_no_dupplicate

"""
COMPUTE AND STORE STATS
"""
def storeBestTeam():
    dataFolder = Path(currentBattlePath)
    dataFolder.mkdir(parents=True, exist_ok=True)
    currentEvent = readCurrentEvents("TODO")
    for event in currentEvent:
        map = event["event"]["map"]
        mode = event["event"]["mode"]
        startTime = event["startTime"]
        winTeams = []
        loseTeams = []
        try:
            with open(currentBattlePath+path_separator+str(event["event"]["id"])+".json", 'r') as f:
                battles_mode_map = json.load(f)
        except:
            print("NO DATA")
            continue

        winTeams.clear()
        loseTeams.clear()
        bestSolos = {}

        # GET WIN AND LOSE TEAMS
        for battle in battles_mode_map:
            winTeam, loseTeam = extractTeamBattles(battle)
            winTeam_set = set(winTeam)
            if len(winTeam) == len(winTeam_set):
                if len(winTeam) > 0:  # to avoid adding void team due to duoshowdown
                    winTeams.append(winTeam)
                if len(loseTeam) > 0:
                    loseTeams.append(loseTeam)

        winTeamsUnique = []
        winTeamsUnique = remove_team_duplicate(winTeams)
        loseTeamsUnique = []
        loseTeamsUnique = remove_team_duplicate(loseTeams)

        winTable = {}
        winList = []

        for team in winTeamsUnique:
            pickNumber = winTeams.count(team)+loseTeams.count(team)
            if(loseTeamsUnique.count(team) == 0):
                winRate = 1
            else:
                winRate = winTeams.count(team)/pickNumber
            win_dict = {
                "teamStats": {
                    "winNumber": winTeams.count(team),
                    "winRate": winRate,
                    "pickRate": (winTeams.count(team)+loseTeams.count(team))/(len(battles_mode_map)),
                    "pickNumber": pickNumber,
                    "brawlers": team
                }
            }
            winList.append(win_dict)
            winTable["teams"] = winList

            # GET WIN AND LOSE TEAMS
        for battle in battles_mode_map:
            winSolo, loseSolo = extractSoloBattles(battle)
            winSolo_set = set(winSolo)
            if len(winSolo) == len(winSolo_set):
                if len(winSolo) > 0:  # to avoid adding void team due to duoshowdown
                    for player in winSolo:
                        if player in bestSolos:
                            bestSolos[player]["wins"] = bestSolos[player]["wins"]+1
                        else:
                            bestSolos[player] = {}
                            bestSolos[player]["wins"] = 1
                            bestSolos[player]["loses"] = 0
                if len(loseSolo) > 0:
                    for player in loseSolo:
                        if player in bestSolos:
                            bestSolos[player]["loses"] = bestSolos[player]["loses"]+1
                        else:
                            bestSolos[player] = {}
                            bestSolos[player]["wins"] = 0
                            bestSolos[player]["loses"] = 1

        winListSolo = []

        for brawler in bestSolos:
            pickNumber = bestSolos[brawler]["wins"]+bestSolos[brawler]["loses"]
            if(bestSolos[brawler]["loses"] == 0):
                winRate = 1
            else:
                winRate = bestSolos[brawler]["wins"]/pickNumber
            win_dict = {
                "soloStats": {
                    "winNumber": bestSolos[brawler]["wins"],
                    "winRate": winRate,
                    "pickRate": (pickNumber/(len(battles_mode_map)))/2,
                    "pickNumber": pickNumber,
                    "brawler": brawler
                }
            }
            winListSolo.append(win_dict)
            winTable["solo"] = winListSolo
            winTable["battlesNumber"] = len(battles_mode_map)
            winTable["mode"] = mode
            winTable["map"] = map
            winTable["startTime"] = startTime

        filename = dataPath+"/stats/"+str(event["event"]["id"])+".json"
        with open(filename, 'w') as fp:
            json.dump(winTable, fp, indent=4)

"""
LIST FILES IN A DIR
"""
def getListOfFiles(dirName):
    for root, subdirectories, files in os.walk(dirName):
        for file in files:
            print(os.path.join(root, file))

"""
STORE BATTLES IN BATTLES DIR
"""
def storeBattles(battlelogsList, limitNumberOfBattles, expectedModes, maxBattlesPerEvent):
    battles={}
    go = False
    numberOfBattles = 0
    battleNotInEvent = 0
    battleInEvent = 0
    total = 0
    listNumOfBattles = []
    newBattle = 0
    duppBattle = 0
    lenBattles={}
    alreadyStoredBattle = 0
    curentEvent = readCurrentEvents("TODO")
    currentEventId=[]
    dataFolder = Path(currentBattlePath)
    dataFolder.mkdir(parents=True, exist_ok=True)

    for event in curentEvent:
        currentEventId.append(event["event"]["id"])

    for eventId in currentEventId:
        try:
            with open(f"{currentBattlePath}/{eventId}.json", 'r') as f:
                battles[eventId]=json.load(f)
            lenBattles[eventId]=len(battles[eventId])
        except:
            battles[eventId]=[]
            lenBattles[eventId]=0

    print(currentEventId)

    for pays in battlelogsList:
        for players in battlelogsList[pays]:
            if "items" in battlelogsList[pays][players]:
                numberOfBattles = 0
                for battle in battlelogsList[pays][players]["items"]:
                    if numberOfBattles < limitNumberOfBattles:
                        numberOfBattles = numberOfBattles+1
                        total = total+1
                        b = Battle(battle)
                        
                        go = False
                        if b.mode in expectedModes:
                            if not b.noDuration and not b.noResult and not b.noStarPlayer and not b.noType and not b.noTeams and b.typee != "friendly":
                                go = True
                        elif b.mode == "soloShowdown" or b.mode == "duoShowdown":
                            if not b.noType and b.typee != "friendly":
                                go = True

                        if go:
                            if b.eventId in currentEventId:
                                battles[b.eventId].append(battle)
                                battleInEvent += 1
                            else:
                                battleNotInEvent += 1

    for eventId in currentEventId:
        battlesNoDupp = remove_dupe_dicts(battles[eventId])
        duppBattle = duppBattle + (len(battles[eventId])-len(battlesNoDupp))
        newBattle=newBattle+(len(battlesNoDupp)-lenBattles[eventId])
        #if len(battlesNoDupp) > maxBattlesPerEvent:
            #battlesNoDupp[-maxBattlesPerEvent:]
        with open(f"{currentBattlePath}/{eventId}.json", 'w') as f:
            json.dump(battlesNoDupp, f, indent=4)
    return newBattle, duppBattle, battleInEvent, total

"""
REMOVE SAME DICTS IN A LIST OF DICTS
"""
def remove_dupe_dicts(l):
    list_of_strings = [json.dumps(d, sort_keys=True) for d in l]
    A = len(list_of_strings)
    list_of_strings = set(list_of_strings)
    B = len(list_of_strings)
    return [json.loads(s) for s in list_of_strings]

"""
CONVERT BRAWL STARS START/END STRING INTO DATETIME 
"""
def convertDateTimeFromString(string):
    year = int(string[0:4])
    month = int(string[4:6])
    day = int(string[6:8])
    hours = int(string[9:11])
    minutes = int(string[11:13])
    seconds = int(string[13:15])
    eventDateTime = datetime(year, month, day, hours, minutes, seconds)
    return eventDateTime

"""
GET DATETIME FROM BRAWL STARS START/END STRING
"""
def computeEventTime(event):
    # UTC TIME
    startDateTimeStr = event["startTime"]
    endDateTimeStr = event["endTime"]
    nowDateTime = datetime.now(timezone.utc)

    startDateTime = convertDateTimeFromString(startDateTimeStr)
    endDateTime = convertDateTimeFromString(endDateTimeStr)

    eventDuration = endDateTime.replace(
        tzinfo=timezone.utc)-startDateTime.replace(tzinfo=timezone.utc)
    timePassed = nowDateTime-startDateTime.replace(tzinfo=timezone.utc)
    remainTime = endDateTime.replace(tzinfo=timezone.utc)-nowDateTime

    progress = int(100.0*timePassed/eventDuration)

    return startDateTime, endDateTime, progress, remainTime

"""
CONVERT TIME DELTA INTO HOURS MINUTES SECONDS
"""
def convert_timedelta(duration):
    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return hours, minutes, seconds