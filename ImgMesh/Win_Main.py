import os
import time

import cv2
import numpy as np
import pygmsh
import gmsh
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtWidgets import QTreeWidgetItem, QMainWindow, QMenu, QAction
from colorama import Fore
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from ImgMesh.Win_helpdoc import HelpDoc
from ImgMesh.mesh_generate import *
from ImgMesh.Win_mesh_edit import *
from ImgMesh.Win_PCSet import Win_PCSet
from ImgMesh.Win_Setting import Win_Setting
from ImgMesh.Win_aboutus import *
from ImgMesh.Img import *
from ImgMesh.tools import *
from ImgMesh.Ui.Ui_MainWindow import Ui_MainWindow
from .Icons import icon_rc
from ImgMesh.Qss.QssList import color_list

QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)


class Win_Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.init_UI()

    def init_UI(self):
        self.setWindowIcon(QIcon(':/icon/ImgMesh.png'))
        self.init_tree_view()
        self.init_menu()
        self.init_VTK()
        self.init_setting_window()
        self.init_variables()
        self.show()

    def init_tree_view(self):
        self.tree_items = {}
        self.tree_items['Images'] = self.create_tree_item(self.treeWidget, 'Images', ':/icon/image.png')
        self.tree_items['Point Cloud'] = self.create_tree_item(self.treeWidget, 'Point Cloud', ':/icon/pointcloud.png')
        self.tree_items['Surface Mesh'] = self.create_tree_item(self.treeWidget, 'Surface Mesh', ':/icon/tri.png')
        self.tree_items['Tetrahedral'] = self.create_tree_item(self.treeWidget, 'Tetrahedral', ':/icon/tetra.png')

        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.modelTree_rightmenu)
        self.treeWidget.expandAll()

    def create_tree_item(self, parent, text, icon_path):
        item = QTreeWidgetItem(parent)
        item.setText(0, text)
        item.setIcon(0, QIcon(icon_path))
        return item

    def init_menu(self):
        self.act_importimage.triggered.connect(self.import_image)
        self.act_importpc.triggered.connect(self.import_point_cloud)
        self.act_importmesh.triggered.connect(self.import_mesh)
        self.act_options.triggered.connect(self.show_setting_window)
        self.act_aboutus.triggered.connect(self.show_aboutus)
        self.act_helpdocs.triggered.connect(self.show_helpdocs)

        self.backview.setIcon(QIcon(":/icon/back.png"))
        self.bottomview.setIcon(QIcon(":/icon/bottom.png"))
        self.frontview.setIcon(QIcon(":/icon/front.png"))
        self.leftview.setIcon(QIcon(":/icon/left.png"))
        self.rightview.setIcon(QIcon(":/icon/right.png"))
        self.topview.setIcon(QIcon(":/icon/top.png"))
        self.isoview.setIcon(QIcon(":/icon/iso.png"))
        self.frontview.triggered.connect(lambda: front_view(self.render_window))
        self.backview.triggered.connect(lambda: back_view(self.render_window))
        self.leftview.triggered.connect(lambda: left_view(self.render_window))
        self.rightview.triggered.connect(lambda: right_view(self.render_window))
        self.topview.triggered.connect(lambda: top_view(self.render_window))
        self.bottomview.triggered.connect(lambda: bottom_view(self.render_window))
        self.isoview.triggered.connect(lambda: iso_view(self.render_window))

    def init_VTK(self):
        self.vtk_vertical_layout = QVBoxLayout(self.widget)
        self.vtk_widget = QVTKRenderWindowInteractor(self.widget)
        self.vtk_vertical_layout.addWidget(self.vtk_widget)
        self.render_window = self.vtk_widget.GetRenderWindow()

        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(1, 1, 1)
        self.renderer.SetBackground2(0.2, 0.4, 0.6)
        self.renderer.SetGradientBackground(1)
        self.render_window.AddRenderer(self.renderer)

        self.iren = self.render_window.GetInteractor()
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.style.SetDefaultRenderer(self.renderer)
        self.iren.SetInteractorStyle(self.style)

        self.axesActor = vtk.vtkAxesActor()
        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axesActor)
        self.axes_widget.SetInteractor(self.iren)
        self.axes_widget.EnabledOn()
        self.axes_widget.InteractiveOff()
        self.iren.Initialize()

    def init_setting_window(self):
        self.setting = Win_Setting()
        self.setting.lineedit_maxsize.textChanged.connect(self.setMaxsize)
        self.setting.lineedit_minsize.textChanged.connect(self.setMinsize)
        self.setting.checkBox_2dnode.stateChanged.connect(self.set_show_2d_node_label)
        self.setting.checkBox_2delement.stateChanged.connect(self.set_show_2d_mesh_label)
        self.setting.checkBox_2dbound.stateChanged.connect(self.set_show_2d_mesh_boundary)
        self.setting.checkBox_2dcheck.stateChanged.connect(self.set_show_2d_mesh_check)
        self.setting.checkBox_2dframe.stateChanged.connect(self.set_show_2d_mesh_edge)
        self.setting.checkBox_2dface.stateChanged.connect(self.set_show_2d_mesh_face)
        self.setting.checkBox_bounding_box.stateChanged.connect(self.set_show_bounding_box)

    def init_variables(self):
        self.edgeActor_2d_mesh = None
        self.labelActor_2d_node = None
        self.labelActor_2d_mesh = None

        self.point_actor = None
        self.vol = None
        self.actor = None
        self.bounding_box_actor = None

        self.Win_smooth = None
        self.Win_PC = None
        self.Win_ThresholdSlider = None
        self.Win_mesh_edit = None
        self.Orthogonal_View = None

        self.thresholdMin = 0
        self.thresholdMax = 255

        self.mesh = None
        self.tetmesh = None
        self.meshmaxsize = -1
        self.meshminsize = -1

        self.edge_angle = 45
        self.model_object = {}

    """
    Model tree
    """

    def modelTree_rightmenu(self, pos):
        item = self.treeWidget.currentItem()
        item1 = self.treeWidget.itemAt(pos)

        popMenu = QMenu()

        if item is not None and item1 is not None:
            if item.parent() is not None and item.parent() == self.tree_items['Images']:
                popMenu = QMenu()
                actionA = QAction(u'Volume rendering')
                actionB = QAction(u'Ortho views')
                actionC = QAction(u'Interactive threshold')
                # actionD = QAction(u'Interactive thresholding')
                actionE = QAction(u'Export')

                actionA.triggered.connect(self.volume_render)
                actionB.triggered.connect(self.orthogonal_view)
                actionC.triggered.connect(self.show_threshold_slider)
                # actionD.triggered.connect(self.show_threshold_set)
                actionE.triggered.connect(self.export_image)

                popMenu.addActions([actionA, actionB, actionC, actionE])

            if item == self.tree_items['Point Cloud']:
                actionA = QAction(u'Create')
                actionA.triggered.connect(self.create_point_cloud)
                popMenu.addAction(actionA)

            if item.parent() is not None and item.parent() == self.tree_items['Point Cloud']:
                actionA = QAction(u'Render')
                actionB = QAction(u'Downsample')
                actionC = QAction(u'Reconstruction')

                actionA.triggered.connect(self.show_point_cloud)
                actionB.triggered.connect(self.point_cloud_downsample)
                actionC.triggered.connect(self.treeWidget_mesh)

                popMenu.addActions([actionA, actionB, actionC])

            if item.parent() is not None and item.parent() == self.tree_items['Surface Mesh']:
                popMenu = QMenu()
                vtkmesh = self.model_object[item.text(0)]['surface mesh']
                V, T, Q = vtk_numpy(vtkmesh)
                Planar = False
                for col in range(V.shape[1]):
                    if np.all(V[:, col] == V[0, col]):
                        Planar = True
                        break
                if Planar:
                    actionA = QAction(u'Display')
                    actionB = QAction(u'Edit')
                    actionC = QAction(u'Export')

                    actionA.triggered.connect(self.show_mesh)
                    actionB.triggered.connect(self.show_mesh_edit)
                    actionC.triggered.connect(self.export_2Dmesh)

                    popMenu.addActions([actionA, actionB, actionC])
                else:

                    actionA = QAction(u'Display')
                    actionB = QAction(u'Edit')
                    actionC = QAction(u'Filling holes')
                    actionD = QAction(u'Smooth')
                    actionE = QAction(u'3D')
                    actionF = QAction(u'Export')

                    actionA.triggered.connect(self.show_mesh)
                    actionB.triggered.connect(self.show_mesh_edit)
                    actionC.triggered.connect(self.treeWidget_fillhole)
                    actionD.triggered.connect(self.treeWidget_smooth)
                    actionE.triggered.connect(self.treeWidget_tetra_mesh)
                    actionF.triggered.connect(self.export_2Dmesh)

                    popMenu.addActions([actionA, actionB, actionC, actionD, actionE, actionF])

            if item.parent() is not None and item.parent() == self.tree_items['Tetrahedral']:
                actionA = QAction(u'Display')
                actionB = QAction(u'Display nodes')
                actionC = QAction(u'Export')

                actionA.triggered.connect(self.show_tet_mesh)
                actionB.triggered.connect(self.show_tet_point)
                actionC.triggered.connect(self.export_tetmesh)

                popMenu.addActions([actionA, actionB, actionC])

        popMenu.exec_(QCursor.pos())

    """
    Image function：image import render and orthoview
    """

    def import_image(self):
        self.image_module = Img()
        self.image_module.select_image()
        self.image_module.img_signal.connect(self.end_import_image)

    def end_import_image(self, image_info):
        # Update model object
        try:
            model_object = {'imagepath': image_info['imagepath'],
                            'resolution': image_info['resolution'],
                            'vtkimage': image_info['vtkdata']}
            object_name = generate_unique_key(image_info['objectname'], self.model_object.keys())
            self.model_object[object_name] = model_object

            update_tree(self.tree_items['Images'], object_name)

            path_parts = image_info['imagepath'][0].split('/')
            path = '/'.join(path_parts[:-1])
            self.statusbar.showMessage('Successfully imported ' + path)
            print(f"Info    : Image loaded from {path} Size : {image_info['vtkdata'].GetDimensions()}")
        except Exception as e:
            self.statusbar.showMessage('Error!')
            print(Fore.RED + f"Error   : {e}" + Fore.RESET)

    def volume_render(self):
        item = self.treeWidget.currentItem().text(0)
        vtkimage = self.model_object[item]['vtkimage']

        color_values = self.get_color_transfer_function()
        self.vol = volume_render(vtkimage, self.render_window, color_values)
        self.thresholdMin, self.thresholdMax = 1, 255

        self.Win_ThresholdSlider = WIN_RENDER_THRESHOLD_SLIDER(self.thresholdMin, self.thresholdMax)
        self.Win_ThresholdSlider.threshold_slider.valueChanged.connect(self.set_render_threshold)

        # Add bounding box
        if self.setting.checkBox_bounding_box.isChecked():
            self.bounding_box_actor = draw_bounding_box(vtkimage)
            self.renderer.AddActor(self.bounding_box_actor)
            self.render_window.Render()

    def orthogonal_view(self):
        item = self.treeWidget.currentItem().text(0)
        vtkimage = self.model_object[item]['vtkimage']

        camera = self.renderer.GetActiveCamera()
        position = camera.GetPosition()
        focal_point = camera.GetFocalPoint()
        view_up = camera.GetViewUp()

        ORTHOGONAL_VIEW(vtkimage, self.vol, self.thresholdMin, self.thresholdMax, position, focal_point, view_up)

    def show_threshold_slider(self):
        if self.Win_ThresholdSlider:
            self.Win_ThresholdSlider.show()
            self.Win_ThresholdSlider.threshold_signal.connect(self.image_threshold_segment)
        else:
            self.statusbar.showMessage('Please render first!')
            print(Fore.YELLOW + f"Warn    :  Please volume rendering first!" + Fore.RESET)

    def set_render_threshold(self):
        threshold_slider_value = self.Win_ThresholdSlider.threshold_slider.value()

        opacity_func = vtk.vtkPiecewiseFunction()
        opacity_func.AddPoint(threshold_slider_value[0] - 1, 1)
        opacity_func.AddPoint(threshold_slider_value[1], 1)
        opacity_func.ClampingOff()

        colors = self.get_color_transfer_function()
        color_func = vtk.vtkColorTransferFunction()
        for color in colors:
            color_func.AddRGBPoint(color[0], color[1] / 255, color[2] / 255, color[3] / 255)

        volume_property = self.vol.GetProperty()
        volume_property.SetScalarOpacity(opacity_func)

        self.vol.Update()
        self.render_window.Render()

    def image_threshold_segment(self, threshold):
        item = self.treeWidget.currentItem().text(0)

        vtkimage = self.model_object[item]['vtkimage']
        # GaussianSmooth
        if self.setting.checkBox_imagesmooth.isChecked():
            print(f"Info    : Start gaussian smooth ")
            filtered_image_data = vtk.vtkImageGaussianSmooth()
            filtered_image_data.SetInputData(vtkimage)
            filtered_image_data.SetDimensionality(int(self.setting.lineedit_image_Gaussian_Dimensionality.text()))
            filtered_image_data.SetStandardDeviations(float(self.setting.lineedit_image_StandardDeviation1.text()),
                                                      float(self.setting.lineedit_image_StandardDeviation2.text()),
                                                      float(self.setting.lineedit_image_StandardDeviation3.text()))
            filtered_image_data.SetRadiusFactors(float(self.setting.lineedit_image_RadiusFactor1.text()),
                                                 float(self.setting.lineedit_image_RadiusFactor2.text()),
                                                 float(self.setting.lineedit_image_RadiusFactor3.text()))
            filtered_image_data.Update()
            vtkimage = filtered_image_data.GetOutput()
            print(f"Info    : Gaussian smooth finished")

        # Threshold segmentation
        print(f"Info    : Start threshold segment")
        threshold_filter = vtk.vtkImageThreshold()
        threshold_filter.SetInputData(vtkimage)
        threshold_filter.ThresholdBetween(threshold[0], threshold[1])
        threshold_filter.ReplaceInOn()
        threshold_filter.ReplaceOutOn()
        threshold_filter.SetInValue(255)
        threshold_filter.SetOutValue(0)
        threshold_filter.Update()
        print(f"Info    : Threshold segment complted")

        # Update model object and model tree
        object_name = generate_unique_key(item, self.model_object.keys())
        self.model_object[object_name] = {'imagepath': '', 'vtkimage': threshold_filter.GetOutput(),
                                          'resolution': self.model_object[item]['resolution']}

        update_tree(self.tree_items['Images'], object_name)

        colors = self.get_color_transfer_function()
        volume_render(threshold_filter.GetOutput(), self.render_window, colors)

        self.statusbar.showMessage('Successfully segmented!')
        print(f"Info    : {object_name} Image segmented in range : {threshold[0]} - {threshold[1]}")

    def export_image(self):
        item = self.treeWidget.currentItem().text(0)
        vtkimage = self.model_object[item]['vtkimage']
        fd, fd_type = QFileDialog.getSaveFileName(self, "Export Image", "", "*.jpg;;*.png;;*.bmp;;*.tif;;All Files(*)")
        if fd.split('.')[0]:
            self.export_vtkimage(vtkimage, fd.split('.')[0], fd_type.split('.')[-1])
            self.statusbar.showMessage('Files saved in: ' + fd)
            print(f"Info    : Files saved in : {fd}")

    def export_vtkimage(self, data, path, fd_type):

        dimensions = data.GetDimensions()
        vtk_array = data.GetPointData().GetScalars()
        numpy_array = vtk_to_numpy(vtk_array).reshape(dimensions, order='F')

        for slice_idx in range(dimensions[2]):
            slice_data = numpy_array[:, :, slice_idx]
            normalized_slice = (
                    (slice_data - np.min(slice_data)) / (np.max(slice_data) - np.min(slice_data)) * 255).astype(
                np.uint8)
            output_file = f"{path}_{slice_idx}.{fd_type}"
            cv2.imwrite(output_file, np.rot90(normalized_slice))

    def get_color_transfer_function(self):
        color_values = []
        for row in range(self.setting.color_trans_table.color_table.rowCount()):
            row_values = []
            for column in range(self.setting.color_trans_table.color_table.columnCount()):
                color_item = self.setting.color_trans_table.color_table.item(row, column)
                if color_item:
                    temp = color_item.text()
                    row_values.append(int(float(temp)))
            color_values.append(row_values)
        return color_values

    """
    Point cloud function：create render 
    """

    # Create point cloud
    def import_point_cloud(self):
        pc_path = QFileDialog.getOpenFileNames(filter='*.txt', caption='Select Point Cloud')
        if len(pc_path[0]) > 0:
            pc_path = pc_path[0][0]
            try:
                pc = np.loadtxt(pc_path, delimiter=' ')
            except:
                try:
                    pc = np.loadtxt(pc_path, delimiter=',')
                except:
                    self.statusbar.showMessage('Unsupported format!')
                    print(
                        Fore.RED + f"Error   : Unsupported format Please enter txt file and split point with a space "
                                   f"or ," + Fore.RESET)
                    return

            pc = np.column_stack((np.zeros((pc.shape[0], 1)), pc))
            object_name = pc_path.split('/')[-1].split('.')[0]
            self.model_object[object_name] = {}
            pc_info = {
                'imagename': object_name,
                'gridsize': -1,
            }
            self.statusbar.showMessage('Successfully imported ' + pc_path)
            print(f"Info    : {pc.shape[0]} points loaded from {pc_path}")
            self.end_create_point_cloud(pc_info, pc)

    def create_point_cloud(self):
        self.Win_PC = Win_PCSet(self.model_object)
        self.Win_PC.PC_signal.connect(self.end_create_point_cloud)
        for key in self.model_object.keys():
            if 'vtkimage' in self.model_object[key].keys():
                self.Win_PC.cbx_inputimage.addItem(key)
        self.Win_PC.show()
        self.statusbar.showMessage('Successfully created point cloud!')

    def end_create_point_cloud(self, pc_info, polygon):
        if pc_info:
            object_name = pc_info['imagename']
            self.model_object[object_name]['point cloud'] = polygon
            self.model_object[object_name]['mesh size'] = pc_info['gridsize']

            update_tree(self.tree_items['Point Cloud'], object_name)

            color, point_size = self.get_PC_color_size()
            self.point_cloud_render(polygon, color, point_size)

            num_polygon = np.unique(polygon[:, 0]).shape[0]
            print(f"Info    : {polygon.shape[0]} points created : {num_polygon} polygons")

            z_unique = np.unique(polygon[:, 3])

            if self.setting.checkbox_2dmesh.isChecked():
                if z_unique.shape[0] > 1:
                    result = self.create_2D_mesh(object_name)
                    if result:
                        if self.setting.checkbox_smooth.isChecked():
                            self.mesh_smooth(object_name)
                        if self.setting.checkbox_3dmesh.isChecked() and not self.setting.checkbox_openmesh.isChecked():
                            self.create_tetra_mesh(object_name)
                else:
                    self.create_2D_mesh_plane(pc_info['imagename'])

    def show_point_cloud(self):
        item = self.treeWidget.currentItem().text(0)

        color = [int(self.setting.lineedit1_Pc_color.text()) / 255,
                 int(self.setting.lineedit2_Pc_color.text()) / 255,
                 int(self.setting.lineedit3_Pc_color.text()) / 255, ]
        point_size = float(self.setting.lineedit_Pc_size.text())

        self.point_cloud_render(self.model_object[item]['point cloud'], color, point_size)

    def point_cloud_downsample(self):
        item = self.treeWidget.currentItem().text(0)
        points = np.array(self.model_object[item]['point cloud'])

        point_idx = np.unique(points[:, 0])

        parameter = int(self.setting.lineedit_downsample.text())
        algorithm = self.setting.combobox_downsample.currentIndex()
        color, point_size = self.get_PC_color_size()

        downsample_points = np.zeros((0, 4))

        print(f"Info    : Start point cloud downsampling, Algorithm : {self.setting.combobox_downsample.currentText()}")
        for i in range(len(point_idx)):
            idx = np.where(points[:, 0] == point_idx[i])[0]
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points[idx, 1:])
            if algorithm == 0:
                parameter = max(parameter, 1)
                voxel_down_pcd = pcd.voxel_down_sample(voxel_size=parameter)
            elif algorithm == 1:
                parameter = max(parameter, 1)
                voxel_down_pcd = pcd.uniform_down_sample(every_k_points=parameter)
            else:
                voxel_down_pcd = pcd.random_down_sample(sampling_ratio=parameter)

            out_points = np.asarray(voxel_down_pcd.points)
            out_points = np.column_stack((np.full(out_points.shape[0], point_idx[i]), out_points))
            downsample_points = np.vstack((downsample_points, out_points))

            print(
                f"Info    : Polygon {i} downsampling completed : {idx.shape[0]} points to {out_points.shape[0]} points ")

        self.point_cloud_render(downsample_points, color, point_size)

        new_key = generate_unique_key(item, self.model_object.keys())
        model_object = {}
        for key in self.model_object[item].keys():
            if key != 'point cloud':
                model_object[key] = self.model_object[item][key]
            else:
                model_object[key] = downsample_points
        self.model_object[new_key] = model_object

        update_tree(self.tree_items['Point Cloud'], new_key)

        self.statusbar.showMessage('Points downsampling completed!')
        print(f"Info    : Points downsampling completed ")

    def get_PC_color_size(self):
        color = [int(self.setting.lineedit1_Pc_color.text()) / 255,
                 int(self.setting.lineedit2_Pc_color.text()) / 255,
                 int(self.setting.lineedit3_Pc_color.text()) / 255, ]
        point_size = float(self.setting.lineedit_Pc_size.text())
        return color, point_size

    """
    Mesh function：create render
    """

    def import_mesh(self):
        mesh_path = QFileDialog.getOpenFileNames(caption='Select mesh')[0]
        if len(mesh_path) > 0:
            try:
                mesh = meshio.read(mesh_path[0])
                mesh_name = mesh_path[0].split('/')[-1]
                new_key = generate_unique_key(mesh_name.split('.')[0], self.model_object.keys())
                update_tree(self.tree_items['Surface Mesh'], new_key)

                self.mesh = meshio_vtk(mesh)
                model_object = {'surface mesh': self.mesh, 'mesh size': -1}
                self.model_object[new_key] = model_object
                self.mesh_render(self.mesh)
                self.renderer.ResetCamera()

                self.statusbar.showMessage('Mesh imported successfully!')
                print(
                    f"Info    : Mesh imported : {self.mesh.GetNumberOfCells()} elements {self.mesh.GetNumberOfPoints()} points")

            except Exception as e:
                self.statusbar.showMessage('Error!')
                print(Fore.RED + f"Error   : {e}" + Fore.RESET)

    def treeWidget_mesh(self):
        item = self.treeWidget.currentItem().text(0)
        z_list = np.unique(self.model_object[item]['point cloud'][:, 3])
        if z_list.shape[0] == 1:
            self.create_2D_mesh_plane(item)
        else:
            self.create_2D_mesh(item)

    def treeWidget_fillhole(self):
        item = self.treeWidget.currentItem().text(0)
        self.fill_mesh_holes(item)

    def treeWidget_smooth(self):
        item = self.treeWidget.currentItem().text(0)
        self.mesh_smooth(item)

    def treeWidget_tetra_mesh(self):
        item = self.treeWidget.currentItem()
        self.create_tetra_mesh(item.text(0))

    def create_2D_mesh_plane(self, item):
        print(f"Info    : Starting adding polygon")
        start_time = time.process_time()
        polygons = self.model_object[item]['point cloud']
        polygon_idx = np.unique(polygons[:, 0])
        outer_idx = polygon_idx[np.where(polygon_idx % 1 < 0.01)[0]]
        outer_idx = np.array(outer_idx, dtype=int)

        lcar = float(self.model_object[item]['mesh size'])

        try:
            if not self.setting.checkbox_backgroundmesh.isChecked():
                with pygmsh.occ.Geometry() as geom:
                    for i in range(len(outer_idx)):
                        pc = polygons[polygons[:, 0] == outer_idx[i], 1:3]
                        _, idx = np.unique(pc, axis=0, return_index=True)
                        pc2 = pc[np.sort(idx)]
                        poly1 = geom.add_polygon(pc2, mesh_size=lcar)
                        print(f"Info    : Added polygon {outer_idx[i]}")

                        in_idx = np.where((polygon_idx > outer_idx[i]) & (polygon_idx < outer_idx[i] + 1))[0]

                        for j in range(len(in_idx)):
                            pc2 = polygons[polygons[:, 0] == polygon_idx[in_idx[j]], 1:3]
                            poly2 = geom.add_polygon(pc2, mesh_size=lcar)
                            poly1 = geom.boolean_difference(poly1, poly2)
                            print(f"Info    : Added polygon {in_idx[j]}")
                    print(f"Info    : Start meshing 2D ")
                    if self.setting.checkbox_quadmesh.isChecked():
                        mesh = geom.generate_mesh(quad=True)
                        gmsh.write("temp.msh")
                        mesh = meshio.read("temp.msh", file_format='gmsh')
                        os.remove("temp.msh")
                    else:
                        mesh = geom.generate_mesh()

            else:
                vtk_data = self.model_object[item]['vtkimage']
                boundx = vtk_data.GetDimensions()[0] - 1
                boundy = vtk_data.GetDimensions()[1] - 1

                bound_box = np.array([[0, 0, 0], [0, boundy, 0], [boundx, boundy, 0], [boundx, 0, 0]])

                poly1list = []
                poly2list = []
                with pygmsh.occ.Geometry() as geom:
                    bound = geom.add_polygon(bound_box, mesh_size=lcar)
                    for i in range(len(outer_idx)):
                        pc = polygons[polygons[:, 0] == outer_idx[i], 1:3]
                        poly1 = geom.add_polygon(pc, mesh_size=lcar)
                        bound = geom.boolean_difference(bound, poly1, delete_other=False)
                        print(f"Info    : Added polygon {outer_idx[i]}")

                        in_idx = np.where((polygon_idx > outer_idx[i]) & (polygon_idx < outer_idx[i] + 1))[0]
                        for j in range(len(in_idx)):
                            pc2 = polygons[polygons[:, 0] == polygon_idx[in_idx[j]], 1:3]
                            poly2 = geom.add_polygon(pc2, mesh_size=lcar)
                            poly1 = geom.boolean_difference(poly1, poly2, delete_other=False)
                            if type(poly2) == list:
                                poly2list.append(poly2[0])
                            else:
                                poly2list.append(poly2)
                            print(f"Info    : Added polygon {in_idx[j]}")
                        if type(poly1) == list:
                            poly1list.append(poly1[0])
                        else:
                            poly1list.append(poly1)

                    if len(poly2list) > 0:
                        geom.add_physical(poly2list, label="Material_2")
                    if len(poly1list) > 0:
                        geom.add_physical(poly1list, label="Material_1")
                    geom.add_physical(bound, label="Material_0")

                    print(f"Info    : Start meshing 2D ")
                    if self.setting.checkbox_quadmesh.isChecked():
                        mesh = geom.generate_mesh(quad=True)
                        gmsh.write("temp.msh")
                        mesh = meshio.read("temp.msh", file_format='gmsh')
                        os.remove("temp.msh")
                    else:
                        mesh = geom.generate_mesh()

            # render the mesh

            self.mesh = meshio_vtk(mesh)
            end_time = time.process_time()

            tri_qua, quad_qua = mesh_quality(self.mesh)
            hist, bin_edges = np.histogram(tri_qua, bins=10, range=(0, 1))
            percentage = hist / tri_qua.shape[0] * 100
            print(f"Done meshing 2D: {tri_qua.shape[0]} triangles {quad_qua.shape[0]} quad {end_time - start_time} s")
            print("Triangle quality : ")
            for i in range(10):
                print(
                    f"Info    : {i * 0.1:.2f} < quality <  {(i + 1) * 0.1:.2f} : {hist[i]} elements ({percentage[i]:.2f}%)")

            print("Quad quality : ")
            hist, bin_edges = np.histogram(quad_qua, bins=10, range=(0, 1))
            percentage = hist / quad_qua.shape[0] * 100
            for i in range(10):
                print(
                    f"Info    : {i * 0.1:.2f} < quality <  {(i + 1) * 0.1:.2f} : {hist[i]} elements ({percentage[i]:.2f}%)")

            self.model_object[item]['surface mesh'] = self.mesh
            update_tree(self.tree_items['Surface Mesh'], item)

            num_ele = self.mesh.GetNumberOfCells()
            self.mesh_render(self.mesh)
            self.statusbar.showMessage(f"{num_ele} elements created in " + f"{end_time - start_time} seconds!")
        except Exception as e:
            self.statusbar.showMessage('Error!')
            print(Fore.RED + f"Error   : {e}" + Fore.RESET)

    def export_2Dmesh(self):
        item = self.treeWidget.currentItem().text(0)
        vtkmesh = self.model_object[item]['surface mesh']

        mesh = vtk_meshio(vtkmesh)
        currentPath = QDir.currentPath()
        title = "Export mesh"
        fileList, filtUsed = QFileDialog.getSaveFileName(self, title, currentPath)
        if fileList:
            mesh.write(fileList)
            self.statusbar.showMessage('File saved in ：' + fileList)
            print(f"Info    : File saved in : {fileList}")

    def create_2D_mesh(self, item):
        # get parameters of 2d mesh generation
        algorithm_index = self.setting.combobox_2d_mesh_gen.currentIndex()
        tables = [
            self.setting.table_greedy_crust,
            self.setting.table_matching_cubes,
            self.setting.table_o3d_alpha,
            self.setting.table_o3d_poisson,
            self.setting.table_o3d_ball_pivoting
        ]

        # get values from mesh
        values = []
        for row in range(tables[algorithm_index].rowCount()):
            for column in range(tables[algorithm_index].columnCount()):
                value_item = tables[algorithm_index].item(row, column)
                if value_item:
                    values.append(value_item.text())

        polygon = self.model_object[item]['point cloud']
        polygon_idx = np.unique(polygon[:, 0])
        start_time = time.process_time()

        polys = vtk.vtkCellArray()
        vtkpoints = vtk.vtkPoints()
        color_array = vtk.vtkUnsignedCharArray()
        color_array.SetNumberOfComponents(3)
        color_array.SetName("Colors")

        print(f"Info    : Start meshing 2D Algorithm : {self.setting.combobox_2d_mesh_gen.currentText()}")
        if algorithm_index == 0:
            V_num = 0
            for i in range(len(polygon_idx)):
                pc = polygon[polygon[:, 0] == polygon_idx[i], 1:]

                mesh_greedy_crust = Greedy_Crust()
                mesh_greedy_crust.vertices = np.array(pc)
                mesh_greedy_crust.offset = int(values[0])
                mesh_greedy_crust.N_shield = int(values[1])
                mesh_greedy_crust.ifact_factor = float(values[2])
                mesh_greedy_crust.alpha_factor = np.cos((180 - float(values[3])) / 180 * np.pi)
                mesh_greedy_crust.alpha_flat = np.cos((180 - float(values[4])) / 180 * np.pi)
                mesh_greedy_crust.openmesh = self.setting.checkbox_openmesh.isChecked()
                mesh_greedy_crust.perform_reconstruction()

                V, T = mesh_greedy_crust.vertices, mesh_greedy_crust.t

                if not self.setting.checkbox_openmesh.isChecked():
                    mesh = numpy_vtk(V, T)
                    normals = vtk.vtkPolyDataNormals()
                    normals.SetInputData(mesh)
                    normals.ConsistencyOn()
                    normals.SplittingOff()
                    normals.Update()
                    mesh = vtk.vtkPolyData()
                    mesh.SetPoints(normals.GetOutput().GetPoints())
                    mesh.SetPolys(normals.GetOutput().GetPolys())
                    try:
                        V, T, Q = vtk_numpy(mesh)
                        V, T = triangulate_refine_fair(V, T, density_factor=1.8)
                    except:
                        pass

                for v in V:
                    vtkpoints.InsertNextPoint(v)
                for t in T:
                    polys.InsertNextCell(3, t + V_num)
                    color_array.InsertNextTuple3(color_list[i][0], color_list[i][1], color_list[i][2])

                V_num += V.shape[0]
                print(f"Info    : Point cloud {i} meshing completed")

            vtkmesh = vtk.vtkPolyData()
            vtkmesh.SetPoints(vtkpoints)
            vtkmesh.SetPolys(polys)
            vtkmesh.GetCellData().SetScalars(color_array)

            normals = vtk.vtkPolyDataNormals()
            normals.SetInputData(vtkmesh)
            normals.ConsistencyOn()
            normals.SplittingOff()
            normals.Update()

            vtkmesh = vtk.vtkPolyData()
            vtkmesh.SetPoints(normals.GetOutput().GetPoints())
            vtkmesh.SetPolys(normals.GetOutput().GetPolys())
            vtkmesh.GetCellData().SetScalars(normals.GetOutput().GetCellData().GetScalars())

        elif algorithm_index == 1:
            contour = vtk.vtkMarchingCubes()
            if 'vtkimage' in self.model_object[item].keys():
                vtk_data = self.model_object[item]['vtkimage']
                contour.SetInputData(vtk_data)
                contour.ComputeGradientsOn()
                # contour.ComputeNormalsOn()
                for ii in range(0, len(values), 2):
                    contour.SetValue(int(values[ii]), int(values[ii + 1]))
                # contour.SetValue(0, 255)
                contour.Update()
                vtkmesh = contour.GetOutput()
                color_array = vtk.vtkUnsignedCharArray()
                color_array.SetNumberOfComponents(3)
                color_array.SetName("Colors")
                for i in range(vtkmesh.GetNumberOfCells()):
                    color_array.InsertNextTuple3(color_list[0][0], color_list[0][1], color_list[0][2])
                vtkmesh.GetCellData().SetScalars(color_array)
                print(f"Info    : Point cloud meshing completed")
            else:
                self.statusbar.showMessage('Please import image first!')
                print(Fore.RED + "Error   : Marching cubes cannot proceed without image data" + Fore.RESET)
                return

        else:
            mesh_o3d = O3d_Reconstruction()
            T = np.empty((0, 3), dtype=int)
            V = np.empty((0, 3), dtype=float)
            for i in range(len(polygon_idx)):
                pc = polygon[polygon[:, 0] == polygon_idx[i], 1:]
                mesh_o3d.vertices = np.array(pc)
                if algorithm_index == 2:
                    mesh_o3d.method = 'Alpha shapes'
                    mesh_o3d.para = float(values[0])
                    mesh_o3d.perform_reconstruction()
                elif algorithm_index == 3:
                    mesh_o3d.method = 'Poisson'
                    mesh_o3d.para = int(values[0])
                    mesh_o3d.knn = int(values[1])
                    mesh_o3d.perform_reconstruction()
                elif algorithm_index == 4:
                    mesh_o3d.method = 'Ball pivoting'
                    text = values[0].split(',')
                    value = [float(value) for value in text]
                    mesh_o3d.para = value
                    mesh_o3d.knn = int(values[1])
                    mesh_o3d.perform_reconstruction()
                V, T = mesh_union(V, T, mesh_o3d.vertices, mesh_o3d.t)
                print(f"Info    : Point cloud {i} meshing completed")
            vtkmesh = numpy_vtk(V, T)

        self.mesh = vtkmesh
        end_time = time.process_time()

        tri_qua, quad_qua = mesh_quality(self.mesh)
        hist, bin_edges = np.histogram(tri_qua, bins=10, range=(0, 1))
        percentage = hist / tri_qua.shape[0] * 100
        print(
            f"Info    : Done meshing 2D: {tri_qua.shape[0]} triangles {quad_qua.shape[0]} quad {end_time - start_time} s")
        print("Info    : Triangle quality : ")
        for i in range(10):
            print(
                f"Info    : {i * 0.1:.2f} < quality <  {(i + 1) * 0.1:.2f} : {hist[i]} elements ({percentage[i]:.2f}%)")

        self.mesh_render(self.mesh)
        update_tree(self.tree_items['Surface Mesh'], item)
        self.model_object[item]['surface mesh'] = self.mesh

        num_cells = self.mesh.GetNumberOfCells()
        if num_cells > 0:
            self.statusbar.showMessage(f"{num_cells} elements created in " + f"{end_time - start_time} seconds!")
            return True
        else:
            print(Fore.RED + f"Error   : Mesh generation failed, please adjust the parameters" + Fore.RESET)
            self.statusbar.showMessage('Mesh generation failed, please adjust the parameters!')
            return False

    def show_mesh(self):
        item = self.treeWidget.currentItem().text(0)
        self.mesh = self.model_object[item]['surface mesh']
        self.mesh_render(self.mesh)

    """
        Hole filling
    """

    def fill_mesh_holes(self, item):
        vtkmesh = self.model_object[item]['surface mesh']
        V, T, Q = vtk_numpy(vtkmesh)
        V, T = triangulate_refine_fair(V, T, density_factor=1.8)
        vtkmesh = numpy_vtk(V, T)
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(vtkmesh)
        normals.ConsistencyOn()
        normals.SplittingOff()
        normals.Update()

        self.mesh = vtk.vtkPolyData()
        self.mesh.SetPoints(normals.GetOutput().GetPoints())
        self.mesh.SetPolys(normals.GetOutput().GetPolys())
        self.mesh.GetCellData().SetScalars(normals.GetOutput().GetCellData().GetScalars())

        self.model_object[item]['surface mesh'] = self.mesh
        self.mesh_render(self.mesh)

    def mesh_smooth(self, item):
        if self.setting.combobox_smoothalgorithm.currentText() == 'vtkWindowedSincPolyDataFilter':
            smooth = vtk.vtkWindowedSincPolyDataFilter()
        else:
            smooth = vtk.vtkSmoothPolyDataFilter()

        smooth_iterations = int(self.setting.lineedit_iterations.text())
        bound_smooth = self.setting.checkBox_boundsmooth.isChecked()
        edge_smooth = self.setting.checkBox_featureedgesmooth.isChecked()
        edge_angle = float(self.setting.lineedit_featureangle.text())

        print("Info    : Start smooth : ")
        vtkmesh = self.model_object[item]['surface mesh']
        smooth.SetInputData(vtkmesh)
        smooth.SetNumberOfIterations(smooth_iterations)
        smooth.SetFeatureEdgeSmoothing(not edge_smooth)
        smooth.SetBoundarySmoothing(bound_smooth)
        smooth.SetFeatureAngle(edge_angle)
        smooth.Update()

        self.mesh = smooth.GetOutput()
        self.mesh_render(self.mesh)

        tri_qua, quad_qua = mesh_quality(self.mesh)
        hist, bin_edges = np.histogram(tri_qua, bins=10, range=(0, 1))
        percentage = hist / tri_qua.shape[0] * 100
        print(f"Info    : Done smoothing: {tri_qua.shape[0]} triangles ")
        print("Info    : Triangle quality : ")
        for i in range(10):
            print(
                f"Info    : {i * 0.1:.2f} < quality <  {(i + 1) * 0.1:.2f} : {hist[i]} elements ({percentage[i]:.2f}%)")

        self.model_object[item]['surface mesh'] = self.mesh
        self.statusbar.showMessage('Mesh smoothed !')

    """
    Setting
    """

    # 打开设置窗口
    def show_setting_window(self):
        self.setting.show()

    def set_show_2d_mesh_edge(self):
        actors = self.renderer.GetActors()
        actor_num = actors.GetNumberOfItems()
        actors.InitTraversal()
        for i in range(0, actor_num):
            actor = actors.GetNextItem()
            if self.setting.checkBox_2dframe.isChecked():
                if not self.setting.checkBox_2dface.isChecked():
                    actor.GetProperty().SetOpacity(1)
                    actor.GetProperty().SetRepresentationToWireframe()
                else:
                    actor.GetProperty().SetOpacity(1)
                    actor.GetProperty().EdgeVisibilityOn()
            else:
                if not self.setting.checkBox_2dface.isChecked():
                    actor.GetProperty().SetOpacity(0)
                else:
                    actor.GetProperty().SetOpacity(1)
                    actor.GetProperty().EdgeVisibilityOff()
        self.render_window.Render()

    def set_show_2d_mesh_face(self):
        actors = self.renderer.GetActors()
        actor_num = actors.GetNumberOfItems()
        actors.InitTraversal()
        for i in range(0, actor_num):
            actor = actors.GetNextItem()
            if self.setting.checkBox_2dface.isChecked():
                if not self.setting.checkBox_2dframe.isChecked():
                    actor.GetProperty().SetRepresentationToSurface()
                    actor.GetProperty().EdgeVisibilityOff()
                    actor.GetProperty().SetOpacity(1)
                else:
                    actor.GetProperty().SetRepresentationToSurface()
                    actor.GetProperty().EdgeVisibilityOn()
                    actor.GetProperty().SetOpacity(1)
            else:
                if self.setting.checkBox_2dframe.isChecked():
                    actor.GetProperty().SetRepresentationToWireframe()
                else:
                    actor.GetProperty().SetOpacity(0)

        self.render_window.Render()

    def set_show_2d_mesh_boundary(self):
        if self.setting.checkBox_2dbound.isChecked():
            if self.actor is not None:
                self.show_mesh_holes_and_boundary()
        else:
            if self.edgeActor_2d_mesh is not None:
                self.renderer.RemoveActor(self.edgeActor_2d_mesh)
                self.render_window.Render()
                self.edgeActor_2d_mesh = None

    def set_show_2d_node_label(self):
        if self.setting.checkBox_2dnode.isChecked():
            if self.actor is not None:
                self.show_2d_node_label()
        else:
            if self.labelActor_2d_node is not None:
                self.renderer.RemoveActor(self.labelActor_2d_node)
                self.render_window.Render()
                self.labelActor_2d_node = None

    def set_show_2d_mesh_label(self):
        if self.setting.checkBox_2delement.isChecked():
            if self.actor is not None:
                self.show_2d_mesh_label()
        else:
            if self.labelActor_2d_mesh is not None:
                self.renderer.RemoveActor(self.labelActor_2d_mesh)
                self.render_window.Render()
                self.labelActor_2d_mesh = None

    def show_2d_mesh_label(self):
        if self.renderer is not None:
            idfilter = vtk.vtkIdFilter()
            idfilter.SetInputData(self.mesh)
            idfilter.PointIdsOn()
            idfilter.CellIdsOn()

            cellcenter = vtk.vtkCellCenters()
            cellcenter.SetInputConnection(idfilter.GetOutputPort())

            labelmapper = vtk.vtkLabeledDataMapper()
            labelmapper.SetInputConnection(cellcenter.GetOutputPort())
            labelmapper.SetLabelModeToLabelFieldData()
            labelmapper.GetLabelTextProperty().SetFontSize(10)

            labelmapper.GetLabelTextProperty().SetColor(0.0, 0.0, 1.0)
            self.labelActor_2d_mesh = vtk.vtkActor2D()
            self.labelActor_2d_mesh.SetMapper(labelmapper)
            self.renderer.AddActor(self.labelActor_2d_mesh)
            self.render_window.Render()

    def show_2d_node_label(self):
        if self.renderer is not None:
            idfilter = vtk.vtkIdFilter()
            idfilter.SetInputData(self.mesh)
            idfilter.PointIdsOn()
            idfilter.CellIdsOn()

            labelmapper = vtk.vtkLabeledDataMapper()
            labelmapper.SetInputConnection(idfilter.GetOutputPort())
            labelmapper.SetLabelModeToLabelFieldData()
            labelmapper.GetLabelTextProperty().SetFontSize(10)
            labelmapper.GetLabelTextProperty().SetColor(1.0, 0.0, 0.0)

            self.labelActor_2d_node = vtk.vtkActor2D()
            self.labelActor_2d_node.SetMapper(labelmapper)
            self.renderer.AddActor(self.labelActor_2d_node)
            self.render_window.Render()

    def show_mesh_holes_and_boundary(self):
        if self.renderer is not None:
            featureEdges = vtk.vtkFeatureEdges()
            featureEdges.SetInputData(self.mesh)
            featureEdges.BoundaryEdgesOn()
            featureEdges.FeatureEdgesOff()
            featureEdges.ManifoldEdgesOff()
            featureEdges.NonManifoldEdgesOff()
            featureEdges.Update()
            edgeMapper = vtk.vtkPolyDataMapper()
            edgeMapper.SetInputConnection(featureEdges.GetOutputPort())
            self.edgeActor_2d_mesh = vtk.vtkActor()
            self.edgeActor_2d_mesh.SetMapper(edgeMapper)
            self.edgeActor_2d_mesh.GetProperty().SetColor(1.0, 0, 0)
            self.renderer.AddActor(self.edgeActor_2d_mesh)
            self.render_window.Render()

    def set_show_2d_mesh_check(self):
        if self.setting.checkBox_2dcheck.isChecked():
            self.show_2d_mesh_check()
        else:
            if self.edgeActor_2d_mesh is not None:
                self.renderer.RemoveActor(self.edgeActor_2d_mesh)
                self.render_window.Render()
                self.edgeActor_2d_mesh = None

    def show_2d_mesh_check(self):
        if self.renderer is not None:
            featureEdges = vtk.vtkFeatureEdges()
            featureEdges.SetInputData(self.mesh)
            featureEdges.BoundaryEdgesOn()
            featureEdges.FeatureEdgesOff()
            featureEdges.ManifoldEdgesOff()
            featureEdges.NonManifoldEdgesOn()
            featureEdges.Update()

            edgeMapper = vtk.vtkPolyDataMapper()
            edgeMapper.SetInputConnection(featureEdges.GetOutputPort())

            self.edgeActor_2d_mesh = vtk.vtkActor()
            self.edgeActor_2d_mesh.SetMapper(edgeMapper)
            self.edgeActor_2d_mesh.GetProperty().SetColor(1.0, 0, 0)
            self.renderer.AddActor(self.edgeActor_2d_mesh)
            self.render_window.Render()

    def set_show_bounding_box(self):
        if self.setting.checkBox_bounding_box.isChecked():
            if self.vol is not None:
                mapper = self.vol.GetMapper()
                vtkdata = mapper.GetInput()
                self.bounding_box_actor = draw_bounding_box(vtkdata)
                self.renderer.AddActor(self.bounding_box_actor)
                self.render_window.Render()
        else:
            if self.bounding_box_actor is not None:
                self.renderer.RemoveActor(self.bounding_box_actor)
                self.render_window.Render()
                self.bounding_box_actor = None

    def setMaxsize(self):
        # self.meshmaxsize = {key: float(self.setting.lineedit_maxsize.text()) for key, value in self.meshmaxsize.items()}
        self.meshmaxsize = float(self.meshmaxsize)

    def setMinsize(self):
        # self.meshminsize = {key: float(self.setting.lineedit_minsize.text()) for key, value in self.meshminsize.items()}
        self.meshminsize = float(self.meshminsize)

    def create_tetra_mesh(self, item):

        vtkmesh = self.model_object[item]['surface mesh']

        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(vtkmesh)
        normals.ConsistencyOn()
        normals.SplittingOff()
        normals.Update()

        self.mesh = vtk.vtkPolyData()
        self.mesh.SetPoints(normals.GetOutput().GetPoints())
        self.mesh.SetPolys(normals.GetOutput().GetPolys())
        self.mesh.GetCellData().SetScalars(normals.GetOutput().GetCellData().GetScalars())

        self.model_object[item]['surface mesh'] = self.mesh

        if self.mesh.GetNumberOfCells() > 0:
            writer = vtk.vtkSTLWriter()
            writer.SetFileName('tet.stl')
            writer.SetInputData(self.mesh)
            writer.Write()
            gmsh.initialize()
            gmsh.logger.start()
            gmsh.clear()
            gmsh.open('tet.stl')
            os.remove('tet.stl')

            try:
                s = gmsh.model.getEntities(2)
                l = gmsh.model.geo.addSurfaceLoop([e[1] for e in s])
                gmsh.model.geo.addVolume([l])
                gmsh.model.geo.synchronize()
                funny = False
                f = gmsh.model.mesh.field.add("MathEval")
                if funny:
                    gmsh.model.mesh.field.setString(f, "F", "2*Sin((x+y)/5) + 3")
                else:
                    gmsh.model.mesh.field.setString(f, "F", "5")
                gmsh.model.mesh.field.setAsBackgroundMesh(f)

                if self.meshmaxsize > 0:
                    gmsh.option.setNumber('Mesh.MeshSizeMax', self.meshmaxsize)
                # gmsh.option.setNumber('Mesh.MeshSizeMin', meshminsize)
                if self.setting.combobox_3dmeshalgorithm.currentText() == 'Delaunay':
                    gmsh.option.setNumber('Mesh.Algorithm3D', 1)
                elif self.setting.combobox_3dmeshalgorithm.currentText() == 'Initial mesh only':
                    gmsh.option.setNumber('Mesh.Algorithm3D', 3)
                elif self.setting.combobox_3dmeshalgorithm.currentText() == 'Frontal':
                    gmsh.option.setNumber('Mesh.Algorithm3D', 4)
                elif self.setting.combobox_3dmeshalgorithm.currentText() == 'MMG3D':
                    gmsh.option.setNumber('Mesh.Algorithm3D', 7)
                elif self.setting.combobox_3dmeshalgorithm.currentText() == 'R-tree':
                    gmsh.option.setNumber('Mesh.Algorithm3D', 9)
                else:
                    gmsh.option.setNumber('Mesh.Algorithm3D', 10)
                gmsh.model.mesh.generate(3)
                elementTypes, elementTags, elementNode = gmsh.model.mesh.getElements(dim=2)
                nodeTags, coord, _ = gmsh.model.mesh.getNodes()
                if elementNode:
                    elementNode = elementNode[0]
                    gmsh_tri = elementNode.reshape((-1, 3))
                    gmsh_tri = gmsh_tri - 1
                    gmsh_node = coord.reshape((-1, 3))

                    polys = vtk.vtkCellArray()
                    vtkpoints = vtk.vtkPoints()
                    vtkpoints.SetData(numpy_to_vtk(np.asarray(gmsh_node)))
                    for t in gmsh_tri:
                        polys.InsertNextCell(3, t)
                    tet_point = vtk.vtkPolyData()
                    tet_point.SetPoints(vtkpoints)
                    self.model_object[item]['tet point'] = tet_point

                    elementTypes, elementTags, elementNode = gmsh.model.mesh.getElements(dim=3)
                    elementNode = elementNode[0]
                    gmsh_tet = elementNode.reshape((-1, 4))
                    gmsh_tet -= 1

                    update_tree(self.tree_items['Tetrahedral'], item)

                    color_array = vtk.vtkUnsignedCharArray()
                    color_array.SetNumberOfComponents(3)
                    color_array.SetName("Colors")

                    vtktetmesh = vtk.vtkUnstructuredGrid()
                    cells = vtk.vtkTetra()
                    for temp in gmsh_tet:
                        for k in range(len(temp)):
                            cells.GetPointIds().SetId(k, temp[k])
                        vtktetmesh.InsertNextCell(cells.GetCellType(), cells.GetPointIds())
                        color_array.InsertNextTuple3(color_list[1][0], color_list[1][1], color_list[1][2])
                    vtktetmesh.SetPoints(vtkpoints)
                    vtktetmesh.GetCellData().SetScalars(color_array)

                    self.mesh_render(vtktetmesh)
                    self.model_object[item]['tet mesh'] = vtktetmesh

                    self.statusbar.showMessage(f"{len(gmsh_tet)} elements created! ")
            except:
                self.statusbar.showMessage('Tetrahedrization wrong!')
                print(Fore.RED + f"Error   : {gmsh.logger.getLastError()}" + Fore.RESET)

        gmsh.finalize()

    def show_tet_mesh(self):
        item = self.treeWidget.currentItem().text(0)
        self.tetmesh = self.model_object[item]['tet mesh']
        self.mesh_render(self.tetmesh)

    def show_tet_point(self):
        item = self.treeWidget.currentItem().text(0)
        tetpoint = self.model_object[item]['tet point']
        V, T, Q = vtk_numpy(tetpoint)
        color, point_size = self.get_PC_color_size()
        self.point_cloud_render(V, color, point_size)

    def export_tetmesh(self):
        item = self.treeWidget.currentItem().text(0)
        tetmesh = self.model_object[item]['tet mesh']
        mesh = vtk_meshio(tetmesh)
        currentPath = QDir.currentPath()
        title = "Export"
        # filter = "Abaqus INP(*.inp);;Gmsh MSH(*.msh);;LSDYNA KEY(*.key);;CELUM(*.celum);;" \
        #          "MATLAB(*.m);;Nastran Bulk Data File(*.bdf);;STL Surface(*.stl);;VTK(*.vtk);;PLY2 Surface(*.ply2)"
        fileList, filtUsed = QFileDialog.getSaveFileName(self, title, currentPath)
        if fileList:
            try:
                mesh.write(fileList)
                self.statusbar.showMessage('File saved in ： ' + fileList)
                print(f"Info    : File saved in ： ' {fileList}")
            except:
                self.statusbar.showMessage('Error! Unsupported format!')
                print(Fore.RED + "Error   : Unsupported format" + Fore.RESET)

    """
    Mesh edit
    """

    def show_mesh_edit(self):
        item = self.treeWidget.currentItem().text(0)
        self.mesh = self.model_object[item]['surface mesh']
        self.mesh_render(self.mesh)

        self.Win_mesh_edit = Win_mesh_edit()
        self.Win_mesh_edit.show()

        self.Win_mesh_edit.mesh_delete.clicked.connect(self.mesh_delete)
        self.Win_mesh_edit.mesh_create.clicked.connect(self.mesh_create)
        self.Win_mesh_edit.dialogSignal.connect(self.clear_mesh_edit)

    def clear_mesh_edit(self, msg):
        self.renderer.RemoveAllViewProps()
        self.renderer.AddActor(self.actor)
        self.render_window.Render()
        self.style.RemoveObservers("LeftButtonPressEvent")
        self.style.RemoveObservers("RightButtonPressEvent")

    def mesh_delete(self, item):
        if self.Win_mesh_edit.mesh_delete.isChecked():
            # self.actor.GetProperty().SetRepresentationToWireframe()
            # If not BuildCells new elements may not display
            self.mesh.BuildCells()
            self.mesh.Modified()
            self.render_window.Render()
            self.delete_mesh = []
            self.statusbar.showMessage('Select elements to delete')

            self.style.AddObserver("LeftButtonPressEvent", self.mesh_delete_pick)
            self.style.AddObserver("RightButtonPressEvent", self.mesh_delete_unpick)
        else:
            self.style.RemoveObservers("LeftButtonPressEvent")
            self.style.RemoveObservers("RightButtonPressEvent")
            a = QMessageBox.question(self, 'Exit', 'Confirm delete?', QMessageBox.Yes | QMessageBox.No)
            if a == QMessageBox.Yes:
                self.mesh.BuildCells()
                for cellId in self.delete_mesh:
                    self.mesh.DeleteCell(cellId)

                self.mesh.RemoveDeletedCells()
                self.mesh.Modified()

                # self.model_object[item]['surface mesh'] = self.mesh
                self.polys = self.mesh.GetPolys()
                self.renderer.RemoveAllViewProps()
                self.mapper.SetInputData(self.mesh)
                self.mapper.Update()
                self.renderer.AddActor(self.actor)
                self.render_window.Render()
                print(f"Info    : {len(self.delete_mesh)} elements selected")
                self.statusbar.showMessage(f"{len(self.delete_mesh)} elements selected")
            else:
                self.renderer.RemoveAllViewProps()
                self.mapper.Update()
                self.actor.SetMapper(self.mapper)
                self.renderer.AddActor(self.actor)
                self.render_window.Render()

    def mesh_delete_pick(self, object1, event):
        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.005)
        self.iren.SetPicker(picker)
        pickPos = self.iren.GetEventPosition()
        picker.Pick(pickPos[0], pickPos[1], 0, self.renderer)
        # cell_data = self.mesh.GetCellData().GetScalars()
        if picker.GetCellId() > 0:
            self.delete_mesh.append(picker.GetCellId())
            delete_num = np.unique(np.array(self.delete_mesh)).shape[0]
            self.statusbar.showMessage(f"{delete_num} elements selected")
            self.mesh_delete_render(self.delete_mesh)

    def mesh_delete_render(self, cellId):
        self.renderer.RemoveAllViewProps()

        vtkmesh = vtk.vtkPolyData()
        vtkmesh.DeepCopy(self.mesh)
        cell_data = vtkmesh.GetCellData().GetScalars()
        # color = np.array(cell_data.GetTuple3(cellId))
        for cell in cellId:
            cell_data.SetTuple3(cell, 255, 0, 0)
        vtkmesh.GetCellData().SetScalars(cell_data)

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(vtkmesh)
        mapper.SetResolveCoincidentTopologyToPolygonOffset()
        mapper.SetScalarModeToUseCellData()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().EdgeVisibilityOn()
        actor.GetProperty().SetEdgeColor(0, 0, 0)
        self.renderer.AddActor(actor)
        self.renderer.Render()
        self.render_window.Render()

    def mesh_delete_unpick(self, object2, event):
        picker = vtk.vtkCellPicker()
        self.iren.SetPicker(picker)
        pickPos = self.iren.GetEventPosition()
        picker.Pick(pickPos[0], pickPos[1], 0, self.renderer)
        if picker.GetCellId() > 0:
            if picker.GetCellId() in self.delete_mesh:
                cell_data = self.mesh.GetCellData().GetScalars()
                color = np.array(cell_data.GetTuple3(picker.GetCellId()))
                self.delete_mesh.remove(picker.GetCellId())
                self.mesh_delete_render(self.delete_mesh)
                # self.render_window.Render()

    def mesh_create(self):
        if self.Win_mesh_edit.mesh_create.isChecked():
            # self.actor.GetProperty().SetRepresentationToWireframe()
            point_pos = vtk.vtkPolyData()
            point_pos.DeepCopy(self.mesh)
            vertex = vtk.vtkVertexGlyphFilter()
            vertex.SetInputData(point_pos)

            point_mapper = vtk.vtkDataSetMapper()
            point_mapper.SetInputConnection(vertex.GetOutputPort())

            self.point_actor = vtk.vtkActor()
            self.point_actor.SetMapper(point_mapper)
            self.point_actor.GetProperty().SetRepresentationToPoints()
            self.point_actor.GetProperty().SetColor(1, 0, 0)
            self.point_actor.GetProperty().SetPointSize(5)

            self.mesh.Modified()
            self.renderer.AddActor(self.point_actor)
            self.render_window.Render()
            self.statusbar.showMessage('Pick first point')

            self.new_mesh_point = []
            self.polys = self.mesh.GetPolys()
            self.style.AddObserver("LeftButtonPressEvent", self.mesh_create_pick)

        else:
            self.style.RemoveObservers("LeftButtonPressEvent")
            self.statusbar.showMessage('Finish')

            self.mesh_render(self.mesh)

    def mesh_create_pick(self, object1, event):
        picker = vtk.vtkPointPicker()
        picker.SetTolerance(0.005)
        self.iren.SetPicker(picker)
        pickPos = self.iren.GetEventPosition()
        picker.Pick(pickPos[0], pickPos[1], 0, self.renderer)
        if picker.GetPointId() != -1:
            self.new_mesh_point.append(picker.GetPointId())
            point_select = vtk.vtkPolyData()
            vtkpoints = vtk.vtkPoints()
            vertices = []
            point = [0.000000] * 3
            self.mesh.GetPoint(picker.GetPointId(), point)
            vertices.append([point[0], point[1], point[2]])
            vtkpoints.SetData(numpy_to_vtk(np.asarray(np.array(vertices))))
            point_select.SetPoints(vtkpoints)

            vertex = vtk.vtkVertexGlyphFilter()
            vertex.SetInputData(point_select)

            point_mapper = vtk.vtkDataSetMapper()
            point_mapper.SetInputConnection(vertex.GetOutputPort())
            point_mapper.SetResolveCoincidentTopologyPointOffsetParameter(-4)
            point_mapper.SetRelativeCoincidentTopologyPointOffsetParameter(-4)

            point_select_actor = vtk.vtkActor()
            point_select_actor.SetMapper(point_mapper)
            point_select_actor.GetProperty().SetColor(0, 0, 1)
            point_select_actor.GetProperty().SetPointSize(5)

            self.mesh.Modified()
            self.renderer.AddActor(point_select_actor)
            self.render_window.Render()
            new_mesh_point = np.unique(np.array(self.new_mesh_point))

            if len(new_mesh_point) % 3 == 1:
                self.statusbar.showMessage('Pick second point')
            if len(new_mesh_point) % 3 == 2:
                self.statusbar.showMessage('Pick third point')
            if len(new_mesh_point) % 3 == 0:

                print(f"Info    : Element created : {new_mesh_point}")
                self.statusbar.showMessage(f"Element created : {new_mesh_point}")

                polys = self.mesh.GetPolys()
                color_array = self.mesh.GetCellData().GetScalars()

                polys.InsertNextCell(3, np.array(new_mesh_point))
                color_array.InsertNextTuple3(0, 0, 255)

                self.mesh.SetPolys(polys)
                self.mesh.GetCellData().SetScalars(color_array)

                self.mesh.Modified()
                self.polys = self.mesh.GetPolys()

                self.new_mesh_point = []
                self.mesh_render(self.mesh)
                self.renderer.AddActor(self.point_actor)
                self.render_window.Render()

    """
    Render function
    """

    def mesh_render(self, mesh):
        self.renderer.RemoveAllViewProps()
        self.mapper = vtk.vtkDataSetMapper()
        # self.mapper.ScalarVisibilityOff()
        self.mapper.SetInputData(mesh)
        self.mapper.SetResolveCoincidentTopologyToPolygonOffset()
        self.mapper.SetScalarModeToUseCellData()

        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetRepresentationToWireframe()
        self.actor.GetProperty().EdgeVisibilityOn()
        self.actor.GetProperty().SetEdgeColor(0, 0, 0)
        # self.actor.GetProperty().SetColor(100 / 255, 240 / 255, 150 / 255)
        self.renderer.AddActor(self.actor)

        self.set_show_2d_mesh_boundary()
        self.set_show_2d_mesh_edge()
        self.set_show_2d_mesh_face()
        self.set_show_2d_mesh_label()
        self.set_show_2d_node_label()

        # self.renderer.ResetCamera()
        # self.render_window.Render()

    def point_cloud_render(self, point_cloud, color, size):
        if point_cloud.shape[1] == 3:
            point_cloud = np.hstack((np.zeros((point_cloud.shape[0], 1)), point_cloud))

        point_idx = np.unique(point_cloud[:, 0])

        points = vtk.vtkPoints()
        polydata = vtk.vtkPolyData()

        color_array = vtk.vtkUnsignedCharArray()
        color_array.SetNumberOfComponents(3)
        color_array.SetName("Colors")

        self.renderer.RemoveAllViewProps()
        for i in range(len(point_idx)):
            idx = np.where(point_cloud[:, 0] == point_idx[i])[0]
            pc = point_cloud[idx, 1:]
            np.savetxt('blade_wenzhe_5.txt', pc, fmt='%f')

            for point in pc:
                points.InsertNextPoint(np.array(point))
                if i == 0:
                    color_array.InsertNextTuple3(min(color[0] * 255, 255), min(color[1] * 255, 255),
                                                 min(color[2] * 255, 255))
                else:
                    color_array.InsertNextTuple3(color_list[i % len(color_list)][0],
                                                 color_list[i % len(color_list)][1],
                                                 color_list[i % len(color_list)][2])

        polydata.SetPoints(points)
        polydata.GetPointData().SetScalars(color_array)
        vertex = vtk.vtkVertexGlyphFilter()
        vertex.SetInputData(polydata)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(vertex.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetPointSize(size)
        win_render = vtk.vtkRenderWindowInteractor()
        win_render.SetRenderWindow(self.render_window)
        win_render.SetInteractorStyle(vtk.vtkInteractorStyleMultiTouchCamera())
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.render_window.Render()

    def show_aboutus(self):
        self.Win_aboutus = Win_aboutus()
        self.Win_aboutus.show()

    def show_helpdocs(self):
        self.Win_helpdoc = HelpDoc()
        self.Win_helpdoc.show()

    def closeEvent(self, event):
        reply = QMessageBox(QMessageBox.Question, self.tr("Exit Confirmation"),
                            self.tr(" Are you sure you want to exit the application？"), QMessageBox.NoButton, self)
        yr_btn = reply.addButton(self.tr("Confirm "), QMessageBox.YesRole)
        reply.addButton(self.tr("Cancel"), QMessageBox.NoRole)
        reply.exec_()
        if reply.clickedButton() == yr_btn:
            sys.exit()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = Win_Main()
    sys.exit(app.exec_())
