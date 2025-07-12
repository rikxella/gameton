import math

import click
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Circle, RegularPolygon

import json


class HexGridVisualizer:
    def __init__(self, game_data, hex_size=1.0):
        """
        Инициализация визуализатора гексагонального поля

        :param game_data: JSON-данные игры
        :param hex_size: Размер гекса (радиус описанной окружности)
        """
        self.game_data = game_data
        self.hex_size = hex_size
        self.fig, self.ax = plt.subplots(figsize=(15, 15))
        self.ax.set_aspect("equal")
        self.ax.axis("off")

        # Определяем границы карты
        self.q_min = min(hex["q"] for hex in game_data["map"]) - 2
        self.q_max = max(hex["q"] for hex in game_data["map"]) + 2
        self.r_min = min(hex["r"] for hex in game_data["map"]) - 2
        self.r_max = max(hex["r"] for hex in game_data["map"]) + 2

    def axial_to_pixel(self, q, r):
        """Конвертация осевых координат (q, r) в пиксельные (x, y)"""
        x = self.hex_size * (3 / 2 * q)
        y = self.hex_size * (math.sqrt(3) / 2 * q + math.sqrt(3) * r)
        return (x, y)

    def draw_map(self):
        """Отрисовка карты"""
        patches = []
        colors = []

        # Типы клеток и их цвета
        terrain_colors = {
            1: "#8B4513",  # Земля
            2: "#228B22",  # Трава
            3: "#1E90FF",  # Вода
            4: "#A9A9A9",  # Камень
            5: "#FFD700",  # Песок
        }

        # Рисуем все гексы карты
        for hex_cell in self.game_data["map"]:
            q, r = hex_cell["q"], hex_cell["r"]
            x, y = self.axial_to_pixel(q, r)

            color = terrain_colors.get(hex_cell["type"], "#DDDDDD")

            hexagon = RegularPolygon(
                (x, y),
                numVertices=6,
                radius=self.hex_size,
                orientation=np.pi / 6,
                facecolor=color,
                edgecolor="k",
                alpha=0.7,
            )
            patches.append(hexagon)
            colors.append(color)

        # Добавляем все гексы на график
        self.ax.add_collection(PatchCollection(patches, facecolor=colors))

    def draw_ants(self):
        """Отрисовка муравьев"""
        for ant in self.game_data["ants"]:
            q, r = ant["q"], ant["r"]
            x, y = self.axial_to_pixel(q, r)

            # Цвет в зависимости от типа муравья
            ant_color = {0: "red", 1: "blue", 2: "green"}.get(ant["type"], "black")  # Рабочий  # Воин  # Разведчик

            # Размер в зависимости от здоровья
            size = 10 + ant["health"] / 10

            self.ax.plot(x, y, "o", color=ant_color, markersize=size, label=f"Ant {ant['id'][:4]}")

            # Если есть еда - рисуем маленький кружок внутри
            if ant["food"]["amount"] > 0:
                food_color = "#FF69B4" if ant["food"]["type"] == 1 else "#FF4500"
                self.ax.plot(x, y, "o", color=food_color, markersize=size / 3)

    def draw_food(self):
        """Отрисовка еды"""
        for food in self.game_data["food"]:
            q, r = food["q"], food["r"]
            x, y = self.axial_to_pixel(q, r)

            food_color = "#FF69B4" if food["type"] == 1 else "#FF4500"
            size = min(10, 5 + food["amount"] / 3)

            self.ax.plot(x, y, "h", color=food_color, markersize=size, alpha=0.8)

    def draw_home(self):
        """Отрисовка базы"""
        for home in self.game_data["home"]:
            q, r = home["q"], home["r"]
            x, y = self.axial_to_pixel(q, r)

            self.ax.plot(x, y, "s", color="purple", markersize=15, alpha=0.7)

    def draw_spot(self):
        """Отрисовка специальной точки"""
        spot = self.game_data["spot"]
        if spot:
            q, r = spot["q"], spot["r"]
            x, y = self.axial_to_pixel(q, r)

            self.ax.plot(x, y, "*", color="cyan", markersize=20, alpha=0.9)

    def draw_last_moves(self):
        """Отрисовка последних перемещений"""
        for ant in self.game_data["ants"]:
            if "lastMove" in ant and len(ant["lastMove"]) >= 2:
                path = [(p["q"], p["r"]) for p in ant["lastMove"]]
                x_coords = []
                y_coords = []
                for q, r in path:
                    x, y = self.axial_to_pixel(q, r)
                    x_coords.append(x)
                    y_coords.append(y)

                self.ax.plot(x_coords, y_coords, "--", color="yellow", linewidth=1, alpha=0.5)

    def visualize(self):
        """Основной метод визуализации"""
        self.draw_map()
        self.draw_food()
        self.draw_home()
        self.draw_spot()
        self.draw_ants()
        self.draw_last_moves()

        # Настройки отображения
        plt.title(f"Ants Simulation - Turn {self.game_data['turnNo']}\nScore: {self.game_data['score']}", pad=20)
        plt.tight_layout()

        # Легенда
        from matplotlib.lines import Line2D

        legend_elements = [
            Line2D([0], [0], marker="o", color="w", label="Worker", markerfacecolor="red", markersize=10),
            Line2D([0], [0], marker="o", color="w", label="Warrior", markerfacecolor="blue", markersize=10),
            Line2D([0], [0], marker="o", color="w", label="Scout", markerfacecolor="green", markersize=10),
            Line2D([0], [0], marker="h", color="w", label="Food Type 1", markerfacecolor="#FF69B4", markersize=10),
            Line2D([0], [0], marker="h", color="w", label="Food Type 2", markerfacecolor="#FF4500", markersize=10),
            Line2D([0], [0], marker="s", color="w", label="Home", markerfacecolor="purple", markersize=10),
            Line2D([0], [0], marker="*", color="w", label="Special Spot", markerfacecolor="cyan", markersize=10),
        ]

        self.ax.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(1.3, 1))
        # plt.savefig('ants_simulation.png', dpi=300, bbox_inches='tight')
        plt.show()



@click.command()
@click.option("--json_file", "-j", help="path to JSON to render", default="sample_json.json")
def main(json_file):

    with open(json_file, "r") as stream:
        game_data = json.load(stream)
    
    visualizer = HexGridVisualizer(game_data)
    visualizer.visualize()


# Пример использования
if __name__ == "__main__":
    # Здесь должен быть ваш JSON-объект с данными игры
    # game_data = None

    # visualizer = HexGridVisualizer(game_data)
    # visualizer.visualize()
    main()
