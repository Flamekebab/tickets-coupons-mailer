#!/usr/bin/env python3
import csv
import sys
#Python doesn't have PHP's var_dump. Fortunately someone wrote an equivalent so we have it here for debugging:
from var_dump import var_dump

#Using the sys library we can work with command line arguments. The first one, 0, is the name of the program so instead we start from 1.
#print(sys.argv[1])

#We check to see whether an argument was supplied and error out if not.
try:
    sys.argv[1]
    sys.argv[2]
except IndexError:
    print("\nYou need to supply two arguments - the core data CSV followed by the additional data CSV.\n")
    quit()


#First we'll need to load our main data. The CSV module is a smidge on the weird side but if we just feed it into a list we end up with a
# nested list of data. Each line is a new list. Lovely.
with open(sys.argv[1], newline='') as csvfile:
     mainData = list(csv.reader(csvfile, delimiter=',', quotechar='"'))

# # For debugging and similar we can get a reasonably helpful view of the structure of the data:
#var_dump(mainData)

#Next we need the additional information:
with open(sys.argv[2], newline='') as csvfile:
     additionalData = list(csv.reader(csvfile, delimiter=',', quotechar='"'))

#first let's create some headings:
headings = ["Prefix", "First", "Last", "Email", "Phone", "Role", "Party Leader", "Party Size", "Bringing Falcons", "How many falcons?", "Flat race entries", "Hunt race entries", "Trader information", "Registration date"]

var_dump(mainData)
#We don't need the old headings:
mainData.pop(0)
additionalData.pop(0)

#Now let's work our way through the main data, branching when necessary
partyLeaders = []

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

for additionalEntry in additionalData:
    freshEntry = {}
    freshEntry['Prefix'] = additionalEntry[0]
    freshEntry['First'] = additionalEntry[1]
    freshEntry['Last'] = additionalEntry[3]
    freshEntry['Email'] = additionalEntry[6]
    freshEntry['Phone'] = additionalEntry[5]
    freshEntry['Role'] = additionalEntry[7]

    #Their party leader is a tad trickier but we can cross reference the parent ID and child IDs from the two datasets:
    for mainEntry in mainData:
        if mainEntry[20] == additionalEntry[19]:
            freshEntry['Party Leader'] = mainEntry[1] + " " + mainEntry[3]
            #We can do the same calculation we did earlier from here:
            freshEntry['Party Size'] = (len(mainEntry[10].split(',')) + 1)

    #For safety let's add some blank fields:
    freshEntry['Bringing Falcons?'] = ""
    freshEntry['How many falcons?'] = ""
    freshEntry['Flat race entries'] = ""
    freshEntry['Hunt race entries'] = ""
    freshEntry['Trader Information'] = ""
    freshEntry['Registration date'] = additionalEntry[10][:additionalEntry[10].index(' ')]

    #Append the completed member to the main list
    partyMembers.append(freshEntry)
    #var_dump(freshEntry)

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
