import sys
import vtkmodules.all as vtk
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSlider, QFrame, QFileDialog, QApplication, \
    QMessageBox
from PyQt5.QtGui import QIcon
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from qtrangeslider import QRangeSlider
from ImgMesh.Qss.QssList import *
from ImgMesh.Ui.Ui_ImportImage import *


class WIN_RENDER_THRESHOLD_SLIDER(QWidget):
    # Threshold setting for image segmentation
    threshold_signal = QtCore.pyqtSignal(list)

    def __init__(self, threshold_min, threshold_max):
        super().__init__()
        self.setWindowIcon(QIcon(':/icon/set.png'))
        self.frame = QFrame()
        self.HLayout_frame = QHBoxLayout(self.frame)

        self.setLayout(QVBoxLayout())
        self.setWindowTitle("Set render threshold")
        self.setGeometry(600, 300, 400, 100)
        self.setFixedSize(400, 100)
        self.setStyleSheet("QLabel{color:rgb(100,100,250);"
                           "font-size:15px;font-weight:bold;font-family:微软雅黑;}")

        self.threshold_slider = QRangeSlider(Qt.Horizontal)
        self.threshold_slider.setStyleSheet(QSS)
        self.threshold_slider.setRange(0, 255)
        self.threshold_slider.setValue((threshold_min, threshold_max))
        self.threshold_slider.setFixedSize(300, 20)

        self.threshold_slider_value = self.threshold_slider.value()
        self.threshold_slider_label1 = QLabel(str(self.threshold_slider_value[0]))
        self.threshold_slider_label2 = QLabel(str(self.threshold_slider_value[1]))

        # self.layout().addWidget(self.threshold_slider_label1)
        # self.layout().addWidget(self.threshold_slider)
        # self.layout().addWidget(self.threshold_slider_label2)
        self.HLayout_frame.addWidget(self.threshold_slider_label1)
        self.HLayout_frame.addWidget(self.threshold_slider)
        self.HLayout_frame.addWidget(self.threshold_slider_label2)

        self.button_box = QtWidgets.QDialogButtonBox()
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.layout().addWidget(self.frame)
        self.layout().addWidget(self.button_box)

        self.threshold_slider.valueChanged.connect(self.slider_value_changed)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.cancel)

    def slider_value_changed(self):
        threshold_slider_value = self.threshold_slider.value()
        self.threshold_slider_label1.setText(str(threshold_slider_value[0]))
        self.threshold_slider_label2.setText(str(threshold_slider_value[1]))

    def accept(self):
        image_threshold_set = [int(self.threshold_slider_label1.text()), int(self.threshold_slider_label2.text())]
        self.close()
        self.threshold_signal.emit(image_threshold_set)

    def cancel(self):
        self.close()


class WIN_IMPORT_IMAGE_SET(QWidget, Ui_ImportImage):
    img_signal = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(':/icon/set.png'))
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.cancel)

    def accept(self):
        img_set_info = [str(self.object_name.text()), float(self.resolution_x.text()),
                        float(self.resolution_y.text()), float(self.resolution_z.text())]
        self.close()
        self.img_signal.emit(img_set_info)

    def cancel(self):
        self.close()


class Img(QObject):
    img_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.image_parameters = None
        self.image_path = None
        self.threshold_min = 1
        self.threshold_max = 255
        self.win_import_image_set = WIN_IMPORT_IMAGE_SET()
        self.win_import_image_set.img_signal.connect(self.get_image_set)

    def get_image_set(self, image_parameters):
        self.image_parameters = image_parameters
        if self.image_parameters:
            file_array = vtk.vtkStringArray()
            for i in range(0, len(self.image_path)):
                file_array.InsertNextValue(self.image_path[i])
            # Identify image formats
            image_format = self.image_path[0].split('.')[-1]
            reader = None
            if image_format == 'bmp':
                reader = vtk.vtkBMPReader()
            elif image_format == 'tif':
                reader = vtk.vtkTIFFReader()
            elif image_format == 'png':
                reader = vtk.vtkPNGReader()
            elif image_format == 'jpg':
                reader = vtk.vtkJPEGReader()

            if reader:
                reader.SetFileNames(file_array)
                reader.SetDataSpacing(self.image_parameters[1],
                                      self.image_parameters[2],
                                      self.image_parameters[3])
                reader.Update()
                if reader.GetNumberOfScalarComponents() > 1:
                    luminance_filter = vtk.vtkImageLuminance()
                    luminance_filter.SetInputData(reader.GetOutput())
                    luminance_filter.Update()
                    vtkimagedata = luminance_filter.GetOutput()
                else:
                    vtkimagedata = reader.GetOutput()
                image_info = {'objectname': self.image_parameters[0],
                              'imagepath': self.image_path,
                              'vtkdata': vtkimagedata,
                              'resolution': [self.image_parameters[1], self.image_parameters[2],
                                             self.image_parameters[3]]}
                self.img_signal.emit(image_info)

    def select_image(self):
        image_filter = "All files(*.*);;bmp(*.bmp);;jpg(*.jpg);;png(*.png);;tif(*.tif)"
        self.image_path = QFileDialog.getOpenFileNames(filter=image_filter, caption="Select images")[0]
        if len(self.image_path) > 0:
            image_format = self.image_path[0].split('.')[-1]
            if image_format not in ['bmp', 'tif', 'png', 'jpg']:
                QMessageBox.critical(self.win_import_image_set, "Error", "Unsupported formats (bmp/tif/png/jpg)!")
                return
            folder_name = self.image_path[0].split('/')[-1]
            self.win_import_image_set.object_name.setText(folder_name.split('.')[0])
            self.win_import_image_set.show()


class ORTHOGONAL_VIEW(QWidget):
    def __init__(self, image, vol, threshold_min, threshold_max, position, focal_point, view_up):
        super().__init__()
        self.sliders, self.labels, self.widgets, self.render_list, self.planes = [], [], [], [], []
        self.setWindowTitle("Slider")
        self.setWindowIcon(QIcon(':/icon/slider.png'))
        self.setGeometry(850, 100, 400, 200)
        self.setFixedSize(400, 200)
        self.setLayout(QVBoxLayout())
        self.setStyleSheet("QLabel{color:rgb(100,100,250);"
                           "font-size:12px;font-weight:bold;font-family:微软雅黑;}")

        self.create_gui(image)
        self.show()
        self.camera_position = position
        self.camera_focal_point = focal_point
        self.camera_view_up = view_up
        self.create_ortho_views(image, vol, threshold_min, threshold_max)

    def create_gui(self, image):
        dimension = image.GetDimensions()

        for axis in [0, 1, 2]:
            self.sliders.append(QSlider(Qt.Horizontal))
            self.sliders[axis].setStyleSheet(QSS1)
            self.sliders[axis].setRange(1, dimension[axis])
            self.sliders[axis].setValue(1)

            self.labels.append(QLabel('1'))
            self.labels[axis].setFixedWidth(30)

            self.widgets.append(QWidget())
            self.widgets[axis].setLayout(QHBoxLayout())
            self.widgets[axis].layout().addWidget(self.sliders[axis])
            self.widgets[axis].layout().addWidget(self.labels[axis])

            self.layout().addWidget(self.widgets[axis])

        self.sliders[0].valueChanged.connect(
            lambda: self.slider_value_changed(self.sliders[0], self.planes[0], self.render_list[0], self.labels[0]))
        self.sliders[1].valueChanged.connect(
            lambda: self.slider_value_changed(self.sliders[1], self.planes[1], self.render_list[1], self.labels[1]))
        self.sliders[2].valueChanged.connect(
            lambda: self.slider_value_changed(self.sliders[2], self.planes[2], self.render_list[2], self.labels[2]))

    def slider_value_changed(self, slider, plane, render, label):
        slice_index = slider.value() - 1
        plane.SetSliceIndex(slice_index)
        render.ResetCamera()
        label.setText(str(slider.value()))
        self.ortho_window.Render()

    def create_ortho_views(self, image, vol, threshold_min, threshold_max):
        self.ortho_window = vtk.vtkRenderWindow()
        interactor = vtk.vtkRenderWindowInteractor()

        style = vtk.vtkInteractorStyleTrackballCamera()
        interactor.SetInteractorStyle(style)

        self.ortho_window.SetInteractor(interactor)
        self.ortho_window.SetWindowName("ortho_window")
        self.ortho_window.SetSize(800, 600)

        dimensions = image.GetDimensions()

        xmins = [0, 0.5, 0, 0.5]
        xmaxs = [0.5, 1, 0.5, 1]
        ymins = [0, 0.5, 0.5, 0]
        ymaxs = [0.5, 1, 1, 0.5]
        background_color = [(0.1843, 0.3098, 0.3098), (0.2235, 0.2314, 0.4745), (0, 0.3922, 0), (0.5, 0.5, 0.5)]

        for i in range(4):
            renderer = vtk.vtkRenderer()
            self.render_list.append(renderer)
            self.ortho_window.AddRenderer(renderer)
            renderer.SetViewport(xmins[i], ymins[i], xmaxs[i], ymaxs[i])
            renderer.SetBackground(background_color[i])

        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.005)

        for axis, color in zip(["X", "Y", "Z"], [(1, 0, 0), (1, 1, 0), (0, 0, 1)]):
            plane = vtk.vtkImagePlaneWidget()
            plane.DisplayTextOn()
            plane.SetInputData(image)
            plane.SetPicker(picker)
            plane.SetKeyPressActivationValue(axis.lower())
            plane.SetDefaultRenderer(self.render_list[["X", "Y", "Z"].index(axis)])
            plane.SetPlaneOrientationToXAxes() if axis == "X" else plane.SetPlaneOrientationToYAxes() if axis == "Y" else plane.SetPlaneOrientationToZAxes()
            plane.SetSliceIndex(1)
            prop = plane.GetPlaneProperty()
            prop.SetColor(color)
            plane.SetInteractor(interactor)
            plane.On()
            self.planes.append(plane)

        camera = self.render_list[0].GetActiveCamera()
        camera.SetFocalPoint(0, 0, 0)
        camera.SetPosition(1, 0, 0)
        camera.SetViewUp(0, 1, 0)
        self.render_list[0].ResetCamera()
        camera = self.render_list[1].GetActiveCamera()
        camera.SetFocalPoint(0, 0, 0)
        camera.SetPosition(0, 1, 0)
        camera.SetViewUp(0, 0, -1)
        self.render_list[1].ResetCamera()

        if vol:
            self.render_list[3].AddVolume(vol)
            camera = self.render_list[3].GetActiveCamera()
            camera.SetPosition(self.camera_position)
            camera.SetFocalPoint(self.camera_focal_point)
            camera.SetViewUp(self.camera_view_up)

        self.render_list[3].ResetCamera()
        self.ortho_window.Render()
        interactor.Start()


def volume_render(vtkdata, renderer_window, colors):
    renderer = renderer_window.GetRenderers().GetFirstRenderer()
    renderer.RemoveAllViewProps()
    renderer_window.Render()
    renderer_window.AddRenderer(renderer)

    range1 = vtkdata.GetScalarRange()
    shift_scale = vtk.vtkImageShiftScale()
    # shift_scale.SetScale(255 / (range1[1] - range1[0]))
    shift_scale.SetInputData(vtkdata)
    shift_scale.Update()

    dimension = vtkdata.GetDimensions()
    if dimension[2] < 2:
        rows, cols, _ = vtkdata.GetDimensions()
        vtk_array = vtkdata.GetPointData().GetScalars()
        numpy_array = vtk_to_numpy(vtk_array)
        temp = numpy_array.reshape(dimension, order='F')
        temp = np.repeat(temp, 2, axis=2)

        shape = temp.shape[::-1]
        vtk_data = numpy_to_vtk(temp.ravel(), 1, vtk.VTK_SHORT)

        image_data = vtk.vtkImageData()
        image_data.SetDimensions(shape)
        image_data.SetSpacing([1, 1, 1])
        image_data.SetOrigin([0, 0, 0])
        image_data.GetPointData().SetScalars(vtk_data)

        volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
        volume_mapper.SetInputData(image_data)
        color_func = vtk.vtkColorTransferFunction()
        for color in colors:
            color_func.AddRGBPoint(color[0], color[1] / 255, color[2] / 255, color[3] / 255)

        opacity_func = vtk.vtkPiecewiseFunction()
        opacity_func.AddPoint(-1, 1)
        opacity_func.AddPoint(255, 1)
        opacity_func.ClampingOff()

        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(color_func)
        volume_property.SetScalarOpacity(opacity_func)
        # volume_property.SetInterpolationTypeToLinear()
        volume_property.ShadeOff()

    else:
        volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
        volume_mapper.SetInputData(vtkdata)
        color_func = vtk.vtkColorTransferFunction()
        for color in colors:
            color_func.AddRGBPoint(color[0], color[1] / 255, color[2] / 255, color[3] / 255)

        opacity_func = vtk.vtkPiecewiseFunction()
        opacity_func.AddPoint(0, 1)
        opacity_func.AddPoint(255, 1)
        opacity_func.ClampingOff()

        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(color_func)
        volume_property.SetScalarOpacity(opacity_func)
        # volume_property.SetInterpolationTypeToLinear()
        volume_property.ShadeOn()

    vol = vtk.vtkVolume()
    vol.SetMapper(volume_mapper)
    vol.SetProperty(volume_property)
    renderer.AddVolume(vol)

    renderer.ResetCamera()
    renderer_window.Render()

    return vol


def image_render(vtkdata, renderer_window):
    renderer = renderer_window.GetRenderers().GetFirstRenderer()
    renderer.RemoveAllViewProps()
    renderer_window.AddRenderer(renderer)

    interactor = vtk.vtkRenderWindowInteractor()

    picker = vtk.vtkCellPicker()
    picker.SetTolerance(0.005)

    plane = vtk.vtkImagePlaneWidget()
    plane.DisplayTextOn()
    plane.SetInputData(vtkdata)
    plane.SetPicker(picker)
    # plane.SetKeyPressActivationValue(axis.lower())
    plane.SetDefaultRenderer(renderer)
    plane.SetPlaneOrientationToXAxes()
    plane.SetSliceIndex(1)
    prop = plane.GetPlaneProperty()
    prop.SetColor(1, 0, 0)
    plane.SetInteractor(interactor)
    plane.On()
    renderer.ResetCamera()
    renderer_window.Render()


def draw_bounding_box(vtkdata):
    outline = vtk.vtkOutlineFilter()
    outline.SetInputData(vtkdata)

    outline_mapper = vtk.vtkPolyDataMapper()
    outline_mapper.SetInputConnection(outline.GetOutputPort())

    outline_actor = vtk.vtkActor()
    outline_actor.SetMapper(outline_mapper)
    outline_actor.GetProperty().SetColor(1.0, 1.0, 1.0)
    return outline_actor


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = WIN_RENDER_THRESHOLD_SLIDER(0, 255)
    MainWindow.show()
    sys.exit(app.exec_())
