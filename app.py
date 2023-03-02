from heroes_db import load_database_json, load_replay_files, get_game_id, get_details, update_players_info, save_database_json
from flask import Flask, render_template, request, send_from_directory, request, redirect, url_for
from werkzeug.utils import secure_filename
import logging
import os

DB_FILE="db.json"
ALLOWED_EXTENSIONS = ["stormreplay"]


app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1000 * 1000 # max 500mb upload (summing all replay files
app.config['UPLOAD_FOLDER'] = "./replays"
database = load_database_json(DB_FILE)

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


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_replay_file(full_filename):
    players = database["players"]
    seen_games = database["seen_games"]

    game_id = get_game_id(full_filename)
    if not game_id: # unsuported protocol
        print(f"unsupported protocol on replay {full_filename}")
        return

    if game_id in seen_games:
        print(f"Replay {full_filename} already seen in {seen_games[game_id]}")
        return
    seen_games[game_id] = full_filename

    details = get_details(full_filename)
    update_players_info(details, players)
    save_database_json(database, DB_FILE)


@app.route('/upload', methods=['GET', 'POST'])
def upload_replay():
    app.logger.info('accessing upload')
    if request.method == 'GET':
        return render_template('upload.html')

    # check if the post request has the "file" part
    if not request.files.getlist("file"):
        app.logger.error('could not find "files" on request')
        return redirect(request.url)

    files = request.files.getlist("file")
    for file in files:
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            app.logger.error('found one empty file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            app.logger.info(f'{file.filename} allowed')
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(full_filename)
            process_replay_file(full_filename)

            # remove file after processed
            os.remove(full_filename)
            app.logger.info('file %s processed successfully', full_filename)
    return f'{len(files)} Replays upload successfully'


@app.route('/stats')
def stats():
    return render_template('stats.html', nreplays=len(database["seen_games"]), nplayers=len(database["players"]))


@app.route('/stats/players')
def players():
    return render_template('players.html', players=database["players"].keys())


@app.route('/db.json')
def download_database():
    return send_from_directory("./", "db.json")
