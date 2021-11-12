# Just Watch Letterboxd
### Find out where all films you want to watch are streaming

Ever wonder what films you want to watch are already on the streaming platforms
you subscribe to but too lazy to search for them all? Fear not! If you have a
Letterboxd Watchlist, you can use this script to figure out what subscription
streaming platforms those films are on! Services default to HBO Max, Hulu,
Netflix, Disney+, Amazon Prime Video, and Criterion Channel, but the list is 
customizable.

## INSTALLATION
`python3 -m pip install -r requirements.txt`

Edit `config.yml` and put in your details (no auth required)

## USAGE
`python3 justwatch_letterboxd.py`

Note! Depending on the size of your Letterboxd Watchlist, this script can take a
really long time! With my list of >700 films, it took about a half hour to run.
Be patient!

## ENJOY
Your list of films will be found sorted by service in `sorted_by_service.txt`.

## EXAMPLE
![Output example.](/sample.png "This is what the output will look like.")
