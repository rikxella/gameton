import os
import random
import time
from random import choice

import numpy as np
import requests
from numpy import array as vec

from matplotlib import pyplot as plt


class ChainPolicy:
    def __init__(self, TOKEN, MOVE_ENDPOINT, ant_memory={}):
        self.tic_number = 0
        self.ant_memory = ant_memory.copy()
        self.main_ant_path = []
        self.mirror = []
        self.is_backward = False
        self.is_finished = False
        self.vector = None
        self.backward_vector = None
        self.main_ant_uid = None
        self.history = []
        self.MOVE_ENDPOINT = MOVE_ENDPOINT
        self.TOKEN = TOKEN
    

    def rotate_pos_60(self, pos):
        x, z = pos
        y = -x - z
        left = [-z, -x, -y]
        x, y, z = left
        return [x, z]

    
    def get_valid_paths(self):
        # cubic
        x = self.vector[0]
        z = self.vector[1]
        y = -x - z
        # rotate left/right 60 and 0
        left = [-z, -x, -y]
        right = [-y, -z, -x]
        ego = [x, y, z]
        next_vec = choice(left, right, ego)
        x, y, z = next_vec
        vec = [x, z]
        return vec
    
    def get_neightbour_hex(self, pt, last_vec):
        neighbour = (vec(pt) + vec(self.rotate_pos_60(last_vec))).tolist()
    
    def hex_is_available(self, pt):
        map = self.history[-1]["map"]
        map = { (int(map_pt["q"]), int(map_pt["r"])): map_pt for map_pt in map }
        if hex in map and map[hex]["type"] in [2, 3]:
            return True
        return False
    
    def neighbour_hex_is_available(self, pt, last_vec):
        neighbour_hex = self.get_neightbour_hex(pt, last_vec)
        return self.hex_is_available(neighbour_hex)
    
    def sample_while_available(self, pos, retries=6):
        tries = 0
        while tries < retries:
            tries += 1
            new_path = self.get_valid_paths()
            pts = self.sample_by_vec(pos, new_path)
            path_is_unavailable = False
            mirror_path = []
            for pt in pts:
                if not self.neighbour_hex_is_available(pt, new_path):
                    path_is_unavailable = True
                    break
                mirror_path.append(self.get_neightbour_hex(pt, new_path))
            if path_is_unavailable:
                continue
            else:
                return [pts, mirror_path]
        self.is_backward = True
        return [[], []]
    
    def choose_main_vector(self):
        valid_vectors = [
            [[0, +1],
            [0, -1],
            [-1, 0],
            [+1, 0],
            [-1, +1],
            [+1, -1],]
        ]
        main_base_hex = [self.history[-1]["spot"]["q"], self.history[-1]["spot"]["r"]]
        other_base_hexs = [[sample["q"], sample["r"]] for sample in self.history[-1]["home"]]
        other_base_hexs = [hex for hex in other_base_hexs if hex != main_base_hex]
        for vector in valid_vectors:
            hex = (vec(vector) + vec(main_base_hex)).tolist()
            neighbour_hex = (vec(main_base_hex) + vec(self.rotate_pos_60(vector))).tolist()
            print(f"vec is {vector}, rotated is {self.rotate_pos_60(vector)}")
            if neighbour_hex in other_base_hexs and self.hex_is_available(hex):
                self.vector = vector
            else:
                print(f"NIOH")
                
    
    def control_main_ant_moves(self, pos):
        if self.tic_number == 1:
            self.main_ant_uid = self.history[-1]["ants"][0]["id"]
            self.choose_main_vector()
        if self.is_finished:
            cur_path = [(vec(pos) + (i + 1) * (-vec(self.vector))).tolist() for i in range(self.get_speed(0))]
        elif self.is_backward:
            cur_path = []
            for _ in range(self.speed(0)):
                target = self.mirror.pop()
                self.main_ant_path.append(target)
                cur_path.append(target)
        else:
            cur_path, mirror_path = self.sample_while_available(pos)
            self.main_ant_path.extend(cur_path)
            self.mirror.extend(mirror_path)
        return cur_path
    

    def control_stupid_ant_moves(self, pos):
        for i, path_hex in enumerate(self.main_ant_path):
            if path_hex != pos:
                continue
            path = []
            for bias in range(self.get_speed(0)):
                if i + bias + 1 < len(self.main_ant_path):
                    path.append(self.main_ant_path[i + bias + 1])
            return path
        return []


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
    
    def sample_by_vec(self, pos, new_path):
        path = [vec(pos) + (i + 1) * vec(new_path) for i in range(self.get_speed(0))]
        path = list(map(lambda x: x.tolist(), path))
        return path

    def __call__(self, state):
        self.tic_number += 1
        units = state.get("ants", [])
        self.history.append(state)
        moves = []
        for unit in units:
            uid = unit["id"]
            pos = (unit["q"], unit["r"])
            if self.tic_number == 1 or uid == self.main_ant_uid:
                new_path = self.control_main_ant_moves(pos)
            else:
                new_path = self.control_stupid_ant_moves(pos)
            # new_path = self.choose_next_path(pos, None, self.get_speed(unit["type"]))[0]
            print(new_path)
            # if unit["food"]["amount"] != 0:
            #     new_path = self.do_return(uid, self.get_speed(unit["type"]))
            # else:
            self.update_memory(uid, new_path)
            if new_path is None:
                continue
            
            moves.append((uid, [self.serialize_data(i) for i in new_path]))
        self.do_move(moves)


def mock_event_loop(render=True):
    if render:
        from visualizer import HexGridVisualizer
        path = str(time.time_ns())
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

    policy = ChainPolicy(TOKEN=TOKEN, MOVE_ENDPOINT=MOVE_ENDPOINT)
    while True:
        state = requests.get(STATE_ENDPOINT, params={"token": TOKEN}).json()
        print(state)
        ttl = state["nextTurnIn"]
        try:
            policy(state)
        except Exception as e:
            print("Ошибка:", e)
            raise
        
        if render:
            print(f"SAVING IN {path}")
            visualizer = HexGridVisualizer(state)
            visualizer.visualize(save=True, path=path)
            plt.close()
        time.sleep(ttl)


mock_event_loop(render=True)
