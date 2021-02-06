# AutoTenez
Automates the process of making tennis court reservations for you.

## Usage
1. Open `AutoTenez.py` and enter your personal details.
1. Run `python3 AutoTenez.py -h` in a terminal to see all options possible. 

### Example usage
- `python AutoTenez.py -t 18:30 -f 12341234` attempt to reserve a time slot for tomorrow at `18:30` with a friend that has external reference `12341234`.
- `python AutoTenez.py -t 08:30 09:30 -f 12341234` attempt to reserve two time slots for tomorrow at `8:30` and `9:30` (so from 8:30 to 10:30) with a friend that has external reference `12341234`. Note: these times have to be consecutive and two time slots can only be reserved before `18:00`.
- `python AutoTenez.py -t 18:30 -f 12341234 -c "Baan 4" "Baan 5"` attempt to reserve a time slot for tomorrow at `18:30` with a friend that has external reference `12341234` at court `4` or `5`. Other courts will not be checked.

## Known issues
* Performs a login everytime you run the script. Please do not run the script too often.
* Does not account for how many number of players the court is available to make a reservation.
