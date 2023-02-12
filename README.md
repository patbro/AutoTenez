# AutoTenez
Automates the process of making tennis court reservations for you.

## Setup
1. Install all necessary pip dependencies using `python -m pip install -r requirements.txt`.
1. Open `AutoTenez.py`. Enter your email address, password in the designated variables, or create `credentials.txt` where the first line should contain your email address and the second line your password. Finally, set `only_retrieve_personal_information` to `True` in `AutoTenez.py`.
1. Run `python AutoTenez.py -t 00:00 -f 0` to retrieve your own external reference.
1. Share your external reference with a friend, and set `only_retrieve_personal_information` to `False`.
1. Set the reservation limits of your club in `possible_to_reserve` (defaults to 48 hours upfront), and define the number of courts for your club in `no_courts` (defaults to 21 courts).

## Usage
1. Run `python AutoTenez.py -h` in a terminal to see all options possible.

### Example usage
- `python AutoTenez.py -t 18:30 -f 12341234` attempts to make a reservervation at time `18:30` with friend that has ID `12341234`, by default only succeeds when run 48 hours upfront.
- `python AutoTenez.py -t 08:30 09:30 -f 12341234` attempts to make a reservervationi at time `08:30` and `09:30` (so from 08:30 to 10:30) with friend that has ID `12341234`, by default only succeeds when run 48 hours upfront. Note: These times have to be consecutive and two time slots can only be reserved before `18:00`.
- `python AutoTenez.py -t 18:30 -f 12341234 -c "Tennis 4" "Tennis 5"` attempts to make a reservation for tomorrow at time `18:30` with friend that has ID `12341234` at court `4` or `5`. Other courts will not be checked.
- `python AutoTenez.py -t 18:30 -f 12341234 --dryrun 1` only checks whether the time to reserve is available, but does not actually make the reservation.
- `python AutoTenez.py -t 00:00 -f 0 -q Jan` perform a query to look up the external reference of a member by name (e.g. `Jan`). Query shall be 3 characters or more.
- 'python AutoTenez.py -t 00:00 -f 0 --delete 1` can be used to manually delete a reservation (shell input required).

## Known issues
* Performs a login everytime you run the script. Please do not run the script too often.
* Does not account for how many number of players the court is available to make a reservation.
* Passing `--dryrun` as an argument needs a value assigned in order to properly work (e.g. `--dryrun 1`).
* Move setup and query functionality to a separate file.
* Not reserving a possible time slot when second choice is set before first choice, though second choice is within 48 hours.
