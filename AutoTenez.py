#!/usr/bin/python3
import datetime
from datetime import date, datetime, timezone
from datetime import timedelta
import time
import os
import json
import jwt
import sys
import requests
import argparse

class AutoTenezException(Exception):
    """Base class for AutoTenez exceptions"""
    pass

class ParsingResponseFailed(AutoTenezException):
    def __init__(self, status_code, headers, content, original_exception, message="An unknown error occurred. Could not parse the response."):
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.exception = original_exception
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"""{self.message} -> {self.exception} \r\nStatus code: {self.status_code} \r\nHeaders: {self.headers} \r\nContent: {self.content}"""

class AutoTenez:
    global limt_debug_output
    
    # Your details
    email_address = "" # Your email address
    password = "" # Your password in plain-text

    # AutoTenez settings
    possible_to_reserve = [0, 48] # Reservation limits. Define when it is possible to make a reservation, syntax: [<days>, <hours>]. E.g.: [0, 48] means 48 hours upfront. [1, 0] means 1 day upfront (so tomorrow).
    no_courts = 21 # The number of courts your club has
    only_retrieve_your_external_reference = False # Set to True to retrieve your external reference to share with a friend
    dryrun = False # Only check available time slots, but don't make a reservation. False by default
    limit_debug_output = False # Drastically limit what AutoTenez prints to stdout

    ### Internal AutoTenez variables ###
    if (possible_to_reserve[0] != 0):
        date_to_reserve = date.today() + timedelta(days=possible_to_reserve[0])
    else:
        date_to_reserve = (datetime.now() + timedelta(hours=possible_to_reserve[1])).strftime("%Y-%m-%d")

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

    def __init__(self, reservation_date, hour, player2_external_reference, player3_external_reference, player4_external_reference):
        print("Initializing AutoTenez at", datetime.now())
        # Set class' reservation date if specified
        if (reservation_date):
            self.reservation_date = reservation_date
            print("Reservation date has been set to", self.reservation_date)
        else:
            self.reservation_date = str(self.date_to_reserve)
            print("Reservation date has been set to latest reservation date possible (" + self.reservation_date + ")")

        # AutoTenez sanity checks
        if (not self.email_address) or (not self.password):
            raise AutoTenezException("Make sure to enter your email address and password")
        
        if (self.only_retrieve_your_external_reference == False) and (not player2_external_reference):
            raise AutoTenezException("Fill out the external reference of at least one other player")
        
        if (not hour):
            raise AutoTenezException("First hour of first choice has not been set")

        if (self.only_retrieve_your_external_reference == False):
            # Check if we already can make a reservation based on the restrictions set by the club
            if (self.possible_to_reserve[0] != 0 and self.possible_reserve[1] == 0):
                possible_reservation_date = date.today() + timedelta(days=self.possible_to_reserve[1])
                # Raise exception if the possible reservation date did not reach the chosen reservation date by the user
                if (possible_reservation_date < self.reservation_date):
                    raise AutoTenezException("Ultimately possible reservation date", possible_reservation_date, "did not yet reach reservation date", self.reservation_date)

            elif (self.possible_to_reserve[0] == 0 and self.possible_to_reserve[1] != 0):
                possible_reservation_datetime = datetime.now() + timedelta(hours=self.possible_to_reserve[1])
                # Raise exception if the chosen date and first hour is not within the given time delta as specified by the user
                if (datetime.strptime(self.reservation_date + " " + hour, "%Y-%m-%d %H:%M") > possible_reservation_datetime):
                    raise AutoTenezException("Chosen date and first hour is not yet within " + str(self.possible_to_reserve[1]) + " hours")
                
            else:
                raise AutoTenezException("Sorry! Not yet supported")

        # Prepare other player's external references to send with some of the requests
        self.other_players_external_references = player2_external_reference
        if (player3_external_reference):
            self.other_players_external_references += "," + player3_external_reference
        if (player4_external_reference):
            self.other_players_external_references +=  "," + player4_external_reference

        # Retrieve all necessary information
        self.retrieve_cookies() # Retrieve the necessary cookies (mainly just for AWS services)
        self.login()
        self.retrieve_necessary_ids() # Retrieve necessary IDs to perform reservations

    def retrieve_cookies(self):
        try:
            r = requests.get("https://api.socie.nl/public/pling", headers=self.headers)
            # Add cookies to all feature requests
            self.cookies = r.cookies

        except ValueError as e:
            raise ParsingResponseFailed(r.status_code, r.headers, r.text, e, "Failed to retrieve the cookies")

    def refresh_tokens(self):
        decoded = jwt.decode(self.bearer_token, options={"verify_signature": False})
        expiration_epoch = decoded['exp'] - 300 # Make sure the token does not expire soon
        
        if (datetime.now(timezone.utc) > datetime.fromtimestamp(expiration_epoch, timezone.utc)):
            print("Login token expires soon. Refreshing token now...")
            self.login()
        else:
            print("Login token is still valid")

    def login(self):
        try:
            if (self.limit_debug_output is False):
                print("Logging in as " + self.email_address + "...")

            payload = {
                "appType": "TENNIS",
                "email": self.email_address,
                "password": self.password,
            }

            r = requests.post("https://api.socie.nl/login/socie", json=payload, headers=self.headers, cookies=self.cookies)
            response = r.json()
            # Obtain bearer token from the JSON reponse (later used in `retrieve_necessary_ids`)
            self.bearer_token = response['access_token']
            # Add bearer token to all future requests
            self.headers['Authorization'] = "bearer " + self.bearer_token

        # Catch JSONDecodeError
        except ValueError as e:
            raise ParsingResponseFailed(r.status_code, r.headers, r.text, e, "Failed to retrieve your bearer token")

    def retrieve_necessary_ids(self):
        try:
            if (self.limit_debug_output is False):
                print("Retrieving necessary IDs...")

            # Retrieve membership ID, which is included in the bearer token, so we can make another call to retrieve your external reference
            decoded = jwt.decode(self.bearer_token, options={"verify_signature": False})
            # Bearer token example
            # {
            #    "sub": "Socie",
            #    "exp": 1613909087,
            #    "iat": 1613905487,
            #    "iss": "Socie",
            #    "aud": "Socie",
            #    "user_id": "<userId>",        # Alpha numeric string
            #    "roles": {
            #        "<communityId>": {        # Alpha numeric string
            #        "<externalReference>": [  # Alpha numeric string
            #            "user"
            #        ]
            #        }
            #    },
            #    "email": "<yourEmailAddress>",
            #    "platform": "iOS",
            #    "appType": "TENNIS"
            # }

            # Loop through all roles (=community ID). Which is usually just one role
            for role in decoded['roles']:
                self.community_id = role
                break # Break, in case user is member of multiple communities (this is not yet supported)
            
            # When we found the role hash, we can loop through the next list, of which the key is the user ID
            for membership_hash in decoded['roles'][self.community_id]:
                self.membership_id = membership_hash

            # Add membership ID to all future requests
            self.headers['membership_id'] = self.membership_id
            
            r = requests.get("https://api.socie.nl/v2/me/communities/" + self.community_id + "/memberships/" + self.membership_id, headers=self.headers, cookies=self.cookies)
            response = r.json()
            # Then, your external reference ID will be burried in the response.
            self.your_external_reference = response['extraFields']['externalReference']
            if (self.limit_debug_output is False):
                print(" - Your external reference is: " + response['extraFields']['externalReference'])

            if (self.only_retrieve_your_external_reference == True):
                sys.exit(0)

            if (self.limit_debug_output is False):
                print(" - Your membership ID is: " + self.membership_id)
                print(" - Your community ID is: " + self.community_id)

        # Catch JSONDecodeError
        except ValueError as e:
            raise ParsingResponseFailed(r.status_code, r.headers, r.text, e, "Failed to retrieve the necessary IDs")
    
    def retrieve_member_external_reference(self, query):
        if (len(query) < 3):
            raise AutoTenezException("The search query shall be 3 characters or more")

        r = requests.get("https://api.socie.nl/v2/app/communities/" + self.community_id + "/modules/5a250a75d186db12a00f1dfd/members/search?q=" + query, headers=self.headers, cookies=self.cookies)
        response = r.json()

        if (len(response) > 0):
            print("Found " + str(len(response)) + " member(s) using the query: " + query)
            for member in response:
                print(" - Name: " + member['appendedMembership']['fullName'])
                print(" - External reference: " + member['appendedMembership']['externalReference'])
                print()
        else:
            print("No members found using the query: " + query)

    def retrieve_slots(self):
        try:
            # Retrieve slots for tomorrow
            if (self.limit_debug_output is False):
                print("Retrieving time slots for " + self.reservation_date)

            time.sleep(1) # Lets not stress the server too much
            r = requests.get("https://api.socie.nl/v2/app/communities/" + self.community_id + "/modules/61cb14184779bc6fcade0980/allunited_tennis_courts/slots?date=" \
                    + str(self.reservation_date) + "&externalReferences=" + self.membership_id + "," + self.other_players_external_references, headers=self.headers, cookies=self.cookies)
            response = r.json()

            slots = []
            # Loop through all courts
            # Only loop through the tennis courts. These are the first 'no_courts' in the list in the response. Others are padel courts, but these are disregarded.
            for court_no in range(0, self.no_courts):
                slots_per_court = response['locations'][court_no]['slots']
                # Every time slot has slots
                for slot in slots_per_court:
                    # Only the courts which are available to reserve, have slot keys. Makes life easy for us
                    slot_keys = slot['slotKeys']
                    for key in slot_keys:
                        slot = []
                        slot.append(key['courtName'])
                        slot.append(key['beginDate'])
                        slot.append(key['md5slotkey'])
                        slots.append(slot)
           
            return slots

        # Catch JSONDecodeError
        except ValueError as e: 
            raise ParsingResponseFailed(r.status_code, r.headers, r.text, e, "Failed to retrieve slots")
        
    def find_time_slot(self, slots, first_hour, second_hour=None, courts=[]):
        previous_slot_available_and_matches = False
        second_time_slot_found = False
        first_time_slot_found = False
        first_court_first_time_slot_found = False

        # Sanity checks
        if (len(slots) < 1):
            print(" - No slots available")
            return 0, False, False
        if (first_hour is None):
            print(" - First hour is None. Skip")
            return 0, False, False

        # Loop through all available slots to find a match
        previous_available_slot_court_name = None
        for slot in slots:
            court_name = slot[0]
            time_slot = slot[1][11:16]
            md5slotkey = slot[2]

            # Compensate for difference between local time (has DST) and server time (UTC, has no DST)
            if (time.localtime().tm_isdst == True):
                # Summer time!
                time_slot = format(datetime.strptime(time_slot, '%H:%M') + timedelta(hours=+2), '%H:%M')
            else:
                # Snowman o'clock
                time_slot = format(datetime.strptime(time_slot, '%H:%M') + timedelta(hours=+1), '%H:%M')

            # If we already found the first hour, check if this time slot also matches the second hour
            # Verify the previous available and matched time slot is the same court
            if (previous_slot_available_and_matches == True) and (second_hour == time_slot) \
                and (previous_available_slot_court_name == court_name):
                # Yay! A court is available! Check if desired court matches
                if (self._check_court(courts, court_name) == True):
                    print(" - For the chosen time slot the first hour " + first_hour + " and second hour " + second_hour + " are available on " + court_name + " (" + md5slotkey + ")")
                    second_time_slot_found = md5slotkey
                    break

            # Check if this time slot matches the first hour
            if (first_hour == time_slot):
                # A court (for at least the first hour) is available! Check if desired court matches
                if (self._check_court(courts, court_name) == True):
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
                        previous_available_slot_court_name = court_name
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

    def _check_court(self, courts, court_name):
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

    def make_reservation(self, md5slotkey):
        time.sleep(1) # Lets not stress the server too much
        r = requests.get("https://api.socie.nl/communities/" + self.community_id + "/tennis_court_reservation_create?date=" \
            + str(self.reservation_date) + "&md5slotkey=" + md5slotkey + "&externalReferences=" + self.your_external_reference + "," + self.other_players_external_references, \
            headers=self.headers, cookies=self.cookies)
        
        # We expect a status code 204 No Content, with of course no content
        if (r.status_code == 204) and (len(r.content) == 0):
            print("Successfully made the reservation! With md5slotkey " + md5slotkey)
        else:
            raise ParsingResponseFailed(r.status_code, r.headers, r.text, e, "Failed to make the reservation with md5slotkey " + md5slotkey)

# If ran from command line
if __name__ == "__main__":
    try:
        # Parse input arguments
        parser = argparse.ArgumentParser(description='Reserve tennis court for tomorrow.')
        parser.add_argument('-c',  '--courts',               nargs='+',     help='Specify courts ("Baan X", where X is the court number). Default setting is all courts.')
        parser.add_argument('-d',  '--date',                                help='Specify the date to make the reservation (yyyy-mm-dd). Defaults to the greatest reservation limit set in the AutoTenez settings.')
        parser.add_argument('-t2', '--time_second_choice',   nargs='+',     help='Time you would like to reserve as a second option. One or two consecutive time slots separated by a space are allowed (hh:mm).')
        parser.add_argument('-c2', '--courts_second_choice', nargs='+',     help='Specify courts as second option ("Baan X", where X is the court number). Default setting is all courts.')
        parser.add_argument('-q',  '--query',                               help='Query used when looking up the external reference of a member by name.')
        parser.add_argument(       '--dryrun',               default=False, help="Pass as an argument to only check available time slots, but don't make a reservation.")

        required_arguments = parser.add_argument_group('Required arguments')
        required_arguments.add_argument('-t', '--time',    nargs='+', help="Time you would to you reserve. One or two consecutive time slots separated by a space are allowed (hh:mm).", required=True)
        required_arguments.add_argument('-f', '--friends', nargs='+', help="External reference of whom you would like to play with. Minimum of 1 player required, maximum of 3 players allowed.", required=True)

        args = parser.parse_args()

        # Process input arguments
        player2_external_reference = args.friends[0]
        player3_external_reference = ""
        player4_external_reference = ""
        if len(args.friends) > 1:
            player3_external_reference = args.friends[1]
        if len(args.friends) > 2:
            player4_external_reference = args.friends[2]
        if len(args.friends) > 3:
            raise AutoTenezException("A maximum of 3 external references is allowed, but " + str(len(args.friends)) + " references given: " + ",".join(args.friends))

        reservation_date = None
        if (args.date):
            reservation_date = args.date

        first_choice_first_hour = args.time[0]
        first_choice_second_hour = None
        if len(args.time) > 1:
            first_choice_second_hour = args.time[1]

        first_choice_courts = []
        if args.courts:
            first_choice_courts = args.courts

        second_choice_first_hour = None
        second_choice_second_hour = None
        if args.time_second_choice:
            second_choice_first_hour = args.time[0]
            if len(args.time_second_choice) > 1:
                second_choice_second_hour = args.time[1]

        second_choice_courts = []
        if args.courts_second_choice:
            second_choice_courts = args.courts_second_choice

        dryrun = args.dryrun

        # Init AutoTenez class
        iteration = 1
        while (1):
            try:
                auto_tenez = AutoTenez(reservation_date, first_choice_first_hour, player2_external_reference, player3_external_reference, player4_external_reference)
                break # No exception was thrown, assuming init was successful
            except ParsingResponseFailed:
                # If the server is unreachable an exception will be thrown
                iteration = iteration + 1
                print("Failed to initialize AutoTenez...retrying in 60 seconds (iteration " + str(iteration) + ")")
                if (iteration > 240):
                    print("Retried 240 times already. Exiting script now")
                    sys.exit(-1)
                
                time.sleep(60)

        # If specified the query argument is given, only perform the query action
        # TODO: move to a separate file and inherit other functions from the AutoTenez class
        if (args.query):
            print("Query external reference of a member by name...")
            auto_tenez.retrieve_member_external_reference(args.query)
            sys.exit(0)

        iteration = 1
        while (1):
            try:
                # Retrieve all time slots
                slots = auto_tenez.retrieve_slots()
        
                # Find available time slots
                if (auto_tenez.limit_debug_output is False):
                    print("Finding available time slots for your first choice...")
                first_choice_no_slots, first_choice_first_slotkey, first_choice_second_slotkey = \
                    auto_tenez.find_time_slot(slots, first_choice_first_hour, first_choice_second_hour, first_choice_courts)
                
                if (auto_tenez.limit_debug_output is False):
                    print("Finding available time slots for your second choice...")
                second_choice_no_slots, second_choice_first_slotkey, second_choice_second_slotkey = \
                    auto_tenez.find_time_slot(slots, second_choice_first_hour, second_choice_second_hour, second_choice_courts)
        
                first_md5slotkey = None
                second_md5slotkey = None
        
                # Reserve the biggest time slot
                if(second_choice_no_slots > first_choice_no_slots):
                    if (auto_tenez.limit_debug_output is False):
                        print("Propagating second choice. Number of time slots: " + str(second_choice_no_slots))
                    if (second_choice_first_slotkey):
                        if (auto_tenez.limit_debug_output is False):
                            print(" - First time slot md5slotkey " + second_choice_first_slotkey)
                        first_md5slotkey = second_choice_first_slotkey
                    if (second_choice_second_slotkey):
                        if (auto_tenez.limit_debug_output is False):
                            print(" - Second time slot md5slotkey " + second_choice_second_slotkey)
                        second_md5slotkey = second_choice_second_slotkey
                elif(first_choice_first_slotkey != False):
                    if (auto_tenez.limit_debug_output is False):
                        print("Propagating first choice. Number of time slots: " + str(first_choice_no_slots))
                    if (first_choice_first_slotkey):
                        if (auto_tenez.limit_debug_output is False):
                            print(" - First time slot md5slotkey " + first_choice_first_slotkey)
                        first_md5slotkey = first_choice_first_slotkey
                    if (first_choice_second_slotkey):
                        if (auto_tenez.limit_debug_output is False):
                            print(" - Second time slot md5slotkey " + first_choice_second_slotkey)
                        second_md5slotkey = first_choice_second_slotkey
                else:
                    print("There are no time slots available")
        
                if (dryrun) and (first_md5slotkey or second_md5slotkey):
                    print("Not making a reservation because dryrun is set to True")
                    first_md5slotkey = None
                    second_md5slotkey = None
                
                if (first_md5slotkey):
                    if (auto_tenez.limit_debug_output is False):
                        print("Make the reservation for the first time slot...")
                    auto_tenez.make_reservation(first_md5slotkey)
        
                if (second_md5slotkey):
                    if (auto_tenez.limit_debug_output is False):
                        print("Make the reservation for the second time slot...")
                    auto_tenez.make_reservation(second_md5slotkey)

                break # No exception was thrown, assuming reservation was successful

            except ParsingResponseFailed:
                # If the server is unreachable an exception will be thrown
                iteration = iteration + 1
                print("Failed to make a reservation...retrying in 60 seconds (iteration " + str(iteration) + ")")
                if (iteration > 600):
                    print("Retried 600 times already. Exiting script now")
                    sys.exit(-1)

                time.sleep(60)
                try:
                    auto_tenez.refresh_tokens()
                except Exception as e:
                    print("An error occurred while refreshing the tokens:")
                    print(e)

    except KeyboardInterrupt:
        print("\r\nKeyboard interrupt")
        sys.exit(-1)

    except AutoTenezException as e:
        print("An AutoTenez exception occurred!")
        print(e)
        sys.exit(-1)

    except Exception as e:
        print("An unexpected error occurred!")
        print(e)
        sys.exit(-1)
