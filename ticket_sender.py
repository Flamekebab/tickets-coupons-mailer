import json
import sys
from typing import List
import smtplib
import csv
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
#Python doesn't have PHP's var_dump. Fortunately someone wrote an equivalent so we have it here for debugging:
from var_dump import var_dump

#Using the sys library we can work with command line arguments. The first one, 0, is the name of the program so instead we start from 1.
#print(sys.argv[1])

#We check to see whether an argument was supplied and error out if not.
# try:
#     sys.argv[1]
# except IndexError:
#     print("\nIf you want to send emails include the list in JSON format")    

#First we'll need to load our main data. It's the text file we supplied as an argument. Load that into a dictionary.
# try:
#     print("Loaded " + sys.argv[1])
# except:
#     print("No send file supplied, quitting.")
#     quit()

#with open(sys.argv[1]) as jsonFile:
with open("output.json") as jsonFile:
     inputList = json.load(jsonFile)

#Function to strip HTML tags, used later
def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext.strip()

#Email details:
sender = "Vowley Racing <address@domain>"
subject = "REVISED: Booking Confirmation for Vowley Races 2020"

#Credentials. Should probably make these safe somewhere...
username = "address@domain"
password = "password"
mailServer = "outlook.office365.com"

#open the email template file
file = open("ticket_email_template.html", "r")
emailTemplate = file.read()
file.close()

#We're then going to iterate through the list of coupons we created and send them to each person. First we need to collect the relevant data together.

for recipient in inputList:
    
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender

    message["To"] = recipient['email']

    #the replace() function is to replace the relevant bit of the template ($$NAME$$) with our data. I couldn't get f-strings to behave - {example}

    #The proper version will be HTML
    name = recipient['prefix'] + " " + recipient['firstname'] + " " + recipient['lastname']
    bodyText = emailTemplate.replace("###NAME###", name)

    bodyText = bodyText.replace("###TOTAL###", recipient['payment-made'])

    if (recipient['lunch-26th'] == "yes" and recipient['lunch-27th'] == "yes"):
        lunch = "<span class=\"label\">Lunch:</span> 26th & 27th"
    elif recipient['lunch-26th'] == "yes":
        lunch = "<span class=\"label\">Lunch:</span> 26th"
    elif recipient['lunch-27th'] == "yes":
        lunch = "<span class=\"label\">Lunch:</span> 27th"
    else:
        lunch = "<span class=\"label\">Lunch:</span> No lunch requested"

    if recipient['barbecue'] == "yes":
        bbq = "<span class=\"label\">BBQ:</span> Barbecue on Saturday 26th"
    else:
        bbq = "<span class=\"label\">BBQ:</span> No barbecue"

    if len(recipient['dietary-requirements']) > 0:
        dietaryRequirements = "<span class=\"label\">Dietary requirements:</span> " + recipient['dietary-requirements']
    else:
        dietaryRequirements = "<span class=\"label\">Dietary requirements:</span> No dietary requirements specified"

    bodyText = bodyText.replace("###LUNCH###", lunch)
    bodyText = bodyText.replace("###BBQ###", bbq)
    
    if recipient['lunch-26th'] != "yes" and recipient['lunch-27th'] != "yes" and recipient['barbecue'] != "yes":
        #No food ordered so no need to show dietary requirements, replace it with nothing
        bodyText = bodyText.replace("###DIETARY-REQUIREMENTS###", "")
    else:
        bodyText = bodyText.replace("###DIETARY-REQUIREMENTS###", dietaryRequirements)

    #Additionals go here
    if len(recipient['additionals']) > 0:
        additionalsInfo = "<div class=\"additionals\"><span class=\"label\">Additional guests:</span>"
        for partyMember in recipient['additionals']:
            partyMemberInfo = ""
            if (partyMember['lunch-26th'] == "yes" and partyMember['lunch-27th'] == "yes"):
                lunch = "<span class=\"label\">Lunch:</span> 26th & 27th"
            elif partyMember['lunch-26th'] == "yes":
                lunch = "<span class=\"label\">Lunch:</span> 26th"
            elif partyMember['lunch-27th'] == "yes":
                lunch = "<span class=\"label\">Lunch:</span> 27th"
            else:
                lunch = "<span class=\"label\">Lunch:</span> No lunch requested"

            if partyMember['barbecue'] == "yes":
                bbq = "<span class=\"label\">BBQ:</span> Barbecue on Saturday 26th"
            else:
                bbq = "<span class=\"label\">BBQ:</span> No barbecue"

            if len(partyMember['dietary-requirements']) > 0:
                dietaryRequirements = "<span class=\"label\">Dietary requirements:</span> " + partyMember['dietary-requirements']
            else:
                dietaryRequirements = "<span class=\"label\">Dietary requirements:</span> No dietary requirements specified"

            partyMemberInfo = "<p>" + partyMember['prefix'] + " " + partyMember['firstname'] + " " + partyMember['lastname'] + "</p>"
            partyMemberInfo = partyMemberInfo + "<p>" + lunch + "</p><p>" + bbq + "</p><p>" + dietaryRequirements + "</p>"
            additionalsInfo = additionalsInfo + partyMemberInfo

        additionalsInfo = additionalsInfo + "</div>"
    else:
        additionalsInfo = ""

    bodyText = bodyText.replace("###ADDITIONALS###", additionalsInfo)


    #Falcon info:
    
    if len(recipient['falcon-ids']) > 0:
        #var_dump(recipient['falcons'])
        falconInfo = "<span class=\"label\">Falcon information:</span><br/>" + str(len(recipient['falcon-ids'])) + " falcons entered"
        flatRaceCount = 0
        huntRaceCount = 0
        falconAccommodation = []
        tmpFalconAccommodation = ""
        for falcon in recipient['falcons']:
            if falcon['flat-race'] == "Yes":
                flatRaceCount+=1
            if falcon['hunt-race'] == "Yes":
                huntRaceCount+=1
            if falcon['thursday-mews'] == "Yes" or falcon['friday-mews'] == "Yes" or falcon['saturday-mews'] == "Yes" or falcon['sunday-mews'] == "Yes":
                #This falcon will be staying for at least one day:
                tmpFalconAccommodation = "Accommodation booked for " + falcon['name'] + " on the following days: "
                if falcon['thursday-mews'] == "Yes":
                    tmpFalconAccommodation = tmpFalconAccommodation + " Thursday"
                if falcon['friday-mews'] == "Yes":
                    tmpFalconAccommodation = tmpFalconAccommodation + " Friday"
                if falcon['saturday-mews'] == "Yes":
                    tmpFalconAccommodation = tmpFalconAccommodation + " Saturday"
                if falcon['sunday-mews'] == "Yes":
                    tmpFalconAccommodation = tmpFalconAccommodation + " Sunday"
            else:
                tmpFalconAccommodation = "No accommodation booked for " + falcon['name']

            falconAccommodation.append(tmpFalconAccommodation)

        if flatRaceCount > 1:
            flatRaceInfo = str(flatRaceCount) + " flat race entries, "
        else:
            flatRaceInfo = str(flatRaceCount) + " flat race entry, "

        if huntRaceCount > 1:
            huntRaceInfo = str(huntRaceCount) + " hunt race entries"
        else:
            huntRaceInfo = str(huntRaceCount) + " hunt race entry"

        falconInfo = falconInfo + ", " + flatRaceInfo + huntRaceInfo + "<br/>"

        falconAccommodationInfo = "<span class=\"label\">Falcon accommodation:</span><br/>"
        for falconEntry in falconAccommodation:
            falconAccommodationInfo = falconAccommodationInfo + falconEntry + "<br/>"
    else:
        falconInfo = ""
        falconAccommodationInfo = ""

    bodyText = bodyText.replace("###FALCON-INFO###", (falconInfo + "<br/>"))
    bodyText = bodyText.replace("###FALCON-ACCOMMODATION###", (falconAccommodationInfo))

    #In the unlikely event that any nutter doesn't do HTML email we'll offer the plaintext:
    # simpleBodyText = cleanhtml(emailTemplate.replace("$$NAME$$", name))
    # simpleBodyText = simpleBodyText.replace("$$EMAIL$$", recipient['email'])

    #sort out MIME type, whatever that is:
    #simpleBody = MIMEText(simpleBodyText, "plain")
    htmlBody = MIMEText(bodyText, "html")

    #Attach the two body texts to the message object
    #message.attach(simpleBody)
    message.attach(htmlBody)

    #  if len(falconInfo) > 0:
    #      var_dump(bodyText)
    # if recipient['id'] == "563":
    #     print(bodyText)

    #Send that to the mail server!
    server = smtplib.SMTP(mailServer, 587)
    server.starttls()
    server.login(username, password)
    server.sendmail(sender, recipient['email'], message.as_string())
    server.quit()
