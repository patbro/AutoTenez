#!/usr/bin/python3
from datetime import date
import datetime
import time
import os
import json
#import pyjwt

###################################################

email_address = "" # Your email address
password = "" # Your password in plain-text

your_clubapp_id = "" # Your own clubapp ID
friend_clubapp_id = "" # Clubapp ID of friend who you are reserving the court with

first_choice_first_hour = "08:30" 
first_choice_second_hour = "09:30" # Either specify a time or None
first_choice_courts = ["Baan 1", "Baan 2", "Baan 3", "Baan 4"]

second_choice_first_hour = "08:30"
second_choice_second_hour = None # Either specify a time or None
second_choice_courts = [] # Either specify courts or []

first_choice_preference = False # False: will find the longest available time slot. Might be the first or second choice.
                                # True:  will find the best firt option available. Might not be both time slots (so only one hour).

# Usually you don't have to mess with the cookies, rather than just eating them
cookies = "AWSELB=57C90D931ED7A0D581FA0FDCC1A541BAF664D2A7C6ADF011E1622185F3430930403132013A6DD48D61EC856130104D8A52983E53940E17D1F9E11CA9FA6416D564EE3AF294; AWSELBCORS=57C90D931ED7A0D581FA0FDCC1A541BAF664D2A7C6ADF011E1622185F3430930403132013A6DD48D61EC856130104D8A52983E53940E17D1F9E11CA9FA6416D564EE3AF294"

###################################################
##### DO NOT CHANGE ANY LINES BELOW THIS LINE #####
###################################################

def find_time_slot(available_slots, first_hour, second_hour=None, courts=[]):
    previous_slot_available_and_matches = False
    both_time_slots_found = False
    single_time_slot_found = False

    # Sanity checks
    if (len(available_slots) < 1):
        print("No slots available")
        return
    if (first_hour == None):
        print("First hour is invalid")
        return

    # Loop through all available slots to find a match
    for slot in available_slots:
        court_name = slot[0]
        time_slot = slot[1][11:16]
        md5slotkey = slot[2]

        # If we already found the first hour, check if this time slot also matches the second hour
        if (previous_slot_available_and_matches == True) and (second_hour == time_slot):
            # Yay! A court is available! Check if desired court matches
            if (check_court(courts, court_name) == True):
                print("Voor je gekozen tijdslot om " + first_hour + " en " + second_hour + " is " + court_name + " nog vrij met md5slotkey " + md5slotkey)
                both_time_slots_found = md5slotkey
                break

        # Check if this time slot matches the first hour
        if (first_hour == time_slot):
            # A court (for at least the first hour) is available! Check if desired court matches
            if (check_court(courts, court_name) == True):
                single_time_slot_found = md5slotkey
                # Did the user specify a second hour?
                if (second_hour == None):
                    print("Voor je gekozen tijdslot om " + first_hour + " is " + court_name + " nog vrij met md5slotkey " + md5slotkey)
                    break
                else:
                    # Yes, they did. So continue searching...
                    previous_slot_available_and_matches = True

    if (both_time_slots_found != False):
        # Reserve both time slot
        return 2, both_time_slots_found
    
    if (single_time_slot_found != False):
        # Reserve single time slot. Both time slots were not available
        return 1, single_time_slot_found

    # Unfortunately, no matching time slots were found
    return 0, False


def check_court(courts, court_name):
    # Did the user limit their search to certain courts?
    if (len(courts) > 0):
        # Yes. Check if the current court matches one of the user defined courts
        for court in courts:
            if (court == court_name):
                return True
    else:
        # Nope
        return True

    return False

#try:
#    print("Attempt to retrieve bearer token from file")
#    f = open("makeTennisReservationBearerToken.txt", "r")
#    bearer_token = f.readlines()
#    f.close()
#
#    decoded = jwt.decode(bearer_token, algorithms=["RS256"])
#    print(decoded)
#
#    raise Exception("Bearer token expired")
#except:
#    print("Failed to retrieve bearer token from file")

# First of all, login 
login_cli_cmd = "curl -i -s -k -X $'POST' \
    -H $'Host: api.socie.nl' -H $'AppBundle: nl.tizin.socie.tennis' -H $'Accept: application/json' -H $'appVersion: 3.11.0' -H $'Accept-Language: en-us' -H $'Cache-Control: no-cache' -H $'Platform: iOS' -H $'Accept-Encoding: gzip, deflate' -H $'Language: en-NL' -H $'Content-Length: 83' -H $'User-Agent: ClubApp/237 CFNetwork/1209 Darwin/20.2.0' -H $'Connection: close' -H $'Content-Type: application/json' \
    -b $'AWSELB=57C90D931ED7A0D581FA0FDCC1A541BAF664D2A7C6ADF011E1622185F3430930403132013A6DD48D61EC856130104D8A52983E53940E17D1F9E11CA9FA6416D564EE3AF294; AWSELBCORS=57C90D931ED7A0D581FA0FDCC1A541BAF664D2A7C6ADF011E1622185F3430930403132013A6DD48D61EC856130104D8A52983E53940E17D1F9E11CA9FA6416D564EE3AF294' \
    --data-binary $'{\"appType\":\"TENNIS\",\"email\":\""+ email_address + "\",\"password\":\"" + password + "\"}' \
    $'https://api.socie.nl/login/socie' > AutoTenezOutputLogin.txt"

output = os.popen(login_cli_cmd).read()

# Remove extranaeous headers
tail_cli_cmd = "tail -n +8 AutoTenezOutputLogin.txt > AutoTenezOutputLogin.txt"
output = os.popen(tail_cli_cmd).read()

# Parse login JSON response
with open('AutoTenezOutputLogin.txt') as f:
    json_data = json.load(f)

# Obtain bearer token from the JSON reponse
bearer_token = json_data['access_token']

f = open("AutoTenezOutputBearerToken.txt", "w")
f.write(bearer_token)
f.close()

# Retireve slots for tomorrow
date_tomorrow = date.today() + datetime.timedelta(days=1)
# Prepare request to perform
get_slots_tomorrow_cli_cmd = "curl -i -s -k -X $'GET' \
    -H $'Host: api.socie.nl' -H $'AppBundle: nl.tizin.socie.tennis' -H $'Accept: application/json' -H $'Authorization: bearer " + bearer_token + "' -H $'appVersion: 3.11.0' -H $'Accept-Language: en-us' -H $'Cache-Control: no-cache' -H $'Platform: iOS' -H $'membership_id: 5d635eee1ea4c97b221c58fc' -H $'Language: en-NL' -H $'Accept-Encoding: gzip, deflate' -H $'User-Agent: ClubApp/237 CFNetwork/1209 Darwin/20.2.0' -H $'Connection: close' -H $'Content-Type: application/json' \
    -b $'AWSELB=57C90D931ED7A0D581FA0FDCC1A541BAF664D2A7C6ADF011E1622185F3430930403132013A6DD48D61EC856130104D8A52983E53940E17D1F9E11CA9FA6416D564EE3AF294; AWSELBCORS=57C90D931ED7A0D581FA0FDCC1A541BAF664D2A7C6ADF011E1622185F3430930403132013A6DD48D61EC856130104D8A52983E53940E17D1F9E11CA9FA6416D564EE3AF294' \
    $'https://api.socie.nl/v2/app/communities/5a250a75d186db12a00f1def/modules/5eb4720c8618e00287a3eff6/allunited_tennis_courts/slots?date=" + str(date_tomorrow) + "&externalReferences=" + your_clubapp_id + "," + friend_clubapp_id + ",' > AutoTenezOutputSlots.txt"

# Retrieve all available courts for tomorrow
output = os.popen(get_slots_tomorrow_cli_cmd).read()

# Remove extranaeous headers
tail_cli_cmd = "tail -n +8 AutoTenezOutputSlots.txt > AutoTenezOutputSlots.txt"
output = os.popen(tail_cli_cmd).read()

# Parse JSON response
with open('AutoTenezOutputSlots.txt') as f:
    json_data = json.load(f)

available_slots = []
# Loop through all courts: 0 - 12 in our case
for court_no in range(0, 12):
    slots = json_data['locations'][court_no]['slots']
    # Every time slot has slots
    for slot in slots:
        # Only the courts which are available to reserve, have slot keys. Makes life easy for us
        slot_keys = slot['slotKeys']
        for key in slot_keys:
            slot = []
            slot.append(key['courtName'])
            slot.append(key['beginDate'])
            slot.append(key['md5slotkey'])
            available_slots.append(slot)

# Find available time slots
first_choice_no_slots, first_choice_slotkey = find_time_slot(available_slots, first_choice_first_hour, first_choice_second_hour, first_choice_courts)
second_choice_no_slots, second_choice_slotkey = find_time_slot(available_slots, second_choice_first_hour, second_choice_second_hour, second_choice_courts)

md5slotkey = ""
if (first_choice_preference == True):
    # No matter how big the time slot is, reserve the first choice
    if (first_choice_slotkey != False):
        print("Reserveer eerste keuze: aantal sloten " + str(first_choice_no_slots) + " - " + first_choice_slotkey)
        md5slotkey = first_choice_slotkey
    elif(second_choice_slotkey != False):
        print("Reserveer tweede keuze: aantal sloten " + str(second_choice_no_slots) + " - " + second_choice_slotkey)
        md5slotkey = second_choice_slotkey
    else:
        print("Geen tijds sloten beschikbaar")
else:
    # Reserve the biggest time slot
    if(second_choice_no_slots > first_choice_no_slots):
        print("Reserveer tweede keuze: aantal sloten " + str(second_choice_no_slots) + " - " + second_choice_slotkey)
        md5slotkey = second_choice_slotkey
    elif(first_choice_slotkey != False):
        print("Reserveer eerste keuze: aantal sloten " + str(first_choice_no_slots) + " - " + first_choice_slotkey)
        md5slotkey = first_choice_slotkey
    else:
        print("Geen tijds sloten beschikbaar")

if (md5slotkey):
    make_reservation_tomorrow_cli_cmd = "curl -i -s -k -X $'GET' \
        -H $'Host: api.socie.nl' -H $'AppBundle: nl.tizin.socie.tennis' -H $'Accept: application/json' -H $'Authorization: bearer " + bearer_token + "' -H $'appVersion: 3.11.0' -H $'Accept-Language: en-us' -H $'Cache-Control: no-cache' -H $'Platform: iOS' -H $'membership_id: 5d635eee1ea4c97b221c58fc' -H $'Language: en-NL' -H $'Accept-Encoding: gzip, deflate' -H $'User-Agent: ClubApp/237 CFNetwork/1209 Darwin/20.2.0' -H $'Connection: close' -H $'Content-Type: application/json' \
        -b $'" + cookies + "' \
        $'https://api.socie.nl/communities/5a250a75d186db12a00f1def/tennis_court_reservation_create?date=" + str(date_tomorrow) + "&md5slotkey=" + md5slotkey + "&externalReferences=" + your_clubapp_id + "," + friend_clubapp_id + ",' 2>&1 | tee AutoTenezOutputReservation.txt"

    output = os.popen(make_reservation_tomorrow_cli_cmd).read()
    valid_output = "HTTP/1.1 204 No Content"

    if (output.find(valid_output) == 0):
        print("Reservering geplaatst!")
    else:
        print("Het is niet gelukt te reserveren")