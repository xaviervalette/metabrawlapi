class Battle:
   

   def __init__(self, battle):
      self.noDuration=False
      self.noStarPlayer=False
      self.noResult=False
      self.noType=False
      self.noTeams=False
      self.noPlayers=False
      self.noStarBrawlerTrophies=False
      self.noStarBrawlerPower=False
      self.noEventMode=False
      self.noRank=False

      self.playerTag= battle["playerTag"]
      self.mode = battle['battle']['mode']
      if 'duration' in battle['battle']:
         self.duration = battle['battle']['duration']
      else:
         self.noDuration=True

      if 'type' in battle['battle']:
         self.typee = battle['battle']['type']
      else:
         self.noType=True

      if 'rank' in battle['battle']:
         self.rank = battle['battle']['rank']
      else:
         self.noRank=True

      if 'result' in battle['battle']:
         self.result = battle['battle']['result']   
      else:
         self.noResult=True

      if 'teams' in battle['battle']:
         self.teams=battle['battle']['teams']
      else:
         self.noTeams=True
      
      if 'players' in battle['battle']:
         self.players=battle['battle']['players']
      else:
         self.noPlayers=True

      self.battleTime=battle['battleTime']
      self.mapEvent=battle['event']['map']
      self.idEvent=battle['event']['id']
      if 'mode' in battle['event']:
         self.modEvent=battle['event']['mode']
      else:
         self.noEventMode=True
      
      if 'starPlayer' in battle['battle'] and battle['battle']['starPlayer'] is not None :
         self.starTag=battle['battle']['starPlayer']['tag']
         self.starName=battle['battle']['starPlayer']['name']
         if 'trophies' in battle['battle']['starPlayer']['brawler']:
            self.starBrawlerTrophies=battle['battle']['starPlayer']['brawler']["trophies"]
         else:
            self.noStarBrawlerTrophies=True
         
         self.starBrawlerId=battle['battle']['starPlayer']['brawler']["id"]

         if 'power' in battle['battle']['starPlayer']['brawler']:
            self.starBrawlerPower=battle['battle']['starPlayer']['brawler']["power"]
         else:
            self.noStarBrawlerPower=True

         
         self.starBrawlername=battle['battle']['starPlayer']['brawler']["name"]
         self.winTeam=self.get_team_of_star_player()
      else:
         self.noStarPlayer= True

   def get_team_of_player(self):#without using star player
      if self.mode=="duoShowdown":
         for team in self.teams:
            for player in team:
               if player["tag"]==self.playerTag:
                  return team
      elif self.mode=="soloShowdown":
         for player in self.players:
            if player["tag"]==self.playerTag:
               return player

   
   def get_team_of_star_player(self):
      goodTeam=False
      winTeam=[]

      for team in self.teams:
         if goodTeam== False:
               winTeam.clear()
               for i in range(len(team)):
                  winTeam.append(team[i]["brawler"]["name"])
                  if team[i]["tag"]==self.starTag:
                     goodTeam=True
      winTeam.sort()
      return winTeam

   def is_equal(self, otherBattle):
      if self.noDuration== False:
         if self.duration==otherBattle.duration and self.battleTime==otherBattle.battleTime and self.playerTag ==otherBattle.playerTag:
            return True
         else:
            return False
      else:
         if self.battleTime==otherBattle.battleTime and self.modEvent==otherBattle.modEvent and self.playerTag ==otherBattle.playerTag:
            return True
         else:
            return False