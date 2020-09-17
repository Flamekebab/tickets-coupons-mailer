#!/usr/bin/env python3
# This program's task is to build useful CSV files based on everyone who should have a ticket for the 
# 2020 Vowley races. The tickets might be paid or complimentary - if they're registered this should provide the data.
import csv
import sys
import json
import string
import requests
from requests.auth import HTTPBasicAuth 
from typing import List
import smtplib
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
#from datetime import datetime
#from dateutil.parser import parse

#Python doesn't have PHP's var_dump. Fortunately someone wrote an equivalent so we have it here for debugging:
from var_dump import var_dump

# 1. Import `QApplication` and all the required widgets
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog, QLabel, QPushButton, QVBoxLayout
from PyQt5 import QtGui 
from PyQt5.QtGui import QIcon


#QApplication is an object that we fiddle with. I think. We pass it the command line arguments, for some as-yet-obscure reason.
app = QApplication(sys.argv)

#Now we create the GUI
#Window is an object of the type QWidget. Then we do the usual object-orientated stuff to mess with it.
window = QWidget()
window.setWindowTitle('2020 Race Tickets Data Processor')

#Also I don't want the default icon (whether that's the window or the tray)
icon = QIcon('icon.png')
app.setWindowIcon(QIcon(icon))

#The first two parameters are the x and y coordinates at which the window will be placed on the screen. 
#The third and fourth parameters are the width and height of the window.
window.setGeometry(100, 100, 480, 200)
window.move(260, 215)

#Let's lay things out vertically
layout = QVBoxLayout()

#Then we create the widgets that make up the GUI. For example the QLabel object type:
#QLabel objects can accept HTML text, so you can use the HTML element to format the text as an h1 header.

doStuffButton = QPushButton('Grab the form data and process it')

#When the data files are loaded we want that reported to the user.
doStuffLabel = QLabel('Push the button to pull data from the Vowley site.')

def doStuff():
    doStuffButton.hide()
    doStuffLabel.hide()

    #The data we're going to be working our way through is split across multiple forms with two nested forms
    #The IDs are as follows:
    # 4 - Main form
    # 8/13 - Honeybrook
    # 9 - Vowley guests
    # 10 - NBC hospitality tickets
    # 16 - suppliers

    # 5 - Additionals
    # 6 - Falcon info

    #We first need the main data. Once that's complete we cross-reference ID information with the two nested forms
    #This way the only data from the nested forms is stuff we want (so orphaned entries will be ignored)

    #In terms of response length we can stipulate the number of entries per page (upper limit unsure)
    #However we also have the option of using the total_count part. It's one-based (as opposed to counting from zero).

    #So let's start building a data set.



    response = requests.get('https://DOMAIN/wp-json/gf/v2/forms/4/entries?paging[page_size]=10', 
            auth = HTTPBasicAuth('key', 'secret'))

    if response.status_code != 200:
        # This means something went wrong.
        
        #print(response.status_code)

        #Tell the user
        stuffFailedLabel.show()
        #Add a button that kills the program:
        closeButton = QPushButton('Close program')
        closeButton.clicked.connect(lambda _: sys.exit())
        layout.addWidget(closeButton)

        #Also let's email me the response:

        #Credentials. Should probably make these safe somewhere...
        username = "username"
        password = "password"
        mailServer = "outlook.office365.com"

        sender = "Vowley Events <address@domain>"

        message = MIMEMultipart("alternative")
        message["Subject"] = "Vowley API issue (automated bug report)"
        message["From"] = "Vowley Events <address@domain>"

        message["To"] = "myworkemail@domain"

        #HTML email is a bit needless
        simpleBodyText = str(response.content)
        
        #sort out MIME type, whatever that is:
        simpleBody = MIMEText(simpleBodyText, "plain")

        #Attach the two body texts to the message object
        message.attach(simpleBody)

        #Send that to the mail server!
        server = smtplib.SMTP(mailServer, 587)
        server.starttls()
        server.login(username, password)
        server.sendmail(sender, "myworkemail@domain", message.as_string())
        server.quit()
    else: 
    #The API call went through just fine
    # We could just use that data but instead we're going to setup a fresh API call.
        decodedResponse = response.json()

        #Grab the first load of entries.
        sourceData = decodedResponse['entries']

        #The decodedResponse is an object with two properties - "total_count" and "entries"
        #We've already grabbed the first page of data, was that all of them?
        #Len is a zero-based count whereas total_count is not so we need that +1 to balance things out.
        #We've already got page 1 loaded so we set our value to 2.
        page = 2
        
        while ((len(sourceData) + 1) < decodedResponse['total_count']):
            #This means that the first page of entries wasn't the whole lot. We need all of them so we need additional API calls.
            requestURL = "https://DOMAIN/wp-json/gf/v2/forms/4/entries?paging[page_size]=10&paging[current_page]=" + str(page)
            #print(requestURL)
            response = requests.get(requestURL, 
            auth = HTTPBasicAuth('key', 'secret'))
            #print("Getting page " + str(page))
            
            #Increment the page counter
            page+=1
            
           
            
            #Grab the new response and convert it to JSON
            decodedResponse = response.json()


            sourceData = sourceData + decodedResponse['entries']
            #print("sourceData is " + str(len(sourceData)) + " long and decodedResponse is " + str(decodedResponse['total_count']) + " long")
            
        #We now have all the data from the main form, let's gather the rest in a similar fashion:

        #First the forms, as strings:
        formIDs = ["8", "9", "10", "13", "16"]

        #for each of the form IDs provided we grab data and add it to the main set
        for formID in formIDs:
            #Initialise the temporary list that'll contain the additional source data
            moreSourceData = []
            #Reset the page number
            page = 0

            while ((len(moreSourceData) + 1) < decodedResponse['total_count']):
                #This means that the first page of entries wasn't the whole lot. We need all of them so we need additional API calls.
                requestURL = "https://DOMAIN/wp-json/gf/v2/forms/" + formID + "/entries?paging[page_size]=10&paging[current_page]=" + str(page)
                #print(requestURL)
                response = requests.get(requestURL, 
                auth = HTTPBasicAuth('key', 'secret'))
                #Increment the page counter
                page+=1
                
                #Grab the new response and convert it to JSON
                decodedResponse = response.json()

                moreSourceData = moreSourceData + decodedResponse['entries']
            
            #And now we append that lot!
            sourceData = sourceData + moreSourceData



        #Initialise the mainData list
        mainData = []

        #var_dump(sourceData[1])

        #Then we work through our sourceData and turn it into something easier to read:
        for entry in sourceData:
            #var_dump(entry)
            #We're going to build a dictionary here because it's much easier to parse later
            entryMainData = {}
            #Entry WordPress ID
            entryMainData['id'] = entry['id']
            #Prefix
            entryMainData['prefix'] = entry['1.2'].capitalize()
            #First
            entryMainData['firstname'] = entry['1.3'].title()
            #Last
            #We sometimes get people with the name "O'Neil" and similar and we don't want to mess up their names:
            #To this end we try to find the location of an apostrophe or dash in the string. If it doesn't find one the result is -1.
            #So if the result isn't -1 we know one was found and we rely on the customer being able to spell their own name.
            #I wish we didn't have to do this but here we are.
            if (entry['1.6'].find("'") != -1) or (entry['1.6'].find("-") != -1):
                entryMainData['lastname'] = entry['1.6']
            else:
                entryMainData['lastname'] = entry['1.6'].title()
            #Email - stop capitalising your email address, you strange people
            entryMainData['email'] = entry['2'].lower()
            #Phone - where we replace O with 0 because apparently some people don't know how phone numbers work
            entryMainData['phone'] = entry['3'].replace("O", "0")
            #Then we remove spaces:
            entryMainData['phone'] = entryMainData['phone'].replace(" ", "")
            #Let's combine the different bits of the address and append that. Some nitwit will break it somehow but we'll do our best.
            #4.3 is the town, 4.5 the postcode, and 4.6 the country
            entryMainData['address'] = entry['4.1'].title() + ", " + entry['4.2'].title() + ", " + entry['4.3'].title() + ", " + entry['4.5'].upper() + ", " + entry['4.6'].title()

            #Role (e.g. "competing falconer")
            #Here there are paid for tickets with " (£25)" suffixes and complimentary tickets without.
            #Let's strip that out and instead create a new field
            ticketType = entry['5'].split(" (")
            entryMainData['ticket'] = ticketType[0]

            if (entry['5'].find("(") != -1):
                entryMainData['ticket-price'] = "Paid"
            else:
                entryMainData['ticket-price'] = "Complimentary"

            #How much did they pay us?
            #var_dump(entry['payment_amount'])
            if entry['payment_amount'] == None:
                entryMainData['payment-made'] = "0.00"
            else:
                entryMainData['payment-made'] = entry['payment_amount']

            #We can also detect whether this attendee is with someone like NBC or Honeybrook and note that down:
            if (entry['form_id'] == "9"):
                entryMainData['ticket-type'] = "Vowley Guest"
            elif (entry['form_id'] == "10"):
                entryMainData['ticket-type'] = "NBC Guest"
            elif (entry['form_id'] == "8") or (entry['form_id'] == "13"):
                entryMainData['ticket-type'] = "Honeybrook Guest"
            elif (entry['form_id'] == "16"):
                entryMainData['ticket-type'] = "Supplier"
            else:
                entryMainData['ticket-type'] = "Customer"

            #Optional checkboxes are slightly trickier as we need to check whether they exist or not. 
            #If a user didn't select them they don't appear in the API output and so would throw a NameError
            try:  
                if len(entry['21.1']) > 1:
                    entryMainData['lunch-26th'] = "yes"
                    # print(entry['id'] + " wants lunch on the 26th (" + entry['21.1'] + ")")
                elif entry['21.1'] == "":
                    entryMainData['lunch-26th'] = "no"
                    # print(entry['id'] + " gets no lunch on the 26th (" + entry['21.1'] + ")")
            except:
                    entryMainData['lunch-26th'] = "no"
                    # print(entry['id'] + " gets no lunch on the 26th (" + entry['21.1'] + ")")

            # try:
            #     var_dump(entry['21.1'])
            # except:
            #     pass
            try:
                #if entry['21.2'] == "I would like lunch on Sunday 27th during the Finals|0":
                if len(entry['21.2']) > 1:
                    entryMainData['lunch-27th'] = "yes"
                    # print(entry['id'] + " wants lunch on the 27th (" + entry['21.2'] + ")")
                elif entry['21.2'] == "":
                    entryMainData['lunch-27th'] = "no"
                    # print(entry['id'] + " gets no lunch on the 27th (" + entry['21.2'] + ")")
            except:
                    entryMainData['lunch-27th'] = "no"
                    # print(entry['id'] + " gets no lunch on the 27th (" + entry['21.2'] + ")")

            #The barbecue is much easier as it's a mandatory radio button, however the answer may be yes (paid) or yes (complimentary)
            if entry['7'] == "Yes|8":
                entryMainData['barbecue'] = "yes"
                entryMainData['barbecue-cost'] = "paid"
            elif entry['7'] == "Yes|0":
                entryMainData['barbecue'] = "yes"
                entryMainData['barbecue-cost'] = "complimentary"
            else:
                entryMainData['barbecue'] = "no"
                entryMainData['barbecue-cost'] = "not applicable"

            #Then there's dietary requirements which is another def/ndef situations:
            try:
                entryMainData['dietary-requirements'] = entry['8']
            except:
                entryMainData['dietary-requirements'] = "none"

            #Did they bring a party? If so entry['10'] is a string rather than a list which is unhelpful. Let's fix that.
            if entry['9'] == "Multiple attendees":
                entryMainData['guest-ids'] = entry['10'].split(",")
            else:
                #They're alone but this way the variable is defined and we can use a foreach setup (which will do nothing but not error out either)
                entryMainData['guest-ids'] = []

            #Are they bringing falcons? 12 holds the answer (in the form of a string "Yes" and "No") and 13 has the IDs. Again, as a string.
            if entry['12'] == "Yes":
                entryMainData['falcon-ids'] = entry['13'].split(",")
            else:
                entryMainData['falcon-ids'] = []
                

            #Now that we have their information, what about their additionals?
            entryMainData['additionals'] = []

            for guest in entryMainData['guest-ids']:
                requestURL = "https://DOMAIN/wp-json/gf/v2/entries/" + guest
                response = requests.get(requestURL, 
                auth = HTTPBasicAuth('key', 'secret'))
                guestData = response.json()
                #var_dump(response)
                #Let's create a dictionary and then append it to the additionals list
                additional = {}

                additional['id'] = guest

                if (guestData['11'] == "Adult|25"):
                    additional['age'] = "adult"
                else:
                    additional['age'] = "child"

                additional['prefix'] = guestData['2.2']
                additional['firstname'] = guestData['2.3'].title()
                
                if (guestData['2.6'].find("'") != -1) or (guestData['2.6'].find("-") != -1):
                                additional['lastname'] = guestData['2.6']
                else:
                                additional['lastname'] = guestData['2.6'].title()

                additional['email'] = guestData['3'].lower()
                additional['phone'] = guestData['4']

                additional['address'] = guestData['5.1'].title() + ", " + guestData['5.2'].title() + ", " + guestData['5.3'].title() + ", " + guestData['5.5'].upper() + ", " + guestData['5.6'].title()

                additional['ticket'] = guestData['6']
                try:
                    test = guestData['14.1'].split()
                    if test[0] == "I":
                    #if len(guestData['14.1']) > 0:
                        additional['lunch-26th'] = "yes"
                        #print("The data for additional "+ guest + " says " + guestData['14.1'])
                        #print("We are setting their lunch value for 26th to " + additional['lunch-26th'] + "\n")
                except:
                        additional['lunch-26th'] = "no"
                        #print("We are setting their (" + guest + ") lunch value for 26th to " + additional['lunch-26th'] + "\n")
                
                try:
                    #if len(guestData['14.2']) > 0:
                    #if guestData[14.2] == "I would like lunch on Sunday 27th during the Finals|0":
                    test = guestData['14.2'].split()
                    if test[0] == "I":
                        additional['lunch-27th'] = "yes"
                except:
                        additional['lunch-27th'] = "no"
                # print("Additional 26th lunch? " + additional['lunch-26th'])
                # print(guestData['14.1'])
                # print("Additional 27th lunch? " + additional['lunch-27th'])
                # print(guestData['14.2'])

                if guestData['8'] == "Yes|8":
                    additional['barbecue'] = "yes"
                else:
                    additional['barbecue'] = "no"

                #Then there's dietary requirements which is another def/ndef situations:
                try:
                    additional['dietary-requirements'] = guestData['9']
                except:
                    additional['dietary-requirements'] = "none"

                entryMainData['additionals'].append(additional)

            #That's their guests dealt with. Now falcons:
            entryMainData['falcons'] = []

            for falconID in entryMainData['falcon-ids']:
                if (len(falconID) > 0):
                    requestURL = "https://DOMAIN/wp-json/gf/v2/entries/" + falconID
                    response = requests.get(requestURL, 
                    auth = HTTPBasicAuth('key', 'secret'))
                    falconData = response.json()

                    falcon = {}
                    #var_dump(falconData)
                    falcon['id'] = falconData['id']
                    falcon['owner'] = falconData['23'].title()
                    falcon['falconer'] = falconData['24'].title()
                    falcon['trainer'] = falconData['25'].title()
                    falcon['breeder'] = falconData['27'].title()
                    falcon['name'] = string.capwords(falconData['5'])
                    falcon['species'] = falconData['6'].title()
                    falcon['hatched'] = falconData['7']
                    falcon['sex'] = falconData['8']
                    falcon['ring-number'] = falconData['9']

                    photoCleanUp = falconData['13'].split("|:||:||:|")
                    falcon['photo'] = photoCleanUp[0].strip()

                    #Accommodation is a little trickier but not too bad. It's contingent on falconData['11'] but that doesn't really matter
            
                    if (falconData['12.1'] == "Thursday 24th"):
                        falcon['thursday-mews'] = "Yes"
                    else:
                        falcon['thursday-mews'] = "No"

                    if (falconData['12.2'] == "Friday 25th"):
                        falcon['friday-mews'] = "Yes"
                    else:
                        falcon['friday-mews'] = "No"

                    if (falconData['12.3'] == "Saturday 26th"):
                        falcon['saturday-mews'] = "Yes"
                    else:
                        falcon['saturday-mews'] = "No"

                    if (falconData['12.4'] == "Sunday 27th"):
                        falcon['sunday-mews'] = "Yes"
                    else:
                        falcon['sunday-mews'] = "No"

                    #Then there's the races for the falcons

                    #The additional data has all the fields defined even if not filled in so we can check via length:
                    #14.1 is the flat race, 14.2 is the hunt race
                    if (len(falconData['14.1']) > 0):
                        falcon['flat-race'] = "Yes"
                        falcon['flat-race-slip-prefix'] = falconData['16.2'].title()
                        falcon['flat-race-slip-firstname'] = falconData['16.3'].title()
                        falcon['flat-race-slip-lastname'] = falconData['16.6'].title()
                        falcon['flat-race-lure-prefix'] = falconData['17.2'].title()
                        falcon['flat-race-lure-firstname'] = falconData['17.3'].title()
                        falcon['flat-race-lure-lastname'] = falconData['17.6'].title()
                        falcon['flat-race-teamname'] = falconData['18']
                    else:
                        falcon['flat-race'] = "No"
                        falcon['flat-race-slip-prefix'] = ""
                        falcon['flat-race-slip-firstname'] = ""
                        falcon['flat-race-slip-lastname'] = ""
                        falcon['flat-race-lure-prefix'] = ""
                        falcon['flat-race-lure-firstname'] = ""
                        falcon['flat-race-lure-lastname'] = ""
                        falcon['flat-race-teamname'] = ""
                        
                    if (len(falconData['14.2']) > 0):
                        falcon['hunt-race'] = "Yes"
                        falcon['hunt-race-slip-prefix'] = falconData['20.2'].title()
                        falcon['hunt-race-slip-firstname'] = falconData['20.3'].title()
                        falcon['hunt-race-slip-lastname'] = falconData['20.6'].title()
                        falcon['hunt-race-pilot-prefix'] = falconData['21.2'].title()
                        falcon['hunt-race-pilot-firstname'] = falconData['21.3'].title()
                        falcon['hunt-race-pilot-lastname'] = falconData['21.6'].title()
                        falcon['hunt-race-teamname'] = falconData['22']
                    else:
                        falcon['hunt-race'] = "No"
                        falcon['hunt-race-slip-prefix'] = ""
                        falcon['hunt-race-slip-firstname'] = ""
                        falcon['hunt-race-slip-lastname'] = ""
                        falcon['hunt-race-pilot-prefix'] = ""
                        falcon['hunt-race-pilot-firstname'] = ""
                        falcon['hunt-race-pilot-lastname'] = ""
                        falcon['hunt-race-teamname'] = ""
                    
                    #And append the falcon's info to the main object
                    entryMainData['falcons'].append(falcon)

            mainData.append(entryMainData)
        #var_dump(mainData)

         #Time for hacky workarounds because people made changes at the last minute
            bbqFlips = ["317", "324", "608", "609", "610", "392", "347"]

        for entry in mainData:
            #P needs lunch as does A R
            if entry['id'] == "552" or entry['id'] =="544":
                 entry['lunch-26th'] = "yes"
            #A whole load of people need barbecue tickets:
            if entry['id'] in bbqFlips:
                entry['barbecue'] = "yes"
            



        #Now we prompt the user for where to save the output (which will then be passed to the actual function that writes the file)
        outputPath = QFileDialog.getSaveFileName(None,'Save file', './output.csv', "CSV file (*.csv)")
        #The output path is a tuple ("A tuple is a collection which is ordered and unchangeable."). We only want the first element in it.
        #var_dump(outputPath[0])

        #We could do with a JSON version of the data too:
        jsonPath = outputPath[0]
        #remove the file extension
        jsonPath = jsonPath.strip(".csv")
        jsonPath = jsonPath + ".json"
        with open(jsonPath, 'w') as outfile:
             json.dump(mainData, outfile)

        #our CSV should now be complete, let's output it:
        with open(outputPath[0], 'w', newline='') as outputFile:
        #    filehandle.writelines("%s\n" % item for item in tableData)
            writer = csv.writer(outputFile, quotechar='"', quoting=csv.QUOTE_ALL)
            
            #The CSV file we're outputting is more useful if it comes with headings:
            headings = ["ID", "Prefix", "First", "Last", "Email", "Phone", "Ticket", "Additionals:", "ID", "Prefix", "First", "Last", "Email", "Phone", "Ticket", "Falcons", "Falcon ID", "Falcon Name", "Species"]
            
            writer.writerow(headings)
            
            for entry in mainData:
                #For debugging:
                #print(str(entry) + "\n")

                #To ensure things turn out in the correct order we're going to specify:
            
                rowToWrite = entry['id'], entry['prefix'], entry['firstname'], entry['lastname'], entry['email'], entry['phone'], entry['ticket'], ', '.join(entry['guest-ids']), "", "", "", "", "", "", "", ', '.join(entry['falcon-ids'])
                writer.writerow(rowToWrite)

                #Now they might have additionals which will be on a new line but further along.
                #Ideally we want falcons on the same lines but that gets a little bit tricky so we need to be crafty

                if len(entry['guest-ids']) > 0:
                    for additional in entry['additionals']:
                        #Print the info about the guests on a new line with a load of blank columns first
                        rowToWrite = "", "", "", "", "", "", "", "", additional['id'], additional['prefix'], additional['firstname'], additional['lastname'], additional['email'], additional['phone'], additional['ticket']
                        
                        #They might also have falcons. How about that?
                        
                        try:
                            falcon = entry['falcons'].pop(0)
                            #rowToWrite is a tuple and they cannot be changed. Not a problem!
                            workaround = list(rowToWrite)
                            workaround = workaround + [""] + [falcon['id'], falcon['name'], falcon['species']]
                            rowToWrite = tuple(workaround)
                    
                        except:
                            pass
                        
                        #Write that line (additional + falcon)
                        writer.writerow(rowToWrite)

                #We've now dealt with the additionals and some falcons.
                #Alternatively we've not dealt with any additionals and entry['falcons'] still has entries.
                #OR neither is true - no additionals, no falcons. So we'll use TRY
                while len(entry['falcons']) > 0:
                    try:
                        falcon = entry['falcons'].pop(0)
                        rowToWrite = "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", falcon['id'], falcon['name'], falcon['species']
                    
                        writer.writerow(rowToWrite)
                    except:
                        pass

       

        #Now we show the thing that says we've done it!
        stuffDoneLabel.show()
        #Add a button that kills the program:
        closeButton = QPushButton('Close program')
        closeButton.clicked.connect(lambda _: sys.exit())
        layout.addWidget(closeButton)
    

#When the button is clicked run the code
doStuffButton.clicked.connect(doStuff)

stuffDoneLabel = QLabel('Data grabbed and processed!')
stuffDoneLabel.hide()

#If stuff goes wrong we need a different label
stuffFailedLabel = QLabel('Something went wrong. The error has been emailed to NAME for him to debug.')
stuffFailedLabel.hide()

#Now we add those widgets to the layout. At present we're using a vertical layout so these are from top to bottom.
layout.addWidget(doStuffLabel)
layout.addWidget(doStuffButton)
layout.addWidget(stuffDoneLabel)
layout.addWidget(stuffFailedLabel)



#Then we need to actually display it:
window.setLayout(layout)
window.show()

#This one I don't fully understand:
sys.exit(app.exec())