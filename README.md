# Bizzare Biomes Gen Script

Creates n number *(default is 20)* of Bizzarre Biomes. Please note, there is no implementation of conflicts at the moment, and each attribute has a relatively equal weighting/rarity.

## Pre requisists 

1. You have the following structure;
```
.
├── Bizzare-Biomes-Assets
│   ├── README.md
│   └── ZILponds
│       ├── Environment background
│       │   ├── Aurora borealis sky.png 
│       │   ├── ...
│       │   └── numbers.csv
│       ├── Environment foreground
│       │   ├── Arctic.png
│       │   ├── ...
│       │   └── numbers.csv
│       ├── Objects
│       │   ├── Beach stuff.png
│       │   ├── ...
│       │   └── numbers.csv
│       └── Thumbs.db
├── Bizzare-Biomes-Gen-Script
│   ├── Pipfile
│   ├── Pipfile.lock
│   ├── README.md
│   ├── application.py
│   ├── src
│   │   ├── __init__.py
│   │   └── main.py
```

Where `.` is a parent directory _(like so;)_
```
(Bizzare-Biomes-Gen-Script) [richard:~/Documents/git/bizzare]$ pwd
/Users/richard/Documents/git/bizzare
(Bizzare-Biomes-Gen-Script) [richard:~/Documents/git/bizzare]$ ls -l
total 376
drwxr-xr-x  5 richard  staff     160 22 May 12:37 Bizzare-Biomes-Assets
drwxr-xr-x@ 9 richard  staff     288 23 May 17:37 Bizzare-Biomes-Gen-Script
```

2. Virtual env made, you can do the following;
```
$ python -m venv venv
$ # To activate; source venv/bin/activate
```

3. requirements installed (MAKE SURE VENV IS ACTIVATED)
```
(venv) $ pip install -r requirements.txt
```

## Running

It's super easy to run the application
```
(venv) $ ./application
```
This will by default perform 20 iterations. If you require more, just specify;
```
(venv) $ ./application 1024
```

Currently this is single threaded.

## Number.csv

Run the following _(this assumes you have the same directory lay out)_
```
cp background_numbers.csv ../bizzare/Bizzare-Biomes-Assets/ZILponds/Environment\ background/numbers.csv \
cp foreground_numbers.csv ../bizzare/Bizzare-Biomes-Assets/ZILponds/Environment\ foreground/numbers.csv \
cp object_numbers.csv ../bizzare/Bizzare-Biomes-Assets/ZILponds/Objects/numbers.csv 
```

I would have included them in the ponds repo, but just incase I get a ree at the numbers, I've added them here instead.
