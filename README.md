# AutoTenez
Automates the process of making tennis court reservations for you.

## Setup
1. Install all necessary pip dependencies using `python -m pip install -r requirements.txt`.
2. Open `AutoTenez.py`. Enter your email address, password, and set `only_retrieve_your_external_reference` to `True`.
3. Run `python AutoTenez.py -t 00:00 -f 0` to retrieve your own external reference.
4. Share your external reference with a friend, and set `only_retrieve_your_external_reference` to `False`.

## Usage
1. Run `python AutoTenez.py -h` in a terminal to see all options possible.

### Example usage
- `python AutoTenez.py -t 18:30 -f 12341234` attemps to do a reservervation for tomorrow at time `18:30` with friend that has ID `12341234`  
- `python AutoTenez.py -t 8:30 9:30 -f 12341234` attemps to do a reservervation for tomorrow at time `8:30` and `9:30` (so from 8:30 to 10:30) with friend that has ID `12341234`. Note: These times have to be consecutive and two time slots can only be reserved before `18:00`.  
- `python AutoTenez.py -t 18:30 -f 12341234 -c "Baan 4" "Baan 5"` attemps to do a reservation for tomorrow at time `18:30` with friend that has ID `12341234` at court `4` or `5`. Other courts will not be checked.
- `python AutoTenez.py -t 18:30 -f 12341234 --dryrun 1` only checks whether the time to reserve is available, but does not actually make the reservation.

## Known issues
* Performs a login everytime you run the script. Please do not run the script too often.
* Does not account for how many number of players the court is available to make a reservation.
* Passing `--dryrun` as an argument needs a value assigned in order to properly work (e.g. `--dryrun 1`).