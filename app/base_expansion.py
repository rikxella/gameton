import os
import random
import time
from random import choice

import numpy as np
import requests
from numpy import array as vec

from matplotlib import pyplot as plt


class BaseExpansion:
    def __init__(self, TOKEN, MOVE_ENDPOINT, ant_memory={}):
        self.ant_memory = ant_memory.copy()
        self.history = []
        self.MOVE_ENDPOINT = MOVE_ENDPOINT
        self.TOKEN = TOKEN

    def do_move(self, ants):
        body = {"moves": []}
        for ant in ants:
            body["moves"].append({"ant": ant[0], "path": ant[1]})
        resp = requests.post(self.MOVE_ENDPOINT, params={"token": self.TOKEN}, json=body)
        print(body)

    def serialize_data(self, coord: tuple[int, int]) -> dict[str, int]:
        q, r = coord
        return {"q": q, "r": r}

    def do_return(self, ant_uid, speed):
        if ant_uid not in self.ant_memory:
            # raise KeyError(f"THER'S NO SUCH ANT AS {ant_uid}")
            return None
        path = []
        while len(path) < speed and len(self.ant_memory[ant_uid]) > 0:
            path.append(self.ant_memory[ant_uid].pop())
        return path

    def update_memory(self, uid, path):
        if uid not in self.ant_memory.keys():
            self.ant_memory[uid] = path
            return
        for p in path:
            self.ant_memory[uid].append(p)

    def get_speed(self, type):
        return 1

    def choose_next_path(self, pos: tuple[int], prev_pos: tuple[int] = None, speed: int = 1) -> tuple[tuple[int, int]]:
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

    def __call__(self, state):
        units = state.get("ants", [])
        moves = []
        for unit in units:
            uid = unit["id"]
            pos = (unit["q"], unit["r"])
            new_path = self.choose_next_path(pos, None, self.get_speed(unit["type"]))[0]
            # print(new_path)
            if unit["food"]["amount"] != 0:
                new_path = self.do_return(uid, self.get_speed(unit["type"]))
            else:
                self.update_memory(uid, new_path)
            if new_path is None:
                continue
            moves.append((uid, [self.serialize_data(i) for i in new_path]))
        self.do_move(moves)


def mock_event_loop(render=True):
    if render:
        from visualizer import HexGridVisualizer
        path = time.time_ns()
        os.mkdir(str(path))

    BASE_URL = "https://games-test.datsteam.dev"  # Используем боевой сервер
    REGISTER_ENDPOINT = f"{BASE_URL}/api/register"
    STATE_ENDPOINT = f"{BASE_URL}/api/arena"
    MOVE_ENDPOINT = f"{BASE_URL}/api/move"

    TOKEN = os.environ.get("API_TOKEN")

    def register_round():
        resp = requests.post(REGISTER_ENDPOINT, params={"token": TOKEN})
        print(resp.json())
        return resp.json()["nextTurn"]
    ttl = register_round()
    time.sleep(ttl)

    policy = BaseExpansion(TOKEN=TOKEN, MOVE_ENDPOINT=MOVE_ENDPOINT)
    while True:
        state = requests.get(STATE_ENDPOINT, params={"token": TOKEN}).json()
        print(state)
        ttl = state["nextTurnIn"]
        try:
            policy(state)
            if render:
                visualizer = HexGridVisualizer(state)
                visualizer.visualize(save=True, path=path)
                plt.close()
        except Exception as e:
            print("Ошибка:", e)
        time.sleep(ttl)


mock_event_loop(render=True)
