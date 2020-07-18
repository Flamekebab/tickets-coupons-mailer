#!/usr/bin/env python3
import json
import requests
import csv
import sys
from requests.auth import HTTPBasicAuth 
#from var_dump import var_dump

response = requests.get('https://DOMAIN/wp-json/gf/v2/forms/1/entries?paging[page_size]=200', 
            auth = HTTPBasicAuth('key', 'secret'))

if response.status_code != 200:
    # This means something went wrong.
    print(response.status_code)

decodedResponse = response.json()
#var_dump(decodedResponse)
mainData = []

for entry in decodedResponse['entries']:
    entryMainData = []
    #Prefix
    entryMainData.append(entry['1.2'])
    #First
    entryMainData.append(entry['1.3'])
    #Middle (unused)
    entryMainData.append('')
    #Last
    entryMainData.append(entry['1.6'])
    #Suffix (unused)
    entryMainData.append('')
    #Email
    entryMainData.append(entry['2'])
    #Phone
    entryMainData.append(entry['4'])
    #Role (e.g. "competing falconer")
    entryMainData.append(entry['15'])
    #What product will you be offering? (We're not bothering with it here)
    entryMainData.append('')
    #Single attendee/multiple attendees
    entryMainData.append(entry['16'])
    #List of attendee IDs
    entryMainData.append(entry['8'])
    #Unused fields (connected to multiple attendee stuff)
    entryMainData.append('')
    entryMainData.append('')
    entryMainData.append('')
    entryMainData.append('')
    #Entering falcons? Y/N
    entryMainData.append(entry['17'])
    #Trader information
    #entryMainData.append(entry['10'])
    #How many falcons total?
    entryMainData.append(entry['12'])
    #Flat race falcon count
    entryMainData.append(entry['13'])
    #Hunt race falcon count
    entryMainData.append(entry['14'])
    #Created by ID (unused)
    entryMainData.append('')
    #Entry ID
    entryMainData.append(str(entry['id']))
    entryMainData.append(entry['date_created'])
    mainData.append(entryMainData)
    

#first let's create some headings:
headings = ["Prefix", "First", "Last", "Email", "Phone", "Role", "Party Leader", "Party Size", "Bringing Falcons", "How many falcons?", "Flat race entries", "Hunt race entries", "Trader information", "Registration date"]


#Now let's work our way through the main data, branching when necessary
partyLeaders = []

#var_dump(additionalData)

for mainEntry in mainData:
    #Some of the entries are blank (they're where the additional info is) (also we're checking first name as the test data is missing prefixes in places)
    if len(mainEntry[1]) > 0:
        #We only need certain columns and some of the new info is conditional. To keep life sane we'll be using a dictionary rather than a list (i.e. there's key/value pairs)
        freshEntry = {}
        freshEntry['Prefix'] = mainEntry[0]
        freshEntry['First'] = mainEntry[1]
        freshEntry['Last'] = mainEntry[3]
        freshEntry['Email'] = mainEntry[5]
        freshEntry['Phone'] = mainEntry[6]
        freshEntry['Role'] = mainEntry[7]

        #How big is their party and who leads it?
        if mainEntry[9] == "single attendee":
            #They're alone so we set it to 1 and set their full name as the party leader
            freshEntry['Party Size'] = 1
            freshEntry['Party Leader'] = freshEntry['First'] + " " + freshEntry['Last']
        else:
            #They're the party leader (as this is the main data, not the additional)
            freshEntry['Party Leader'] = freshEntry['First'] + " " + freshEntry['Last']
            #The list of additional party members isn't an actual list - it's just a string (e.g. "8,9,10")
            #Let's split it and then count it! (also add 1 because they're part of their party!)
            freshEntry['Party Size'] = (len(mainEntry[10].split(',')) + 1)

        #Are they bringing falcons?
        if mainEntry[15] == "No":
            freshEntry['Bringing Falcons?'] = "No"
            freshEntry['How many falcons?'] = 0
            freshEntry['Flat race entries'] = 0
            freshEntry['Hunt race entries'] = 0
        else:
            freshEntry['Bringing Falcons?'] = "Yes"
            freshEntry['How many falcons?'] = mainEntry[16]
            freshEntry['Flat race entries'] = mainEntry[17]
            freshEntry['Hunt race entries'] = mainEntry[18]

        #If they're a trader we record that info, if not we register a blank string (blank fields will be an issue)
        if mainEntry[7] == "Trader":
            freshEntry['Trader Information'] = mainEntry[8]
        else:
            freshEntry['Trader Information'] = ""

        #Registration info could be handy but I think we can ditch the actual time:
        #We're using string.index() to find the location of the space character and then grabbing everything before that character.
        # e.g. mainEntry[21][:2] would grab the first 2 characters of the string.
        freshEntry['Registration date'] = mainEntry[21][:mainEntry[21].index(' ')]
        #print(freshEntry)

        #That's a party leader sorted. Load it into the array and repeat.
        partyLeaders.append(freshEntry)

#Debug:
#var_dump(partyLeaders)

#Now for the additional people
partyMembers = []

#Now we want the additional attendee information
response = requests.get('https://DOMAIN/wp-json/gf/v2/forms/2/entries?paging[page_size]=200', 
            auth = HTTPBasicAuth('key', 'secret'))

if response.status_code != 200:
    # This means something went wrong.
    print(response.status_code)

decodedResponse = response.json()

for additionalEntry in decodedResponse['entries']:
    freshEntry = {}
    freshEntry['Prefix'] = additionalEntry['1.2']
    freshEntry['First'] = additionalEntry['1.3']
    freshEntry['Last'] = additionalEntry['1.6']
    freshEntry['Email'] = additionalEntry['3']
    freshEntry['Phone'] = additionalEntry['2']
    freshEntry['Role'] = additionalEntry['7']

    #Their party leader is a tad trickier but we can cross reference the parent ID and child IDs from the two datasets:
    for mainEntry in mainData:
        if mainEntry[20] == additionalEntry['gpnf_entry_parent']:
            freshEntry['Party Leader'] = mainEntry[1] + " " + mainEntry[3]
            #We can do the same calculation we did earlier from here:
            freshEntry['Party Size'] = (len(mainEntry[10].split(',')) + 1)

    #For safety let's add some blank fields:
    freshEntry['Bringing Falcons?'] = ""
    freshEntry['How many falcons?'] = ""
    freshEntry['Flat race entries'] = ""
    freshEntry['Hunt race entries'] = ""
    freshEntry['Trader Information'] = ""
    freshEntry['Registration date'] = additionalEntry['date_created'][:additionalEntry['date_created'].index(' ')]

    #Append the completed member to the main list
    partyMembers.append(freshEntry)
    
    #var_dump(additionalEntry)

#var_dump(partyMembers)

#Now let's create the final list:
finalList = []

#We're going to work our way through and add additional party members when they come up:

for partyLeader in partyLeaders:
    #Add the party leader
    finalList.append(partyLeader)

    #Do they have extra party members?
    if partyLeader['Party Size'] > 1:
        for partyMember in partyMembers:
            if partyMember['Party Leader'] == partyLeader['Party Leader']:
                finalList.append(partyMember)

#finalList contains everything now except the headings - we'll be writing those in the bit below:

#our CSV should now be complete, let's output it:
with open('output.csv', 'w') as outputFile:
#    filehandle.writelines("%s\n" % item for item in tableData)
    writer = csv.writer(outputFile, quotechar='"', quoting=csv.QUOTE_ALL)

    writer.writerow(headings)
    for entry in finalList:
        #To ensure things turn out in the correct order we're going to specify:
        rowToWrite = entry['Prefix'], entry['First'], entry['Last'], entry['Email'], entry['Phone'], entry['Role'], entry['Party Leader'], entry['Party Size'], entry['Bringing Falcons?'], entry['How many falcons?'], entry['Flat race entries'], entry['Hunt race entries'], entry['Trader Information'], entry['Registration date']
        writer.writerow(rowToWrite)
