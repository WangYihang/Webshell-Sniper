# -*- coding: utf-8 -*-

import requests
import ConfigParser
import json
import sys
import datetime

challenge = "BabyEval"
category = "WEB"

config = ConfigParser.ConfigParser()
config.read('../config.ini')

def create_game(name, start_time, end_time, bout=300):
    data = {
        "name": name,
        "start_time": start_time,
        "end_time": end_time,
        "bout":bout,
    }
    response = requests.post(
        "http://%s:%d/api/game/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
        ),
        data=data,
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    return json.loads(response.content)

def create_challenge(name, category, game_id):
    data = {
        "game":"http://%s:%d/api/game/%d/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
            game_id,
        ),
        "name": name,
        "category": category,
    }
    response = requests.post(
        "http://%s:%d/api/challenge/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
        ),
        data=data,
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    return json.loads(response.content)

def create_team(name, game_id):
    data = {
        "game":"http://%s:%d/api/game/%d/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
            game_id
        ),
        "name": name,
    }
    response = requests.post(
        "http://%s:%d/api/team/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
        ),
        data=data,
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    return json.loads(response.content)

def create_target(host, port, team_id, challenge_id, enabled=True):
    data = {
        "host": host,
        "port": port,
        "enable": True,
        "team":"http://%s:%d/api/team/%d/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
            team_id
        ),
        "challenge":"http://%s:%d/api/challenge/%d/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
            challenge_id
        ),
    }
    response = requests.post(
        "http://%s:%d/api/target/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
        ),
        data=data,
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    return json.loads(response.content)

def get_game(name):
    response = requests.get(
        "http://%s:%d/api/game/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
        ),
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    data = json.loads(response.content)
    for i in data:
        if i["name"] == name:
            return i

def get_team(name):
    response = requests.get(
        "http://%s:%d/api/team/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
        ),
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    data = json.loads(response.content)
    for i in data:
        if i["name"] == name:
            return i

def get_challenge(name):
    response = requests.get(
        "http://%s:%d/api/challenge/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
        ),
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    data = json.loads(response.content)
    for i in data:
        if i["name"] == name:
            return i

def get_targets(challenge_id):
    response = requests.get(
        "http://%s:%d/api/target/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
        ),
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    content = response.content
    data = json.loads(response.content)
    result = []
    for i in data:
        if "challenge/%d/" % (challenge_id) in i["challenge"]:
            result.append(i)
    return result

def create_webshell(target_id, path, filename, password, alive=True, memory=False):
    data = {
        "path": path,
        "filename": filename,
        "password": password,
        "alive": alive,
        "memory": memory,
        "target":"http://%s:%d/api/target/%d/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
            target_id
        ),
    }
    response = requests.post(
        "http://%s:%d/api/webshell/" % (
            config.get("sirius", "host"),
            int(config.get("sirius", "port")),
        ),
        data=data,
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    return json.loads(response.content)

def main():
    if len(sys.argv) != 5:
        print('python %s [CHALLENGE_NAME] [PATH] [FILENAME] [PASSWORD]') 
        exit(1)
    challenge_name = sys.argv[1]
    path = sys.argv[2]
    filename = sys.argv[3]
    password = sys.argv[4]

    game_id = get_game(config.get("game", "name"))['id']
    challenge_id = get_challenge(challenge_name)['id']

    targets = get_targets(challenge_id)
    for target in targets:
        print create_webshell(
            target_id=target["id"],
            path="/",
            filename="index.php",
            password="c",
            alive=True,
            memory=False,
        )

if __name__ == "__main__":
    main()

