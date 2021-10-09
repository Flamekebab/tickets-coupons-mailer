#!/usr/bin/env python3
from woocommerce import API
import json
import sys
from var_dump import var_dump
from datetime import datetime
from dateutil.parser import parse
#Important limitation at present - only 100 coupons checked.

#We're going to check the created_coupons.txt by date so that we get them all - just not all ALL of them
with open('created_coupons.txt') as json_file:
    jsonData = json.load(json_file)

wcapi = API(
    url="https://www.DOMAIN.com",
    consumer_key="key",
    consumer_secret="secret",
    wp_api=True,
    version="wc/v3"
)
#We'll need to compare dates
today = datetime.now()

#We can use parse to turn a string into a date and then compare them as follows:
# exampleDate = parse("2020-06-04T12:31:21")
# diff = today - exampleDate
# print(diff.days)

#Grab a list of existing coupons from the API:
existingCoupons = wcapi.get("coupons", params={"per_page": 100}).json()
#AND THE REST
extraCoupons = wcapi.get("coupons", params={"per_page": 100, "page": 2}).json()
existingCoupons = existingCoupons + extraCoupons

#We're going to check the existing coupons against our JSON data file
#Then we'll build a list of codes that are fresh and need to be emailed out
freshCouponIDs = []

#Work our way through our JSON data:
# for jsonEntry in jsonData:
for existingCode in existingCoupons:
    #We now see how old the code is and if it's more than a day old (i.e. it was created before just now) then we don't bother with it
    couponDate = parse(existingCode['date_created_gmt'])
    dayDifference = today - couponDate
    if dayDifference.days < 1:
        #This code was created today!
        freshCouponIDs.append(existingCode['id'])
        # print(existingCode['code'] + "is old (" + existingCode['date_created_gmt'][0:10:1] +")" )
    # else:
        # print(existingCode['code'] + "is FRESH (" + existingCode['date_created_gmt'][0:10:1] +")" )

#We now have a list of freshly created coupon IDs. We don't have any other details about them but we can ask the API for details and compare.
#var_dump(freshCouponIDs)

freshCoupons = []

for couponID in freshCouponIDs:
    #Grab that coupons details from the API (it returns a dictionary)
    couponDetails = wcapi.get("coupons/" + str(couponID)).json()
    #Let's iterate through the data we have in created_coupons.txt
    for jsonEntry in jsonData:
        #the JSON data has case sensitive stuff - we need to ditch that for the comparison
        if couponDetails['code'] == jsonEntry['coupon_code'].lower():
            freshCoupons.append(jsonEntry)

#freshCoupons is now JSON, just like created_coupons.txt except only new coupons
#var_dump(freshCoupons)

#Output that to fresh_coupons.txt
with open('fresh_coupons.txt', 'w') as outfile:
    json.dump(freshCoupons, outfile)
