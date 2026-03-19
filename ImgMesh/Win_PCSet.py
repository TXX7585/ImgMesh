from SimpleITK import CannyEdgeDetectionImageFilter, Cast, GetArrayFromImage, sitkFloat32
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication
from PyQt5 import QtCore
import cv2
import open3d as o3d
from ImgMesh.Ui.Ui_PC_Setting import Ui_PC_SETTING
import numpy as np

from ImgMesh.tools import point2polygon, vtk_image_to_numpy, vtk2sitk, create_nodes_inpolygon


class Win_PCSet(QWidget, Ui_PC_SETTING):
    PC_signal = QtCore.pyqtSignal(dict, np.ndarray)

    def __init__(self, model_object):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(':/icon/set.png'))

        self.model_object = model_object
        self.pc_info = {}
        self.polygon = np.empty((0, 4), dtype=float)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.cancel)

        self.cbx_algorithm.addItem("2D Canny")
        self.cbx_algorithm.addItem("3D Canny")

        self.cbx_algorithm.currentIndexChanged.connect(self.algorithm_changed)
        self.cbx_inputimage.currentIndexChanged.connect(self.image_range_changed)

    def algorithm_changed(self):
        if self.cbx_algorithm.currentText() == '2D Canny':
            self.label_imageint.setText('Slice interval')
            self.le_imageinterval.setText('1')
            self.label_dpthreshold.setText('DP threshold')
            self.image_range_changed()
        elif self.cbx_algorithm.currentText() == '3D Canny':
            self.label_imageint.setText('Variance')
            self.le_imageinterval.setText('3')
            self.label_dpthreshold.setText('MaximumError')
            self.le_dpthreshold.setText('0.5')
            self.label_imagerange.setText('Threshold')
            self.le_firstimage.setText('1')
            self.le_lastimage.setText('1')
            self.image_range_changed()

    def image_range_changed(self):
        current_image = self.cbx_inputimage.currentText()
        if not len(current_image) == 0:
            self.dimen = self.model_object[current_image]['vtkimage'].GetDimensions()
            self.le_firstimage.setText('1')
            self.le_lastimage.setText(str(self.dimen[2]))

    def accept(self):
        firstimage = int(self.le_firstimage.text())
        lastimage = int(self.le_lastimage.text())
        self.vtkimage = self.model_object[self.cbx_inputimage.currentText()]['vtkimage']
        self.resolution = self.model_object[self.cbx_inputimage.currentText()]['resolution']

        if lastimage > self.dimen[2]:
            QMessageBox.critical(self, "Error", "Out of range!")
        elif firstimage > lastimage:
            QMessageBox.critical(self, "Error", "Error!")
        else:
            self.pc_info = {}
            self.pc_info = {
                'algorithm': self.cbx_algorithm.currentText(),
                'imagename': self.cbx_inputimage.currentText(),
                'firstimage': firstimage,
                'lastimage': lastimage,
                'imageinterval': self.le_imageinterval.text(),
                'gridsize': float(self.le_gridsize.text()),
                'dpthreshold': self.le_dpthreshold.text(),
            }

            if self.cbx_algorithm.currentIndex() == 0:
                self.image2point()
            else:
                self.canny_edge_3d()
                if self.pc_info['gridsize'] >= 1:
                    pcd = o3d.geometry.PointCloud()
                    pcd.points = o3d.utility.Vector3dVector(self.polygon)

                    voxel_down_pcd = pcd.voxel_down_sample(voxel_size=self.pc_info['gridsize'])
                    self.polygon = np.asarray(voxel_down_pcd.points)
                    self.polygon = np.column_stack((np.full(len(self.polygon), 0), self.polygon))

            if self.polygon.shape[0] > 0:
                self.PC_signal.emit(self.pc_info, self.polygon)
                self.close()

    def canny_edge_3d(self):

        variance = float(self.pc_info['imageinterval'])
        maxerror = float(self.pc_info['dpthreshold'])
        maxerror = max(0.01, min(maxerror, 0.99))

        lowerthreshold = self.pc_info['firstimage']
        upperthreshold = self.pc_info['lastimage']

        itk_data = vtk2sitk(self.vtkimage)
        image_float = Cast(itk_data, sitkFloat32)
        canny_filter = CannyEdgeDetectionImageFilter()
        canny_filter.SetUpperThreshold(upperthreshold)
        canny_filter.SetLowerThreshold(lowerthreshold)
        canny_filter.SetVariance(variance)
        canny_filter.SetMaximumError(maxerror)
        canny_sitk = canny_filter.Execute(image_float)
        output = GetArrayFromImage(canny_sitk)
        indices = np.transpose(np.where(output == 1))
        self.polygon = indices[:, [2, 1, 0]]
        self.polygon = np.column_stack((self.polygon[:, 0] * self.resolution[0],
                                        self.polygon[:, 1] * self.resolution[1],
                                        self.polygon[:, 2] * self.resolution[2],))

    def cancel(self):
        self.close()

    def image2point(self):
        # define the interval
        slice_number = self.pc_info['lastimage'] - self.pc_info['firstimage']
        if self.pc_info['imageinterval']:
            interval = int(self.pc_info['imageinterval'])
        else:
            interval = self.pc_info['gridsize'] / 2 * 3 ** 0.5

        if slice_number > 0:
            slice_sequence = np.linspace(0, slice_number - 1,
                                         round(slice_number / interval), dtype=int)
        else:
            slice_sequence = np.array([0])
        # slice_sequence = np.linspace(0, slice_number - 1,
        #                                  round(slice_number / interval), dtype=int)

        # convert vtk to numpy data
        numpy_image = vtk_image_to_numpy(self.vtkimage)
        unique_values = np.unique(numpy_image)
        if len(unique_values) > 2 or (0 not in unique_values) or (255 not in unique_values):
            QMessageBox.critical(self, "Error", "Please input binary data!")
        else:
            if slice_sequence.shape[0] > 1:
                for num in slice_sequence:
                    img = numpy_image[num, :, :]
                    contours, hierarchy = cv2.findContours(img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
                    if hierarchy is None:
                        continue
                    hierarchy = hierarchy[0]

                    def contour_center(contour):
                        moments = cv2.moments(contour)
                        if moments["m00"]>0:
                            cx = int(moments["m10"] / moments["m00"])
                            cy = int(moments["m01"] / moments["m00"])
                        else:
                            cx =0
                            cy=0
                        return cx, cy

                    if len(contours) > 1:
                        contours = sorted(contours, key=lambda x: contour_center(x))
                    else:
                        contours = np.array(contours)

                    # label the contours by hierarchy
                    if hierarchy.shape[0] == 1:
                        # only one outer contour(noholes)
                        bound = contours.reshape(-1, 2)
                        bound = np.column_stack((bound, np.full(len(bound), num)))
                        if self.pc_info['gridsize'] > 1:
                            polygon = point2polygon(bound[:, :2], float(self.pc_info['dpthreshold']),
                                                    self.pc_info['gridsize'])
                            polygon = np.column_stack((polygon, np.full(len(polygon), num)))

                            if num == 0 or num == slice_sequence[-1]:
                                innerNodes = create_nodes_inpolygon(polygon, self.pc_info['gridsize'], 0.8, [])
                                polygon = np.row_stack((polygon, innerNodes))
                        else:
                            polygon = bound
                        polygon = np.column_stack((np.full(len(polygon), 0), polygon))
                        self.polygon = np.row_stack((self.polygon, polygon))

                    elif hierarchy.shape[0] > 1:
                        # multiple outer contours
                        out_idx = 0
                        out_sequence = np.where(hierarchy[:, 0] > 0)[0]
                        for out_ii in range(len(out_sequence) + 1):
                            out_bound = contours[out_idx].reshape(-1, 2)
                            out_bound = np.column_stack((out_bound, np.full(len(out_bound), num)))
                            if self.pc_info['gridsize'] > 1 and out_bound.shape[0] > 2:
                                out_polygon = point2polygon(out_bound[:, :2], float(self.pc_info['dpthreshold']),
                                                            self.pc_info['gridsize'])
                                out_polygon = np.column_stack((out_polygon, np.full(len(out_polygon), num)))
                            else:
                                out_polygon = out_bound
                            out_polygon = np.column_stack((np.full(len(out_polygon), out_ii), out_polygon))
                            if out_polygon.shape[0] > 1:
                                self.polygon = np.row_stack((self.polygon, out_polygon))

                            in_bound = []
                            in_idx = np.where(hierarchy[:, 3] == out_idx)[0]

                            for contour_idx in in_idx:
                                bound = contours[contour_idx].reshape(-1, 2)
                                bound = np.column_stack((bound, np.full(len(bound), num)))
                                if self.pc_info['gridsize'] > 1 and bound.shape[0] > 2:
                                    polygon = point2polygon(bound[:, :2], float(self.pc_info['dpthreshold']),
                                                            self.pc_info['gridsize'])
                                    polygon = np.column_stack((polygon, np.full(len(polygon), num)))

                                else:
                                    polygon = bound
                                in_bound.append(polygon)
                                polygon = np.column_stack((np.full(len(polygon), out_ii), polygon))
                                if polygon.shape[0] > 1:
                                    self.polygon = np.row_stack((self.polygon, polygon))

                            if num == 0 or num == slice_sequence[-1]:
                                if out_polygon.shape[0] < 2:
                                    continue
                                innerNodes = create_nodes_inpolygon(out_polygon[:, 1:], self.pc_info['gridsize'], 0.8,
                                                                    in_bound)
                                innerNodes = np.column_stack((np.full(len(innerNodes), out_ii), innerNodes))
                                self.polygon = np.row_stack((self.polygon, innerNodes))
                            out_idx = hierarchy[out_idx, 0]

                self.polygon = np.column_stack((self.polygon[:, 0],
                                                self.polygon[:, 1] * self.resolution[0],
                                                self.polygon[:, 2] * self.resolution[1],
                                                self.polygon[:, 3] * self.resolution[2],))
            else:  # 2D mesh
                img = numpy_image[0, :, :]
                contours, hierarchy = cv2.findContours(img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
                hierarchy = hierarchy[0]
                if hierarchy.shape[0] == 1:
                    for contour_idx, contour in enumerate(contours):
                        bound = contour.reshape(-1, 2)
                        bound = np.column_stack((bound, np.full(len(bound), 0)))

                        if self.pc_info['gridsize'] > 1:
                            polygon = point2polygon(bound[:, :2], float(self.pc_info['dpthreshold']),
                                                    self.pc_info['gridsize'])
                            polygon = np.column_stack((polygon, np.full(len(polygon), 0)))
                        else:
                            polygon = bound
                        polygon = np.column_stack((np.full(len(polygon), contour_idx), polygon))

                        self.polygon = np.row_stack((self.polygon, polygon))
                else:
                    out_idx = 0
                    out_sequence = np.where(hierarchy[:, 3] < 0)[0]
                    for out_ii in range(len(out_sequence)):
                        out_bound = contours[out_idx].reshape(-1, 2)
                        out_bound = np.column_stack((out_bound, np.full(len(out_bound), 0)))
                        try:
                            if self.pc_info['gridsize'] > 1:
                                out_polygon = point2polygon(out_bound[:, :2], float(self.pc_info['dpthreshold']),
                                                            self.pc_info['gridsize'])
                                out_polygon = np.column_stack((out_polygon, np.full(len(out_polygon), 0)))
                            else:
                                out_polygon = out_bound
                            out_polygon = np.column_stack((np.full(len(out_polygon), out_ii), out_polygon))
                            if out_polygon.shape[0] > 2:
                                self.polygon = np.row_stack((self.polygon, out_polygon))
                                in_bound = []
                                in_idx = np.where(hierarchy[:, 3] == out_idx)[0]

                                for idx, contour_idx in enumerate(in_idx):
                                    bound = contours[contour_idx].reshape(-1, 2)
                                    bound = np.column_stack((bound, np.full(len(bound), 0)))
                                    if self.pc_info['gridsize'] > 1:
                                        polygon = point2polygon(bound[:, :2], float(self.pc_info['dpthreshold']),
                                                                self.pc_info['gridsize'])
                                        polygon = np.column_stack((polygon, np.full(len(polygon), 0)))

                                    else:
                                        polygon = bound
                                    in_bound.append(polygon)
                                    polygon = np.column_stack(
                                        (np.full(len(polygon), out_ii + float("0." + str(idx + 1))), polygon))
                                    if polygon.shape[0] > 2:
                                        self.polygon = np.row_stack((self.polygon, polygon))
                        except:
                            pass

                        out_idx = hierarchy[out_idx, 0]
