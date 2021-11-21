import os
import sys
import mpyq
import heroprotocol
from heroprotocol.versions import build, latest

NUMARGS=2


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
    nick = player['m_name'].decode()
    player_id = player['m_toon']['m_id']
    hero = player['m_hero'].decode()

    # result ranks the teams (1 won, 2 lost)
    result = player['m_result']
    if result == 1:
        win = True
    elif result == 2:
        win = False

    return nick, player_id, hero, win


if __name__ == '__main__':
    if len(sys.argv) != NUMARGS:
        print('usage: python3 main.py <REPLAY_FOLDER>')
        exit(1)

    directory = sys.argv[1]

    # make sure directory name doesn't have a trailing /
    if directory.endswith('/'):
        directory = directory[:-1]

    for filename in os.listdir(directory):
        if filename.endswith(".StormReplay"):
            full_filename = directory+'/'+filename
            details = get_details(full_filename)
            for player in details['m_playerList']:
                nick, player_id, hero, win = extract_player_details(player)
                if win:
                    print(f"{nick}(ID: {player_id}) ---> {hero}\t[WIN]")
                else:
                    print(f"{nick}(ID: {player_id}) ---> {hero}\t[LOSE]")
        break # TODO: remove, using for testing
