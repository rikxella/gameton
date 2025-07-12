import os
import random
import time
from random import choice

import numpy as np
import requests
from numpy import array as vec

BASE_URL = "https://games-test.datsteam.dev"  # Используем боевой сервер
REGISTER_ENDPOINT = f"{BASE_URL}/api/register"
STATE_ENDPOINT = f"{BASE_URL}/api/arena"
MOVE_ENDPOINT = f"{BASE_URL}/api/move"

TOKEN = os.env("API_TOKEN")

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

ant_memory = {}


def register_round():
    resp = requests.post(REGISTER_ENDPOINT, params={"token": TOKEN})
    print(resp.json())
    return resp.json()["nextTurn"]


def add_coords(a, b):
    return [a[0] + b[0], a[1] + b[1]]


def do_move(ants):
    body = {"moves": []}
    for ant in ants:
        body["moves"].append({"ant": ant[0], "path": ant[1]})
    resp = requests.post(MOVE_ENDPOINT, params={"token": TOKEN}, json=body)
    print(body)


def serialize_data(coord: tuple[int, int]) -> dict[str, int]:
    q, r = coord
    return {"q": q, "r": r}


def get_path(pos):
    pass


def do_return(ant_uid, speed):
    global ant_memory
    if ant_uid not in ant_memory:
        # raise KeyError(f"THER'S NO SUCH ANT AS {ant_uid}")
        return None
    path = []
    while len(path) < speed and len(ant_memory[ant_uid]) > 0:
        path.append(ant_memory[ant_uid].pop())
    return path


def update_memory(uid, path):
    global ant_memory
    if uid not in ant_memory.keys():
        ant_memory[uid] = path
        return
    for p in path:
        ant_memory[uid].append(p)


def get_speed(type):
    return 1


def choose_next_path(pos: tuple[int], prev_pos: tuple[int] = None, speed: int = 1) -> tuple[tuple[int, int]]:
    valid_vectors = [
        [0, +1],
        [0, -1],
        [-1, 0],
        [+1, 0],
        [-1, +1],
        [+1, -1],
    ]
    if prev_pos is None:
        prev_pos = [0, 0]
    new_path = prev_pos
    while new_path == prev_pos:
        new_path = choice(valid_vectors)
    path = [vec(pos) + (i + 1) * np.array(new_path) for i in range(speed)]
    path = list(map(lambda x: x.tolist(), path))
    return [path, (-vec(new_path)).tolist()]


ttl = register_round()
time.sleep(ttl)
while True:
    state = requests.get(STATE_ENDPOINT, params={"token": TOKEN}).json()
    print(state)
    ttl = state["nextTurnIn"]
    try:
        units = state.get("ants", [])
        moves = []
        for unit in units:
            uid = unit["id"]
            pos = (unit["q"], unit["r"])
            new_path = choose_next_path(pos, None, get_speed(unit["type"]))[0]
            # print(new_path)
            if unit["food"]["amount"] != 0:
                new_path = do_return(uid, get_speed(unit["type"]))
            else:
                update_memory(uid, new_path)
            if new_path is None:
                continue
            moves.append((uid, [serialize_data(i) for i in new_path]))
        do_move(moves)

    except Exception as e:
        print("Ошибка:", e)
    time.sleep(ttl)
