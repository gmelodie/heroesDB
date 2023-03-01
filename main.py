from heroes_db import load_database_json, load_replay_files
from flask import Flask, render_template, request

DB_FILE="db.json"
app = Flask(__name__)
database = {}

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/user')
def search_user():
    players = database["players"]

    username = request.args.get("username")
    if not username or username not in players:
        return f'Player {username} not found'

    sorted_heroes = sorted(players[username]['heroes'].items(), \
                           key=lambda item: item[1]['total_games'])[::-1]

    sorted_maps = sorted(players[username]['games'].items(), \
                         key=lambda item: item[1]['win_rate'])[::-1]

    return render_template('username.html', player=players[username], heroes=sorted_heroes, maps=sorted_maps, username=username)


@app.route("/upload", methods=['POST'])
def upload():
    pass

if __name__ == '__main__':
    database = load_database_json(DB_FILE)
    replays_directory = "/home/gmelodie/Games/heroes-of-the-storm/drive_c/users/gmelodie/Documents/Heroes of the Storm/Accounts/77009925/1-Hero-1-168611/Replays/Multiplayer/" # TODO: change this to be configurable
    # database = load_replay_files(database, replays_directory)

    app.run()

