#!/usr/bin/python3
import datetime
from datetime import date, datetime
from datetime import timedelta
import time
import os
import json
import jwt
import sys

###################################################

only_retrieve_clubapp_id = False # Set to True to retrieve your clubapp ID, then set to False again
dryrun = False # Only check available time slots, but don't make a reservation. False by default

email_address = "" # Your email address
password = "" # Your password in plain-text

your_clubapp_id = "" # Your own clubapp ID
friend1_clubapp_id = "" # Clubapp ID of friend who you are reserving the court with
friend2_clubapp_id = "" # idem
friend3_clubapp_id = "" # idem, if you have this many friends

reservation_date = "2021-01-25" # Specify the date to make the reservation (yyyy-mm-dd)

first_choice_first_hour = "08:30" # Either specify a time or None (hh:mm)
first_choice_second_hour = "09:30" # Either specify a time or None (hh:mm)
first_choice_courts = ["Baan 1", "Baan 2", "Baan 3", "Baan 4"] # Either specify courts ("Baan X", where X is the court number) or []

second_choice_first_hour = "08:00" # Either specify a time or None (hh:mm)
second_choice_second_hour = None # Either specify a time or None (hh:mm)
second_choice_courts = [] # Either specify courts ("Baan X", where X is the court number) or []

###################################################
##### DO NOT CHANGE ANY LINES BELOW THIS LINE #####
###################################################

lines_to_tail = "10"

def find_time_slot(available_slots, first_hour, second_hour=None, courts=[]):
    previous_slot_available_and_matches = False
    second_time_slot_found = False
    first_time_slot_found = False

    # Sanity checks
    if (len(available_slots) < 1):
        print(" - No slots available")
        return 0, False, False
    if (first_hour is None):
        print(" - First hour is None. Skip")
        return 0, False, False

    # Loop through all available slots to find a match
    for slot in available_slots:
        court_name = slot[0]
        time_slot = slot[1][11:16]
        md5slotkey = slot[2]

        # Compensate for difference between local time and server time
        time_slot = format(datetime.strptime(time_slot, '%H:%M') + timedelta(hours=+1), '%H:%M')

        # If we already found the first hour, check if this time slot also matches the second hour
        if (previous_slot_available_and_matches == True) and (second_hour == time_slot):
            # Yay! A court is available! Check if desired court matches
            if (check_court(courts, court_name) == True):
                print(" - For the chosen time slot the first hour " + first_hour + " and second hour " + second_hour + " are available on " + court_name + " (" + md5slotkey + ")")
                second_time_slot_found = md5slotkey
                break

        # Check if this time slot matches the first hour
        if (first_hour == time_slot):
            # A court (for at least the first hour) is available! Check if desired court matches
            if (check_court(courts, court_name) == True):
                first_time_slot_found = md5slotkey
                # Did the user specify a second hour?
                if (second_hour == None):
                    print(" - For the chosen time slot the first hour " + first_hour + " is available on " + court_name + " (" + md5slotkey + ")")
                    break
                else:
                    # Yes, they did. So continue searching...
                    previous_slot_available_and_matches = True
                    print(" - At least time slot " + first_hour + " is available on " + court_name + " (" + md5slotkey + ")")

    if (second_time_slot_found != False):
        # Reserve both time slot
        return 2, first_time_slot_found, second_time_slot_found
    
    if (first_time_slot_found != False):
        # Reserve single time slot. Both time slots were not available
        return 1, first_time_slot_found, False

    # Unfortunately, no matching time slots were found
    print(" - None found")
    return 0, False, False


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

def make_reservation(bearer_token, date_tomorrow, md5slotkey, your_clubapp_id, friends_clubapp_ids):
    time.sleep(1) # Lets not stress the server too much
    make_reservation_tomorrow_cli_cmd = "curl -i -s -k -X $'GET' \
        -H $'Host: api.socie.nl' -H $'AppBundle: nl.tizin.socie.tennis' -H $'Accept: application/json' -H $'Authorization: bearer " + bearer_token + "' -H $'appVersion: 3.11.0' -H $'Accept-Language: en-us' -H $'Cache-Control: no-cache' -H $'Platform: iOS' -H $'membership_id: 5d635eee1ea4c97b221c58fc' -H $'Language: en-NL' -H $'Accept-Encoding: gzip, deflate' -H $'User-Agent: ClubApp/237 CFNetwork/1209 Darwin/20.2.0' -H $'Connection: close' -H $'Content-Type: application/json' \
        -b $'AWSELB=" + awselb_cookie + "; AWSELBCORS=" + awselbcors_cookie + "' \
        $'https://api.socie.nl/communities/5a250a75d186db12a00f1def/tennis_court_reservation_create?date=" + str(date_tomorrow) + "&md5slotkey=" + md5slotkey + "&externalReferences=" + your_clubapp_id + "," + friends_clubapp_ids + ",' 2>&1 | tee AutoTenezOutputReservation.txt"

    output = os.popen(make_reservation_tomorrow_cli_cmd).read()
    # A reponse with no content is returned if the reservation was successful
    valid_output = "HTTP/1.1 204 No Content"
    if (output.find(valid_output) == 0):
        print("Successfully made the reservation! With md5slotkey " + md5slotkey)
    else:
        print("Failed to make the reservation with md5slotkey " + md5slotkey)

###############

# Sanity checks
if (not email_address) or (not password):
    print("ERROR! Enter your email address and password")
    sys.exit(0)

if (only_retrieve_clubapp_id == False) and ((not your_clubapp_id) or (not friend1_clubapp_id)):
    print("ERROR! Fill out the Clubapp IDs")
    sys.exit(0)

# Exit script if tomorrow is not the chosen date yet, so wait to make the reservation
date_tomorrow = date.today() + timedelta(days=1)
if (only_retrieve_clubapp_id == False) and (str(date_tomorrow) != reservation_date):
    print("INFO! Chosen date (" + reservation_date + ") is not yet tomorrow ("+ str(date_tomorrow) +").")
    sys.exit(0)

# Prepare friends clubadd IDs to send with some of the requests
if (friend1_clubapp_id and friend2_clubapp_id and friend3_clubapp_id):
    friends_clubapp_ids = friend1_clubapp_id + "," + friend2_clubapp_id + "," + friend3_clubapp_id
elif (friend1_clubapp_id and friend2_clubapp_id):
    friends_clubapp_ids = friend1_clubapp_id + "," + friend2_clubapp_id
else:
    # It's anyway only possible to reserve a court with at least 2 people or more
    friends_clubapp_ids = friend1_clubapp_id

# Retrieve the cookies first. They are apparently necessary to perform a valid request to the server
try:
    retrieve_cookies_cli_cmd = "curl -i -s -k -X $'GET' \
        -H $'Host: api.socie.nl' -H $'AppBundle: nl.tizin.socie.tennis' -H $'Accept: application/json' -H $'appVersion: 3.11.0' -H $'Accept-Language: en-us' -H $'Cache-Control: no-cache' -H $'Platform: iOS' -H $'Accept-Encoding: gzip, deflate' -H $'Language: en-NL' -H $'User-Agent: ClubApp/237 CFNetwork/1209 Darwin/20.2.0' -H $'Connection: close' -H $'Content-Type: application/json' \
        $'https://api.socie.nl/public/ping'"

    output = os.popen(retrieve_cookies_cli_cmd).read()

    # Parse the cookies from the response
    # AWS ELB cookie
    begin_awselb_cookie = output.index("AWSELB=")
    end_awselb_cookie = begin_awselb_cookie + 138 # Cookie length is 138 characters
    awselb_cookie = output[begin_awselb_cookie:end_awselb_cookie]

    # The AWS ELB CORS cookie is probably the same, but just retrieve as well it to be sure
    begin_awselbcors_cookie = output.index("AWSELBCORS=")
    end_awselbcors_cookie = begin_awselbcors_cookie + 138 # Cookie length is 138 characters
    awselbcors_cookie = output[begin_awselbcors_cookie:end_awselbcors_cookie]

except ValueError as e:
    print("ERROR! Failed to retrieve the cookies. Could not parse the response")
    print(e)
    sys.exit(-1)

except Exception as e:
    print("ERROR! An unknown error occurred while trying to retrieve the cookies")
    print(e)
    sys.exit(-1)

# Logging you in
try:
    print("Logging in...")
    login_cli_cmd = "curl -i -s -k -X $'POST' \
        -H $'Host: api.socie.nl' -H $'AppBundle: nl.tizin.socie.tennis' -H $'Accept: application/json' -H $'appVersion: 3.11.0' -H $'Accept-Language: en-us' -H $'Cache-Control: no-cache' -H $'Platform: iOS' -H $'Accept-Encoding: gzip, deflate' -H $'Language: en-NL' -H $'Content-Length: 83' -H $'User-Agent: ClubApp/237 CFNetwork/1209 Darwin/20.2.0' -H $'Connection: close' -H $'Content-Type: application/json' \
        -b $'AWSELB=" + awselb_cookie + "; AWSELBCORS=" + awselbcors_cookie + "' \
        --data-binary $'{\"appType\":\"TENNIS\",\"email\":\""+ email_address + "\",\"password\":\"" + password + "\"}' \
        $'https://api.socie.nl/login/socie' > AutoTenezOutputLogin.txt"

    output = os.popen(login_cli_cmd).read()

    # Remove extranaeous headers
    tail_cli_cmd = "tail -n +" + lines_to_tail + " AutoTenezOutputLogin.txt > AutoTenezOutputLoginTailed.txt"
    output = os.popen(tail_cli_cmd).read()

    # Parse login JSON response
    with open('AutoTenezOutputLoginTailed.txt') as f:
        json_data = json.load(f)

    # Obtain bearer token from the JSON reponse
    bearer_token = json_data['access_token']

    # Save bearer token to file for later use
    f = open("AutoTenezOutputBearerToken.txt", "w")
    f.write(bearer_token)
    f.close()

# Catch JSONDecodeError
except ValueError as e: 
    print("ERRROR! Failed to parse the response. Please check the response in the log file. Note: stderr is not printed.")
    print(e)
    sys.exit(-1)

except Exception as e:
    print("ERROR! An unknown error occurred while logging in")
    print(e)
    sys.exit(-1)

try:
    if (only_retrieve_clubapp_id == True):
        print("Retrieving your clubapp ID...")
        # Retrieve user ID, so we can make another call to retrieve your external reference (i.e. clubapp ID)
        decoded = jwt.decode(bearer_token, options={"verify_signature": False})
        user_id = str(decoded)[166:190] # No comment...
        
        get_external_reference_cli_cmd = "curl -i -s -k -X $'GET' \
        -H $'Host: api.socie.nl' -H $'AppBundle: nl.tizin.socie.tennis' -H $'Accept: application/json' -H $'Authorization: bearer " + bearer_token + "' -H $'appVersion: 3.11.0' -H $'Accept-Language: en-us' -H $'Cache-Control: no-cache' -H $'Platform: iOS' -H $'Accept-Encoding: gzip, deflate' -H $'Language: en-NL' -H $'User-Agent: ClubApp/237 CFNetwork/1209 Darwin/20.2.0' -H $'Connection: close' -H $'Content-Type: application/json' \
        -b $'AWSELB=" + awselb_cookie + "; AWSELBCORS=" + awselbcors_cookie + "' \
        $'https://api.socie.nl/v2/me/communities/5a250a75d186db12a00f1def/memberships/" + user_id + "' > AutoTenezOutputGetExternalReference.txt"

        output = os.popen(get_external_reference_cli_cmd).read()

        # Remove extranaeous headers
        tail_cli_cmd = "tail -n +" + lines_to_tail + " AutoTenezOutputGetExternalReference.txt > AutoTenezOutputGetExternalReferenceTailed.txt"
        output = os.popen(tail_cli_cmd).read()

        # Parse JSON response
        with open('AutoTenezOutputGetExternalReferenceTailed.txt') as f:
            json_data = json.load(f)

        print("Your clubapp ID is:")
        print(json_data['extraFields']['externalReference'])
        sys.exit(0)

# Catch JSONDecodeError
except ValueError as e: 
    print("ERRROR! Failed to parse the response while retrieving your clubapp ID. Please check the response in the log file. Note: stderr is not printed.")
    print(e)
    sys.exit(-1)
   
except Exception as e:
    print("ERROR! An unknown error occurred while retrieving your clubapp ID")
    print(e)
    sys.exit(-1)

try:
    # Retrieve slots for tomorrow
    print("Retrieving time slots for tomorrow...")
    time.sleep(1) # Lets not stress the server too much
    get_slots_tomorrow_cli_cmd = "curl -i -s -k -X $'GET' \
        -H $'Host: api.socie.nl' -H $'AppBundle: nl.tizin.socie.tennis' -H $'Accept: application/json' -H $'Authorization: bearer " + bearer_token + "' -H $'appVersion: 3.11.0' -H $'Accept-Language: en-us' -H $'Cache-Control: no-cache' -H $'Platform: iOS' -H $'membership_id: 5d635eee1ea4c97b221c58fc' -H $'Language: en-NL' -H $'Accept-Encoding: gzip, deflate' -H $'User-Agent: ClubApp/237 CFNetwork/1209 Darwin/20.2.0' -H $'Connection: close' -H $'Content-Type: application/json' \
        -b $'AWSELB=" + awselb_cookie + "; AWSELBCORS=" + awselbcors_cookie + "' \
        $'https://api.socie.nl/v2/app/communities/5a250a75d186db12a00f1def/modules/5eb4720c8618e00287a3eff6/allunited_tennis_courts/slots?date=" + str(date_tomorrow) + "&externalReferences=" + your_clubapp_id + "," + friends_clubapp_ids + ",' > AutoTenezOutputSlots.txt"

    # Retrieve all available courts for tomorrow
    output = os.popen(get_slots_tomorrow_cli_cmd).read()

    # Remove extranaeous headers
    tail_cli_cmd = "tail -n +" + lines_to_tail + " AutoTenezOutputSlots.txt > AutoTenezOutputSlotsTailed.txt"
    output = os.popen(tail_cli_cmd).read()

    # Parse JSON response
    with open('AutoTenezOutputSlotsTailed.txt') as f:
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

# Catch JSONDecodeError
except ValueError as e: 
    print("ERRROR! Failed to parse the response while retrieving the available slots. Please check the response in the log file. Note: stderr is not printed.")
    print(e)
    sys.exit(-1)
   
except Exception as e:
    print("ERROR! An unknown error occurred while retrieving your clubapp ID")
    print(e)
    sys.exit(-1)

try:
    # Find available time slots
    print("Finding available time slots for your first choice...")
    first_choice_no_slots, first_choice_first_slotkey, first_choice_second_slotkey = find_time_slot(available_slots, first_choice_first_hour, first_choice_second_hour, first_choice_courts)
    print("Finding available time slots for your second choice...")
    second_choice_no_slots, second_choice_first_slotkey, second_choice_second_slotkey = find_time_slot(available_slots, second_choice_first_hour, second_choice_second_hour, second_choice_courts)

    first_md5slotkey = ""
    second_md5slotkey = ""

    # Reserve the biggest time slot
    if(second_choice_no_slots > first_choice_no_slots):
        print("Propagating second choice. Number of time slots: " + str(second_choice_no_slots))
        if (second_choice_first_slotkey):
            print(" - First time slot md5slotkey " + second_choice_first_slotkey)
            first_md5slotkey = second_choice_first_slotkey
        if (second_choice_second_slotkey):
            print(" - Second time slot md5slotkey " + second_choice_second_slotkey)
            second_md5slotkey = second_choice_second_slotkey
    elif(first_choice_first_slotkey != False):
        print("Propagating first choice. Number of time slots: " + str(first_choice_no_slots))
        if (first_choice_first_slotkey):
            print(" - First time slot md5slotkey " + first_choice_first_slotkey)
            first_md5slotkey = first_choice_first_slotkey
        if (first_choice_second_slotkey):
            print(" - Second time slot md5slotkey " + first_choice_second_slotkey)
            second_md5slotkey = first_choice_second_slotkey
    else:
        print("There are no time slots available")

except Exception as e:
    print("ERROR! An unknown error occurred while finding the best time slot")
    sys.exit(-1)

if (dryrun):
    print("Not making a reservation because dryrun is set to True")
    sys.exit(0)

try:
    if (first_md5slotkey):
        print("Make the reservation for the first time slot...")
        make_reservation(bearer_token, date_tomorrow, first_md5slotkey, your_clubapp_id, friends_clubapp_ids)

    if (second_md5slotkey):
        print("Make the reservation for the second time slot...")
        make_reservation(bearer_token, date_tomorrow, second_md5slotkey, your_clubapp_id, friends_clubapp_ids)

except Exception as e:
    print("ERROR! An unknown error occurred while making the reservation")
    sys.exit(-1)