import logging
import random
from enum import Enum

from map_geration.draw_map import convert_map_to_3d_image
from map_geration.graph import *
from map_geration.map import *
from map_geration.terrain import *

class OUTPUT(Enum):
    BOTH = 1
    MAP_2D = 2
    MAP_3D = 3
    MAP_BIOME = 4


def generate(image, points=25, mode = 3, output: OUTPUT = OUTPUT.BOTH, kernel_size=80, border_size = 60):
    logging.info("Gerando diagrama de Voronoi")
    graph = Graph(N=points, iterations=2)

    logging.info("Definindo biomas")
    assign_terrain_from_image(image, graph)

    logging.info("Calculando elevação")
    assign_corner_elevations(graph)
    redistribute_elevations(graph)
    assign_center_elevations(graph)

    # logging.info("Gerando imagem 2D")
    # convert_map_to_image(graph, path="output_2d", border_size=border_size)

    logging.info("Gerando imagem 3D")
    convert_map_to_3d_image(graph, mode=mode, kernel_size=kernel_size, path="output_3d")

    logging.info("Gerando biomas")

    number_of_rivers = 5
    logging.info(f"Sera gerado um total de {number_of_rivers} rios")
    create_rivers(graph, number_of_rivers, 0.6)

    logging.info(f"Calculando umidade")
    assign_moisture(graph)

    logging.info(f"Selecionando biomas")
    assign_biomes(graph)

    logging.info(f"Gerando imagem bioma")
    image = convert_map_to_image(
        graph,
        path="output_2d",
        plot_type='biome',
        debug_height=False, 
        debug_moisture=False, 
        downslope_arrows=False, 
        rivers=True
    )    
    
    return image
