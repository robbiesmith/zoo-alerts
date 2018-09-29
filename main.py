from lxml import etree
from datetime import timedelta, date, datetime
import requests
import re
import time
import json

users = []

with open('users.json') as f:  
    users = json.load(f)
    
NS_streets = [
    'palatine av n',
    'greenwood av n',
    'phinney av n',
    'dayton av n',
    'evanston av n',
    'fremont av n',
    'linden av n',
    'aurora av n',
    'whitman av n',
    'woodland pl n'
]

NS_numbers = [ 4800, 6100 ]

EW_streets = [
    'n 48th st',
    'n 49th st',
    'n 50th st',
    'n 51st st',
    'n 52nd st',
    'n 53rd st',
    'n 54th st',
    'n 55th st',
    'n argyle pl',
    'n 56th st',
    'n 57th st',
    'n 58th st',
    'n 59th st',
    'n 60th st',
    'n 61st st'
]

EW_numbers = [ 0, 1000 ]

known_incidents = {}

def send_message(type, units, location):
    for user in users:
        key = user['key']
        event = user['event']
        r = requests.post("https://maker.ifttt.com/trigger/{}/with/key/{}".format(event, key), data={ "value1" : type, "value2" : location, "value3" : units })
        print(r.status_code, r.reason)

def address_in_neighborhood(location):
    if re.search(" [/] ", location.lower()):
        parts = location.split("/")
        if len(parts) == 2:
            if parts[0].lower().strip() in NS_streets and parts[1].lower().strip() in EW_streets:
                return True
            elif parts[0].lower().strip() in EW_streets and parts[1].lower().strip() in NS_streets:
                return True
    elif re.search("[a-z] ?[/]", location.lower()):
        parts = location.split("/")
        if len(parts) == 2:
            if parts[0].lower().strip() in NS_streets and parts[1].lower().strip() in EW_streets:
                return True
            elif parts[0].lower().strip() in EW_streets and parts[1].lower().strip() in NS_streets:
                return True
    elif re.match("\d+ av[ e]", location.lower()):
        # if a numbered ave then it's not a house number
        return False
    elif re.match("\d+ ", location):
        parts = location.split(" ", 1)
        if len(parts) == 2:
            if int(parts[0]) > NS_numbers[0] and int(parts[0]) < NS_numbers[1] and parts[1].lower().strip() in NS_streets:
                return True
            elif int(parts[0]) > EW_numbers[0] and int(parts[0]) < EW_numbers[1] and parts[1].lower().strip() in EW_streets:
                return True

    elif re.match("\d+-\d+ ", location):
        
        parts = location.split(" ", 1)
        if len(parts) == 2:
            numbers = parts[0].split("-", 1)
            if len(numbers) == 2:
                if int(numbers[0]) > NS_numbers[0] and int(numbers[0]) < NS_numbers[1] and parts[1].lower().strip() in NS_streets:
                    return True
                elif int(numbers[0]) > EW_numbers[0] and int(numbers[0]) < EW_numbers[1] and parts[1].lower().strip() in EW_streets:
                    return True
    return False

def getLiveFeed():
    url = "http://www2.seattle.gov/fire/realtime911/getRecsForDatePub.asp?action=Today&incDate=&rad1=des"

    parser = etree.HTMLParser()
    tree = etree.parse(url, parser)
    root = tree.getroot()

    incidentRows = tree.xpath("//tr[@id]") # all table rows with id defined
    for incidentRow in incidentRows:
        item = incidentRow.xpath("td")
        dt = item[0].text
        incidentId = item[1].text
        if incidentId in known_incidents:
            continue
        try:
            level = int(item[2].text)
        except:
            level = 1
        units = item[3].text
        location = item[4].text
        type = item[5].text
        if not incidentId: # bad row - no idea what to do
            continue
        if address_in_neighborhood(location):
            known_incidents[incidentId] = dt
            print ('FOUND ONE ' + location)
            when = datetime.strptime(dt, '%m/%d/%Y %I:%M:%S %p')
            send_message(type, units, location)
    
if __name__ == "__main__":
    while True:
        getLiveFeed()
        time.sleep(120)
    