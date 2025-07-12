import math

import click
import json
import matplotlib.pyplot as plt
import numpy as np

import time
import os

from matplotlib.collections import PatchCollection
from matplotlib.patches import RegularPolygon


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
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
        # Определяем границы карты
        all_q = [hex['q'] for hex in game_data['map']]
        all_r = [hex['r'] for hex in game_data['map']]
        self.q_min, self.q_max = min(all_q) - 2, max(all_q) + 2
        self.r_min, self.r_max = min(all_r) - 2, max(all_r) + 2
        
    def axial_to_pixel(self, q, r):
        """Конвертация осевых координат (q, r) в пиксельные (x, y)"""
        x = self.hex_size * (3/2 * q)
        y = self.hex_size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
        return (x, y)
    
    def draw_map(self):
        """Отрисовка карты с учетом типов местности из документации"""
        patches = []
        colors = []
        edgecolors = []
        linewidths = []
        
        # Типы местности и их оформление согласно документации
        terrain_properties = {
            1: {'color': "#B60BA8", 'hatch': None, 'edgecolor': 'k', 'linewidth': 1},  # Муравейник (коричневый)
            2: {'color': '#F5F5DC', 'hatch': None, 'edgecolor': 'k', 'linewidth': 1},  # Пустой (бежевый)
            3: {'color': '#A0522D', 'hatch': None, 'edgecolor': 'k', 'linewidth': 1},  # Грязь (коричневый)
            4: {'color': '#32CD32', 'hatch': '...', 'edgecolor': 'red', 'linewidth': 1.5},  # Кислота (зеленый с точками)
            5: {'color': '#696969', 'hatch': '////', 'edgecolor': 'k', 'linewidth': 2}   # Камни (серый с диагоналями)
        }
        
        # Рисуем все гексы карты
        for hex_cell in self.game_data['map']:
            q, r = hex_cell['q'], hex_cell['r']
            x, y = self.axial_to_pixel(q, r)
            
            terrain_type = hex_cell['type']
            props = terrain_properties.get(terrain_type, 
                                         {'color': '#DDDDDD', 'hatch': None, 'edgecolor': 'k', 'linewidth': 1})
            
            hexagon = RegularPolygon(
                (x, y),
                numVertices=6,
                radius=self.hex_size,
                orientation=np.pi/6,
                facecolor=props['color'],
                edgecolor=props['edgecolor'],
                hatch=props['hatch'],
                linewidth=props['linewidth'],
                alpha=0.8
            )
            patches.append(hexagon)
            colors.append(props['color'])
            edgecolors.append(props['edgecolor'])
            linewidths.append(props['linewidth'])
        
        # Добавляем все гексы на график
        collection = PatchCollection(patches, match_original=True)
        collection.set_facecolor(colors)
        collection.set_edgecolor(edgecolors)
        collection.set_linewidth(linewidths)
        self.ax.add_collection(collection)
    
    def draw_ants(self):
        """Отрисовка муравьев (черные точки)"""
        for ant in self.game_data['ants']:
            q, r = ant['q'], ant['r']
            x, y = self.axial_to_pixel(q, r)
            
            # Все муравьи - черные точки, размером в 1/4 гекса
            self.ax.plot(x, y, 'o', color='black', markersize=self.hex_size*2, alpha=0.9)
    
    def draw_food(self):
        """Отрисовка еды (красные точки)"""
        for food in self.game_data['food']:
            q, r = food['q'], food['r']
            x, y = self.axial_to_pixel(q, r)
            
            # Все виды еды - красные точки, размер зависит от количества
            size = 8
            self.ax.plot(x, y, 'o', color='red', markersize=size, alpha=0.8)
    
    def draw_home(self):
        """Отрисовка базы (фиолетовые шестиугольники с обводкой)"""
        for home in self.game_data['home']:
            q, r = home['q'], home['r']
            x, y = self.axial_to_pixel(q, r)
            
            hexagon = RegularPolygon(
                (x, y),
                numVertices=6,
                radius=self.hex_size*0.7,
                orientation=np.pi/6,
                facecolor='purple',
                edgecolor='k',
                linewidth=1.5,
                alpha=0.7
            )
            self.ax.add_patch(hexagon)
    
    def draw_spot(self):
        """Отрисовка специальной точки (золотой шестиугольник)"""
        spot = self.game_data['spot']
        if spot:
            q, r = spot['q'], spot['r']
            x, y = self.axial_to_pixel(q, r)
            
            hexagon = RegularPolygon(
                (x, y),
                numVertices=6,
                radius=self.hex_size*0.5,
                orientation=np.pi/6,
                facecolor='gold',
                edgecolor='k',
                linewidth=1,
                alpha=0.8
            )
            self.ax.add_patch(hexagon)
    
    def visualize(self, save=False, path=""):
        """Основной метод визуализации"""
        self.draw_map()
        self.draw_food()
        self.draw_home()
        self.draw_spot()
        self.draw_ants()
        
        # Настройки отображения
        plt.title(f"Ants Simulation - Turn {self.game_data['turnNo']}\nScore: {self.game_data['score']}", 
                 pad=20, fontsize=12)
        plt.tight_layout()
        
        # Легенда с типами местности
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#8B4513', edgecolor='k', label='Муравейник (1)'),
            Patch(facecolor='#F5F5DC', edgecolor='k', label='Пустой (2)'),
            Patch(facecolor='#A0522D', edgecolor='k', label='Грязь (3)'),
            Patch(facecolor='#32CD32', edgecolor='red', hatch='...', label='Кислота (4)'),
            Patch(facecolor='#696969', edgecolor='k', hatch='////', label='Камни (5)'),
            Patch(facecolor='black', edgecolor='k', label='Муравьи'),
            Patch(facecolor='red', edgecolor='k', label='Еда'),
            Patch(facecolor='purple', edgecolor='k', label='База'),
            Patch(facecolor='gold', edgecolor='k', label='Спецточка')
        ]
        
        self.ax.legend(handles=legend_elements, loc='upper right', 
                      bbox_to_anchor=(1.25, 1), fontsize=10, title="Легенда")
        
        if save:
            plt.savefig(os.path.join(path, f"image_{time.time()}.png"))
        else:
            plt.show()



@click.command()
@click.option("--json_file", "-j", help="path to JSON to render", default="example.json")
def main(json_file):

    with open(json_file, "r") as stream:
        game_data = json.load(stream)
    
    visualizer = HexGridVisualizer(game_data)
    visualizer.visualize()
    import time
    time.sleep(0.5)
    plt.close('all')


# Пример использования
if __name__ == "__main__":
    main()
