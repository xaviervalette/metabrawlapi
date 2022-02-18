import re
import requests
from bs4 import BeautifulSoup
import os
import errno


sites = ['https://brawlify.com/gamemodes/detail/Duels', 
'https://brawlify.com/gamemodes/detail/Hot-Zone', 
'https://brawlify.com/gamemodes/detail/Knockout', 
'https://brawlify.com/gamemodes/detail/Gem-Grab', 
'https://brawlify.com/gamemodes/detail/Showdown', 
'https://brawlify.com/gamemodes/detail/Duo-Showdown', 
'https://brawlify.com/gamemodes/detail/Bounty', 
'https://brawlify.com/gamemodes/detail/Brawl-Ball', 
'https://brawlify.com/gamemodes/detail/Siege',
'https://brawlify.com/gamemodes/detail/Heist',
'https://brawlify.com/gamemodes/detail/Super-City-Rampage']

modes=["DUELS", "HOTZONE", "KNOCKOUT", "GEMGRAB", "SOLOSHOWDOWN", "DUOSHOWDOWN", "BOUNTY", "BRAWLBALL", "SIEGE", "HEIST", "SUPERCITYRAMPAGE"]
#site = "https://brawlify.com/gamemodes/detail/Duels"
i=0
for site in sites:
    response = requests.get(site)

    soup = BeautifulSoup(response.text, 'html.parser')
    img_tags = soup.find_all('img')

    urls = [img['src'] for img in img_tags]

    for url in urls:
        filename = re.search(r'/([\w_-]+[.](jpg|gif|png))$', url)
        if not filename:
            print("Regex didn't match with the url: {}".format(url))
            continue
        print(url)
        pictureName=filename.group(1)
        pictureName=pictureName.replace("-"," ").upper()
        pictureName=pictureName.replace(" 2","")
        pictureName=pictureName.replace("'","")
        pictureName=pictureName.replace(".PNG",".JPG")
        pictureName=pictureName.upper()
        pictureName=pictureName.replace(" ","")
        if(modes[i]=="DUOSHOWDOWN"):
            pictureName=pictureName.replace("DUO","")


        print(pictureName)

        filename="../web/static/img/maps/"+modes[i]+"/"+pictureName

        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        with open(filename, 'wb') as f:
            if 'http' not in url:
                # sometimes an image source can be relative 
                # if it is provide the base url which also happens 
                # to be the site variable atm. 
                url = '{}{}'.format(site, url)
            response = requests.get(url)
            f.write(response.content)
    i=i+1