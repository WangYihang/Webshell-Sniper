# -*- coding: utf-8 -*-

import requests
import ConfigParser
import json
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
        "http://%s:%s@sirius.lilac.com/api/game/" % (
            config.get("nginx", "username"),
            config.get("nginx", "password"),
        ),
        data=data,
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    return json.loads(response.content)

def create_challenge(name, category, game_id):
    data = {
        "game":"http://sirius.lilac.com/api/game/%d/" % (game_id),
        "name": name,
        "category": category,
    }
    response = requests.post(
        "http://%s:%s@sirius.lilac.com/api/challenge/" % (
            config.get("nginx", "username"),
            config.get("nginx", "password"),
        ),
        data=data,
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    return json.loads(response.content)

def create_team(name, game_id):
    data = {
        "game":"http://sirius.lilac.com/api/game/%d/" % (game_id),
        "name": name,
    }
    response = requests.post(
        "http://%s:%s@sirius.lilac.com/api/team/" % (
            config.get("nginx", "username"),
            config.get("nginx", "password"),
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
        "team":"http://sirius.lilac.com/api/team/%d/" % (team_id),
        "challenge":"http://sirius.lilac.com/api/challenge/%d/" % (challenge_id),
    }
    response = requests.post(
        "http://%s:%s@sirius.lilac.com/api/target/" % (
            config.get("nginx", "username"),
            config.get("nginx", "password"),
        ),
        data=data,
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    return json.loads(response.content)

def get_team(name):
    response = requests.get(
        "http://%s:%s@sirius.lilac.com/api/team/" % (
            config.get("nginx", "username"),
            config.get("nginx", "password"),
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
        "http://%s:%s@sirius.lilac.com/api/challenge/" % (
            config.get("nginx", "username"),
            config.get("nginx", "password"),
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
        "http://%s:%s@sirius.lilac.com/api/target/" % (
            config.get("nginx", "username"),
            config.get("nginx", "password"),
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
        "target":"http://sirius.lilac.com/api/target/%d/" % (target_id),
    }
    response = requests.post(
        "http://%s:%s@sirius.lilac.com/api/webshell/" % (
            config.get("nginx", "username"),
            config.get("nginx", "password"),
        ),
        data=data,
        headers={
            'Authorization': 'Bearer %s' % (config.get("sirius", "token")),
        }
    )
    return json.loads(response.content)

game_id = 1
challenge_id = 1

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
