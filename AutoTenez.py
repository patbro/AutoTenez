#!/usr/bin/python3
import datetime
from datetime import date, datetime
from datetime import timedelta
import time
import os
import json
import jwt
import sys
import requests

###################################################

email_address = "" # Your email address
password = "" # Your password in plain-text

only_retrieve_your_external_reference = False # Set to True to retrieve your external reference to share with a friend
dryrun = False # Only check available time slots, but don't make a reservation. False by default

player2_external_reference = "" # External reference of friend who you are reserving the court with
player3_external_reference = "" # Idem
player4_external_reference = "" # Idem. If you have this many friends

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

def find_time_slot(available_slots, first_hour, second_hour=None, courts=[]):
    previous_slot_available_and_matches = False
    second_time_slot_found = False
    first_time_slot_found = False
    first_court_first_time_slot_found = False

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

                # Additional variable to save first court where the first time slot is available,
                # if no second time slot would be found, the last court would be returned instead of the first one.
                if (first_court_first_time_slot_found == False):
                    first_court_first_time_slot_found = md5slotkey
                
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
        # Return the first available court instead of the last one
        if (second_hour is not None):
            first_time_slot_found = first_court_first_time_slot_found

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

def make_reservation(headers, cookies, date_tomorrow, md5slotkey, your_external_reference, other_players_external_references):
    time.sleep(1) # Lets not stress the server too much

    # Also here the community ID is hardcoded
    r = requests.get("https://api.socie.nl/communities/5a250a75d186db12a00f1def/tennis_court_reservation_create?date=" \
        + str(date_tomorrow) + "&md5slotkey=" + md5slotkey + "&externalReferences=" + your_external_reference + "," + other_players_external_references, \
        headers=headers, cookies=cookies)
    
    # We expect a status code 204 No Content, with of course no content
    if (r.status_code == 204) and (len(r.content) == 0):
        print("Successfully made the reservation! With md5slotkey " + md5slotkey)
    else:
        print("Failed to make the reservation with md5slotkey " + md5slotkey + ". Server returned status code: " + r.status_code())

###############

# Sanity checks
if (not email_address) or (not password):
    print("ERROR! Enter your email address and password")
    sys.exit(0)

if (only_retrieve_your_external_reference == False) and (not player2_external_reference):
    print("ERROR! Fill out the external reference of at least one other player")
    sys.exit(0)

# Exit script if tomorrow is not the chosen date yet, so wait to make the reservation
date_tomorrow = date.today() + timedelta(days=1)
if (only_retrieve_your_external_reference == False) and (str(date_tomorrow) != reservation_date):
    print("INFO! Chosen date (" + reservation_date + ") is not yet tomorrow ("+ str(date_tomorrow) +").")
    sys.exit(0)

# Prepare other player's external references to send with some of the requests
if (player2_external_reference and player3_external_reference and player4_external_reference):
    other_players_external_references = player2_external_reference + "," + player3_external_reference + "," + player4_external_reference
elif (player2_external_reference and player3_external_reference):
    other_players_external_references = player2_external_reference + "," + player3_external_reference
else:
    # It's anyway only possible to reserve a court with at least 2 people or more
    other_players_external_references = player2_external_reference

try:
    headers = {
        "Host": "api.socie.nl",
        "AppBundle": "nl.tizin.socie.tennis",
        "Accept": "application/json",
        "appVersion": "3.11.0",
        "Accept-Language": "en-us",
        "Cache-Control": "no-cache",
        "PLatform": "iOS",
        "Accept-Encoding": "gzip, deflate",
        "Language": "en-NL",
        "User-AGent": "ClubApp/237 CFNetwork/1209 Darwin/20.2.0",
        "Connection": "close",
        "Content-Type": "application/json",
    }
    r = requests.get("https://api.socie.nl/public/pling", headers=headers)
    cookies = r.cookies

except ValueError as e:
    print("ERROR! Failed to retrieve the cookies. Could not parse the response")
    print(e)
    sys.exit(-1)

except Exception as e:
    print("ERROR! An unexpected error occurred while trying to retrieve the cookies")
    print(e)
    sys.exit(-1)

# Logging you in
try:
    print("Logging in as " + email_address + "...")
    payload = {
        "appType": "TENNIS",
        "email": email_address,
        "password": password,
    }

    r = requests.post("https://api.socie.nl/login/socie", json=payload, headers=headers, cookies=cookies)
    response = r.json()
    # Obtain bearer token from the JSON reponse
    bearer_token = response['access_token']
    # Add bearer token to all future requests
    headers['Authorization'] = "bearer " + bearer_token

# Catch JSONDecodeError
except ValueError as e: 
    print("ERRROR! Failed to parse the response")
    print(e)
    sys.exit(-1)

except Exception as e:
    print("ERROR! An unexpected error occurred while logging in")
    print(e)
    sys.exit(-1)

try:
    print("Retrieving necessary IDs...")
    # Retrieve membership ID, which is included in the bearer token, so we can make another call to retrieve your external reference
    decoded = jwt.decode(bearer_token, options={"verify_signature": False})
    # Loop through all roles. Which is usually just one role
    for role in decoded['roles']:
        role_hash = role
    
    # When we found the role hash, we can loop through the next list, of which the key is the user ID
    for membership_hash in decoded['roles'][role_hash]:
        membership_id = membership_hash

    # Add membership ID to all future requests
    headers['membership_id'] = membership_id

    # Community ID is hardcoded because it is always the same for this case
    r = requests.get("https://api.socie.nl/v2/me/communities/5a250a75d186db12a00f1def/memberships/" + membership_id, headers=headers, cookies=cookies)
    response = r.json()
    # Then, your external reference ID will be burried in the response.
    your_external_reference = response['extraFields']['externalReference']
    print(" - Your external reference is: " + response['extraFields']['externalReference'])
    if (only_retrieve_your_external_reference == True):
        sys.exit(0)

    print(" - Your membership ID is: " + membership_id)
    
# Catch JSONDecodeError
except ValueError as e: 
    print("ERRROR! Failed to parse the response while retrieving the necessary IDs")
    print(e)
    sys.exit(-1)
   
except Exception as e:
    print("ERROR! An unexpected error occurred while retrieving the necessary IDs")
    print(e)
    sys.exit(-1)

try:
    # Retrieve slots for tomorrow
    print("Retrieving time slots for tomorrow...")
    time.sleep(1) # Lets not stress the server too much

    r = requests.get("https://api.socie.nl/v2/app/communities/5a250a75d186db12a00f1def/modules/5eb4720c8618e00287a3eff6/allunited_tennis_courts/slots?date=" \
            + str(date_tomorrow) + "&externalReferences=" + membership_id + "," + other_players_external_references, headers=headers, cookies=cookies)
    response = r.json()

    available_slots = []
    # Loop through all courts: 0 to 12 in our case
    for court_no in range(0, 13):
        slots = response['locations'][court_no]['slots']
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
    print("ERRROR! Failed to parse the response while retrieving the available slots")
    print(e)
    sys.exit(-1)
   
except Exception as e:
    print("ERROR! An unexpected error occurred while retrieving the available slots")
    print(e)
    sys.exit(-1)

try:
    # Find available time slots
    print("Finding available time slots for your first choice...")
    first_choice_no_slots, first_choice_first_slotkey, first_choice_second_slotkey = \
        find_time_slot(available_slots, first_choice_first_hour, first_choice_second_hour, first_choice_courts)
    
    print("Finding available time slots for your second choice...")
    second_choice_no_slots, second_choice_first_slotkey, second_choice_second_slotkey = \
        find_time_slot(available_slots, second_choice_first_hour, second_choice_second_hour, second_choice_courts)

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
        sys.exit(0)

except Exception as e:
    print("ERROR! An unexpected error occurred while finding the best time slot")
    sys.exit(-1)

if (dryrun):
    print("Not making a reservation because dryrun is set to True")
    sys.exit(0)

try:
    if (first_md5slotkey):
        print("Make the reservation for the first time slot...")
        make_reservation(headers, cookies, date_tomorrow, first_md5slotkey, your_external_reference, other_players_external_references)

    if (second_md5slotkey):
        print("Make the reservation for the second time slot...")
        make_reservation(headers, cookies, date_tomorrow, second_md5slotkey, your_external_reference, other_players_external_references)

except Exception as e:
    print("ERROR! An unexpected error occurred while making the reservation")
    print(e)
    sys.exit(-1)