"""
-*- coding: utf-8 -*-
@Author: Xuanxin Tian
@Email  : 17710116575@163.com
@Create  : 2022/11/21 19:50
"""
from math import sqrt, pow
import numpy as np


class ApproxPoly:
    def __init__(self):
        self.threshold = None
        self.qualify_list = list()
        self.disqualify_list = list()

    def douglas_peuker(self, point_list, threshold):

        self.threshold = threshold
        self.diluting_dp(point_list)
        while len(self.disqualify_list) > 0:
            self.diluting_dp(self.disqualify_list.pop())
        return self.qualify_list

    def diluting_dp(self, point_list):
        if len(point_list) < 3:
            self.qualify_list.extend(point_list[::-1])
        else:

            max_distance_index, max_distance = 0, 0
            for index, point in enumerate(point_list):
                if index in [0, len(point_list) - 1]:
                    continue
                distance = point_2_line_distance(point, point_list[0], point_list[-1])
                if distance > max_distance:
                    max_distance_index = index
                    max_distance = distance

            if max_distance < self.threshold:
                self.qualify_list.append(point_list[-1])
                self.qualify_list.append(point_list[0])
            else:

                sequence_a = point_list[:max_distance_index]
                sequence_b = point_list[max_distance_index:]

                for sequence in [sequence_a, sequence_b]:
                    if len(sequence) < 3 and sequence == sequence_b:
                        self.qualify_list.extend(sequence[::-1])
                    else:
                        self.disqualify_list.append(sequence)

    def limit_vertical_distance(self, point_list, threshold):

        self.threshold = threshold
        self.qualify_list.append(point_list[0])
        check_index = 1
        while check_index < len(point_list) - 1:
            distance = point_2_line_distance(point_list[check_index],
                                             self.qualify_list[-1],
                                             point_list[check_index + 1])
            if distance < self.threshold:
                check_index += 1
            else:
                self.qualify_list.append(point_list[check_index])
                check_index += 1
        return self.qualify_list

    def limit_accu_distance(self, point_list, size):

        self.qualify_list.append(point_list[0])
        dis_accu = 0
        for i in range(0, len(point_list) - 1):
            dis = np.sqrt(np.sum([(point_list[i][0] - point_list[i + 1][0]) ** 2,
                                  (point_list[i][1] - point_list[i + 1][1]) ** 2]))
            dis_accu = dis_accu + dis
            if dis_accu > size:
                self.qualify_list.append(point_list[i])
                dis_accu = 0
        dis_end = np.sqrt(np.sum([(self.qualify_list[0][0] - self.qualify_list[-1][0]) ** 2,
                                  (self.qualify_list[0][1] - self.qualify_list[-1][1]) ** 2]))
        if dis_end < size / 2:
            self.qualify_list.pop()
        return self.qualify_list

    def dp_limit_accu_distance(self, point_list, size, threshold):

        feature_point = self.douglas_peuker(point_list, threshold)
        self.qualify_list=[]
        self.qualify_list.append(point_list[0])
        dis_accu = 0
        for i in range(0, len(point_list) - 1):
            dis = np.sqrt(np.sum([(point_list[i][0] - point_list[i + 1][0]) ** 2,
                                  (point_list[i][1] - point_list[i + 1][1]) ** 2]))
            dis_accu = dis_accu + dis
            if dis_accu > size or (point_list[i] in feature_point and dis_accu > size / 2):
                self.qualify_list.append(point_list[i])
                dis_accu = 0
        dis_end = np.sqrt(np.sum([(self.qualify_list[0][0] - self.qualify_list[-1][0]) ** 2,
                                  (self.qualify_list[0][1] - self.qualify_list[-1][1]) ** 2]))
        if dis_end < size / 2:
            self.qualify_list.pop()
        return self.qualify_list


def point_2_line_distance(point_a, point_b, point_c):

    if point_b[0] == point_c[0]:
        return 9999999
    slope = (point_b[1] - point_c[1]) / (point_b[0] - point_c[0])
    intercept = point_b[1] - slope * point_b[0]

    distance = abs(slope * point_a[0] - point_a[1] + intercept) / sqrt(1 + pow(slope, 2))
    return distance


def calculate_curvature(x_value, y_value):

    x_t = np.gradient(x_value)
    y_t = np.gradient(y_value)
    xx_t = np.gradient(x_t)
    yy_t = np.gradient(y_t)
    curvature_val = np.abs(xx_t * y_t - x_t * yy_t) / (x_t * x_t + y_t * y_t) ** 1.5
    return curvature_val
