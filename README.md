# heroesDB
Figure out what your enemy plays with on Heroes of the Storm

## Installation
```bash
python3 -m pip install -r requirements.txt
```

## Usage
To load data from replays simply pass the directory path. This will save all important information to a JSON file
```bash
python3 main.py [FOLDER_WITH_REPLAYS]
```

After you loaded your database once, you don't need to do it again, simply
```bash
python3 heroes_db.py
```
Obs: assuming there is a `db.json` file on your current directory
