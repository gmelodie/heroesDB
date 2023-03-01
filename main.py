from heroes_db import load_database_json, load_replay_files, get_game_id, get_details
from flask import Flask, render_template, request
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

DB_FILE="db.json"
ALLOWED_EXTENSIONS = ["StormReplay"]


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 # max 16mb per replay file
app.config['UPLOAD_FOLDER'] = "/replays"
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
        print(f"Replay {filename} already seen in {seen_games[game_id]}")
        return
    seen_games[game_id] = filename

    details = get_details(full_filename)
    update_players_info(details, players)
    save_database_json(database, DB_FILE)


@app.route('/upload', methods=['GET', 'POST'])
def upload_replay():
    if request.method == 'GET':
        return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form method=post enctype=multipart/form-data>
          <input type=file name=file>
          <input type=submit value=Upload>
        </form>
        '''
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        process_replay_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # remove file after processed
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return f'File uploaded successfully'


if __name__ == '__main__':
    database = load_database_json(DB_FILE)
    # replays_directory = "/home/gmelodie/Games/heroes-of-the-storm/drive_c/users/gmelodie/Documents/Heroes of the Storm/Accounts/77009925/1-Hero-1-168611/Replays/Multiplayer/" # TODO: change this to be configurable
    # database = load_replay_files(database, replays_directory)
    app.run()

