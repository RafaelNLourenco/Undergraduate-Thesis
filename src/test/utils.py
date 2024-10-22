import cv2
import re
import numpy as np
from collections import Counter
from PIL import Image
from metrics import *
from typing import List
from enum import Enum
from itertools import combinations
import time

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import generate_map

DIMENSION = (300, 300)
COLOR_MAP = np.array([[0.5,0.5,0.5],
                      [  0,  1,  0],
                      [  1,  0,  0],
                      [  1,  1,  1]])

class GENERATE_PARAM(Enum):
    POINTS = 1
    KERNEL_SIZE = 2
    BORDER_SIZE = 3

class SORT_METHOD(Enum):
    NOT_REVERSE = 0
    REVERSE = 1
    NOT_SORT = 2

class IMAGES(Enum):
    INPUT = 1
    OUTPUT_2D = 2
    OUTPUT_3D = 3

def showImg(img):
    cv2.imshow("Window", img)
    cv2.waitKey(0)

def numpytoimage(numpy):
    numpy = numpy * 255
    image= Image.fromarray(numpy.astype(np.uint8))
    return image

def get_char_for_number(i):
    return chr(i + 64)

def sortDict(curr_dict, column, reverse = False):
    return dict(sorted(curr_dict.items(), key=lambda x: x[1][column], reverse=reverse))

def selectGtAndPrediction(input, im_comb):
    map_2d = cv2.imread("unity/3d_map/Assets/Resources/output_2d.png")
    ocean_color = (255,191,0)
    mask = cv2.inRange(map_2d, ocean_color, ocean_color)
    map_2d = cv2.bitwise_not(mask)
    map_2d_resized = cv2.resize(map_2d, DIMENSION)

    map_3d = cv2.imread("output_3d.png", 0)
    map_3d_resized = cv2.resize(map_3d, DIMENSION)

    if IMAGES.INPUT in im_comb:
        if IMAGES.OUTPUT_2D in im_comb:
            return input, map_2d_resized
        else:
            return input, map_3d_resized
    else:
        return map_2d_resized, map_3d_resized

def getSetClassification(gt, prediction):
    _, thresh_gt = cv2.threshold(gt, 1, 1, 0)
    _, thresh_prediction = cv2.threshold(prediction, 1, 2, 0)

    # Create new image as numpy matrix with sum of two masks
    result_set = COLOR_MAP[thresh_gt + thresh_prediction]

    # Modiffy to counterer occurrences
    result_set_reshaped = result_set.reshape(-1, result_set.shape[-1])
    result_set_tuples =  [tuple(x) for x in result_set_reshaped]
    result_set_counter = Counter(result_set_tuples)

    # True Positive
    counter_TP = result_set_counter[tuple([1, 1, 1])]

    # True Negative
    counter_TN = result_set_counter[tuple([0.5, 0.5, 0.5])]

    # False Negative
    counter_FN = result_set_counter[tuple([0, 1, 0])]

    # False Positive
    counter_FP = result_set_counter[tuple([1, 0, 0])]

    # Visualize result set
    result_set_image = numpytoimage(result_set)
    result_set_image.save("result_set.png")

    return counter_TP, counter_TN, counter_FP, counter_FN, result_set_image

def isSetClassificationMetric(metric):
    return not metric == METRICS_NAME.BLUR and not metric == METRICS_NAME.DURATION

def testCase(start_img_id: int, end_img_id: int, start_param: int, end_param: int, param_step: int, metrics_name: List[METRICS_NAME],
             repeat: int, filename: str, generate_mode: int, generate_param: GENERATE_PARAM, images: List[IMAGES], output_generate = 1,
             sort_method: SORT_METHOD = SORT_METHOD.NOT_SORT):

    results = []
    metrics_quantity = len(metrics_name)
    images_combination = list(combinations(images, 2))

    for comb_idx, im_comb in enumerate(images_combination):
        results.append({})
        rs_image = None
        print(f'Combinacao {comb_idx} do {im_comb[0].name} -> {im_comb[1].name}')

        for img_num in range(start_img_id, end_img_id + 1):
            print(f'Imagem {img_num}')

            input = cv2.imread(f'src/test/images/test-{img_num}.png', 0)
            input_resized = cv2.resize(input, DIMENSION)
            img = cv2.cvtColor(input_resized, cv2.COLOR_BGR2RGB)
            im_pil = Image.fromarray(img)


            for param_num in range(start_param, end_param + 1, param_step):
                metrics = np.zeros(metrics_quantity)
                for j in range (0, repeat):
                    time_duration = 0
                    while True:
                        try:
                            start_time = time.time()
                            if generate_param == GENERATE_PARAM.POINTS:
                                generate_map.generate(im_pil, points=param_num, mode=generate_mode, kernel_size=80, output=output_generate)
                            if generate_param == GENERATE_PARAM.KERNEL_SIZE:
                                generate_map.generate(im_pil, points=150, mode=generate_mode, kernel_size=param_num, output=output_generate)
                            if generate_param == GENERATE_PARAM.BORDER_SIZE:
                                generate_map.generate(im_pil, points=150, mode=generate_mode, kernel_size=80, output=output_generate, border_size=param_num)
                            end_time = time.time()
                            time_duration = end_time - start_time
                            break
                        except Exception as e:
                            print(f"Ocorreu um erro: {e}. Tentando novamente...")
                    gt, prediction = selectGtAndPrediction(input, im_comb)

                    TP, TN, FP, FN, rs_image = getSetClassification(gt, prediction)

                    # evaulate metrics
                    for metric_idx, metric in enumerate(metrics_name):
                        if isSetClassificationMetric(metric):
                            metrics[metric_idx] += METRICS_DICT[metric][0](TP, TN, FP, FN)
                        elif metric == METRICS_NAME.BLUR:
                            metrics[metric_idx] += METRICS_DICT[metric][0](prediction)
                        elif metric == METRICS_NAME.DURATION:
                            metrics[metric_idx] += time_duration
                        else:
                            print(f"Métrica: {metric.name} não encontrada.")

                if not isinstance(results[comb_idx].get(param_num), np.ndarray):
                    results[comb_idx][param_num] = np.zeros(metrics_quantity)
                results[comb_idx][param_num] += metrics
        rs_image.save(f'result_set_{im_comb[0].name.lower()}_{im_comb[1].name.lower()}.png')

    for curr_bomb_idx, curr_comb in enumerate(results):
        if not sort_method == SORT_METHOD.NOT_SORT:
            curr_comb = sortDict(curr_comb, 0, reverse=bool(sort_method.value))
        for key, value in curr_comb.items():
            for i in range(len(value)):
                value[i] = f'{ (value[i] / (repeat * (end_img_id + 1 - start_img_id))):.5f}'
            curr_comb[key] = value.astype(str)
        results[curr_bomb_idx] = curr_comb

    print(results)
    saveTable(results, metrics_name, generate_param, filename, images_combination)


def saveTable(results, metrics, param: GENERATE_PARAM, filename, images_combination):
    with open(f'latex/{filename}.tex', "w", encoding='utf-8') as f:
        backreturn = "\\\\\n" + " "*8
        file_str = ""

        columns_str = ""
        if param == GENERATE_PARAM.KERNEL_SIZE:
            columns_str = "Tamanho filtro"
        elif param == GENERATE_PARAM.POINTS:
            columns_str = "Pontos"
        else:
            columns_str = "Tamanho borda"

        columns_str += ''.join(
            [
                f" & {METRICS_DICT[_metric][1]}"
                for _, _metric in enumerate(metrics)
            ])

        for curr_comb_idx, curr_comb in enumerate(results):
            content = backreturn.join(
            [
                f"{_k} & {' & '.join(_v.astype(str))}"
                for _k, _v in curr_comb.items()
            ])

            gt_str = images_combination[curr_comb_idx][0].name.lower()
            pd_str = images_combination[curr_comb_idx][1].name.lower()

            file_str += re.sub(r"\s{16}(?=\{|\d|\\)", "",
                        f"""
                        \\begin{{table}}[h]
                            \\centering
                            \\caption{{Resultados dos testes {gt_str.replace("_", " ")} {pd_str.replace("_", " ")}}}
                            \\label{{tab:{filename}_{gt_str}_{pd_str}}}
                            \\begin{{tabular}}{{{'|c|' + 'c|' * (len(metrics)) }}}
                                \\hline
                                {columns_str} \\\\
                                \\hline
                                {content}\\\\
                                \\hline
                            \\end{{tabular}}
                        \\end{{table}}
                        """.strip()) + "\n\n\n"

        f.write(file_str)