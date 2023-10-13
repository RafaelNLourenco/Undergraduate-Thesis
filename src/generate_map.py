import logging


from map_geration.graph import *
from map_geration.map import convert_map_to_image
from map_geration.draw_map import  convert_map_to_3d_image
from map_geration.terrain import *


def generate(image, points=25):
    logging.info("Gerando diagrama de Voronoi")
    graph = Graph(N=points, iterations=2)

    logging.info("Definindo biomas")
    assign_terrain_from_image(image, graph)

    logging.info("Calculando elevação")
    assign_corner_elevations(graph)
    redistribute_elevations(graph)
    assign_center_elevations(graph)

    logging.info("Gerando imagem 3D")
    convert_map_to_3d_image(graph, path="output_3d")

    logging.info("Gerando imagem 2D")
    return convert_map_to_image(graph, path="output_2d")