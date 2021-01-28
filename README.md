# AutoTenez
Automates the process of making tennis court reservations for you.

## Usage
1. Open `AutoTenez.py` and enter your personal details.
1. Run `python3 AutoTenez.py -h` in a terminal to see all options possible. 

### Example usage
- `python AutoTenez.py -t 18:30 -f 12341234` attemps to do a reservervation for tomorrow at time `18:30` with friend that has ID `12341234`  
- `python AutoTenez.py -t 8:30 9:30 -f 12341234` attemps to do a reservervation for tomorrow at time `8:30` and `9:30` (so from 8:30 to 10:30) with friend that has ID `12341234`. Note: These times have to be consecutive and two time slots can only be reserved before `18:00`.  
- `python AutoTenez.py -t 18:30 -f 12341234 -c "Baan 4" "Baan 5"` attemps to do a reservation for tomorrow at time `18:30` with friend that has ID `12341234` at court `4` or `5`. Other courts will not be checked.

## Known issues
* Performs a login everytime you run the script. Please do not run the script too often.
* Does not account for how many number of players the court is available to make a reservation.
