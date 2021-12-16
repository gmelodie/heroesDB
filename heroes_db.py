import os
import sys
import json
import mpyq
import pprint
import heroprotocol
from tqdm import tqdm
from heroprotocol.versions import build, latest

NUMARGS=2
DB_FILE="db.json"
TESTING=False
pp = pprint.PrettyPrinter(indent=4)

def get_game_id(full_filename):
    archive = mpyq.MPQArchive(full_filename)

    # Read the protocol header, this can be read with any protocol
    contents = archive.header['user_data_header']['content']
    header = latest().decode_replay_header(contents)

    # The header's baseBuild determines which protocol to use
    baseBuild = header['m_version']['m_baseBuild']
    try:
        protocol = build(baseBuild)
    except:
        print('Unsupported base build: %d' % baseBuild, file=sys.stderr)
        return None

    contents = archive.read_file('replay.initData')
    initdata = protocol.decode_replay_initdata(contents)
    return initdata['m_syncLobbyState']['m_gameDescription']['m_randomValue']


def get_details(full_filename):
    archive = mpyq.MPQArchive(full_filename)

    # Read the protocol header, this can be read with any protocol
    contents = archive.header['user_data_header']['content']
    header = latest().decode_replay_header(contents)

    # The header's baseBuild determines which protocol to use
    baseBuild = header['m_version']['m_baseBuild']
    try:
        protocol = build(baseBuild)
    except:
        print('Unsupported base build: %d' % baseBuild, file=sys.stderr)
        sys.exit(1)

    # Print protocol details
    contents = archive.read_file('replay.details')
    details = protocol.decode_replay_details(contents)
    return details


def extract_player_details(player):
    # remove weird characters from username
    nick = player['m_name'].decode('ascii', 'ignore').lower()

    player_id = player['m_toon']['m_id']
    hero = player['m_hero'].decode()

    # result ranks the teams (1 won, 2 lost)
    result = player['m_result']
    win = False
    if result == 1:
        win = True

    return nick, player_id, hero, win


def update_players_info(details, players):
    for player in details['m_playerList']:
        nick, player_id, hero, win = extract_player_details(player)

        # update overall statistics
        if nick not in players:
            players[nick] = {'wins': 0,\
                             'total_games': 0,\
                             'win_rate': 0,\
                             'heroes': {},\
                             'games': {}}
        if hero not in players[nick]['heroes']:
            players[nick]['heroes'][hero] = {"total_games": 0,\
                                             "wins": 0,\
                                             "win_rate": 0}

        players[nick]['heroes'][hero]['total_games'] += 1
        players[nick]['total_games'] += 1
        if win:
            players[nick]['heroes'][hero]['wins'] += 1
            players[nick]['wins'] += 1

        # update overall win rate
        wins = players[nick]['wins']
        total_games = players[nick]['total_games']
        win_rate = int(100*wins/total_games)
        players[nick]['win_rate'] = win_rate

        # update per-hero win rate
        wins = players[nick]['heroes'][hero]['wins']
        total_games = players[nick]['heroes'][hero]['total_games']
        win_rate = int(100*wins/total_games)
        players[nick]['heroes'][hero]['win_rate'] = win_rate

        # update map statistics
        map_title = details['m_title'].decode()
        if map_title not in players[nick]['games']:
            players[nick]['games'][map_title] = {'wins': 0, \
                                                 'total_games': 0, \
                                                 'win_rate': 0,
                                                 'heroes': {}}
        if hero not in players[nick]['games'][map_title]['heroes']:
            players[nick]['games'][map_title]['heroes'][hero] = 0

        players[nick]['games'][map_title]['heroes'][hero] += 1
        players[nick]['games'][map_title]['total_games'] += 1
        if win:
            players[nick]['games'][map_title]['wins'] += 1

        # update per-map win rate
        wins = players[nick]['games'][map_title]['wins']
        total_games = players[nick]['games'][map_title]['total_games']
        win_rate = int(100*wins/total_games)
        players[nick]['games'][map_title]['win_rate'] = win_rate


def load_replay_files(database, directory):
    players = database["players"]
    seen_games = database["seen_games"]
    for i, filename in tqdm(enumerate(os.listdir(directory)), \
                            total=len(os.listdir(directory)), unit='replays', \
                            colour='green', desc="Loading replays", unit_scale=True,\
                            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} {rate_fmt}{postfix}'+' '*30):

        if not filename.endswith(".StormReplay"):
            continue

        full_filename = directory+'/'+filename

        game_id = get_game_id(full_filename)
        if not game_id: # unsuported protocol
            continue

        if game_id in seen_games:
            print(f"Replay {filename} already seen in {seen_games[game_id]}")
            continue
        seen_games[game_id] = filename

        details = get_details(full_filename)
        update_players_info(details, players)

    if TESTING:
        pp.pprint(players)

    return {"players": players, "seen_games": seen_games}


def print_overall_stats(player):
    print(f'================ STATS ================')
    print(f"Overall win rate: {player['win_rate']}%")
    print()


def print_heroes(heroes):
    print(f'================ HEROES ================')
    for hero, stats in heroes:
        print(f"{stats['total_games']}\t{stats['win_rate']}%\t-> {hero}")
    print()


def print_maps(maps):
    print(f'================ MAPS ================')
    for map_title, stats in maps:
        print(f"{stats['win_rate']}%\t{map_title}")
        sorted_heroes = sorted(stats['heroes'].items(), \
                key=lambda item: item[1])

        for hero, ngames in sorted_heroes:
            print(f'\t{ngames} -> {hero}')
        print()
    print()


def save_database_json(database, filename):
    with open(filename, "w") as json_file:
        json.dump(database, json_file)


def load_database_json(filename):
    if not os.path.isfile(filename):
        return {"players": {}, "seen_games": {}}

    with open(filename, "r") as json_file:
        database = json.load(json_file)
    return database


if __name__ == '__main__':
    if len(sys.argv) > NUMARGS:
        print('usage: python3 main.py [REPLAY_FOLDER]')
        exit(1)

    database = load_database_json(DB_FILE)
    if len(sys.argv) == 2:
        replays_directory = sys.argv[1]
        # make sure directory name doesn't have a trailing /
        if replays_directory.endswith('/'):
            replays_directory = replays_directory[:-1]
        database = load_replay_files(database, replays_directory)

    save_database_json(database, DB_FILE)
    print(f"Database saved to {DB_FILE}")

    players = database["players"]
    query_nick = ""
    while query_nick != 'exit':
        query_nick = input("Player: ")
        if query_nick not in players:
            print('[ERROR] Player not found')
            continue

        sorted_maps = sorted(players[query_nick]['games'].items(), \
            key=lambda item: item[1]['win_rate'])
        sorted_heroes = sorted(players[query_nick]['heroes'].items(), \
            key=lambda item: item[1]['total_games'])

        if TESTING:
            pp.pprint(players[query_nick])
            break
        print_overall_stats(players[query_nick])
        print_heroes(sorted_heroes)
        print_maps(sorted_maps)
        print()
