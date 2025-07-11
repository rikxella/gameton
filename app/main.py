import requests
import random
import time
import os

from random import choice
import numpy as np
from numpy import array as vec

BASE_URL = "https://games.datsteam.dev"  # Используем боевой сервер
REGISTER_ENDPOINT = f"{BASE_URL}/api/register"
STATE_ENDPOINT = f"{BASE_URL}/api/state"
MOVE_ENDPOINT = f"{BASE_URL}/api/move"

TOKEN = ""
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

ant_memory = {}

def register_round():
    resp = requests.post(REGISTER_ENDPOINT, params={'token': TOKEN})
    return resp.json['nextTurn']


def add_coords(a, b):
    return [a[0] + b[0], a[1] + b[1]]

def do_move(ants):
    body = {"movers":[]}
    for ant in ants:
        body["movers"].append({"ant": ant[0], "path": ant[1]})
    requests.post(MOVE_ENDPOINT, params={"token": TOKEN}, json=body)

def get_path(pos):
    pass

def do_return(ant_uid,speed):

    
def update_memory(uid,path):
    global ant_memory
    if uid in ant_memory.keys():
        ant_memory[uid] = path
        return
    for p in path:
        ant_memory[uid].append(p)
    

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
    ttl = state['nextTurnIn']
    try:
        units = state.get("ants", [])
        moves = []
        for unit in units:
            uid = unit["id"]
            pos = (unit["r"], unit["q"])
            new_path = choose_next_path(pos)
            update_memory(uid, new_path)
            moves.append((uid, new_path))
        do_move(moves)

    except Exception as e:
        print("Ошибка:", e)
    time.sleep(ttl)
