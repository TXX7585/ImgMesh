import meshio
import numpy as np
import vtkmodules.all as vtk
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTreeWidgetItem
from scipy.spatial import ConvexHull, distance_matrix, Delaunay
from shapely.geometry import Polygon, Point
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
import SimpleITK as sitk
from ImgMesh.Qss.QssList import color_list


def vtk_meshio(vtkmesh):
    cell_data = vtkmesh.GetCellData()
    color_array = cell_data.GetScalars()

    num_cells = vtkmesh.GetNumberOfCells()
    color_dict = {}

    tri = []
    quad = []
    tet = []
    for cell_id in range(num_cells):
        cell_type = vtkmesh.GetCellType(cell_id)
        color_value = color_array.GetTuple3(cell_id)
        color_key = tuple(color_value)

        if color_key not in color_dict:
            color_dict[color_key] = []

        color_dict[color_key].append(cell_id)

        cell = vtkmesh.GetCell(cell_id)
        num_points = cell.GetNumberOfPoints()

        node_ids = [cell.GetPointId(i) for i in range(num_points)]
        if num_points == 3 and cell_type == 5:
            tri.append(node_ids)
        elif num_points == 4 and cell_type == 9:
            quad.append(node_ids)
        elif num_points == 4 and cell_type == 10:
            tet.append(node_ids)

    meshio_cells = {}
    V = vtk_to_numpy(vtkmesh.GetPoints().GetData())

    cells = {}
    if tri is not None and len(tri) > 0:
        cells['triangle'] = tri
    if quad is not None and len(quad) > 0:
        cells['quad'] = quad
    if tet is not None and len(tet) > 0:
        cells['tetra'] = tet

    mesh = meshio.Mesh(points=V, cells=cells)

    ID = 0
    for color, cell_list in color_dict.items():  # Assuming all cells of the same color have the same cell type
        meshio_cells['Material' + str(ID)] = [np.array(cell_list), []]
        ID += 1

    mesh.cell_sets = meshio_cells

    return mesh


def meshio_vtk(mesh):
    vtkpoints = vtk.vtkPoints()
    vtkpoints.SetData(numpy_to_vtk(np.asarray(mesh.points)))

    cellarray = vtk.vtkCellArray()

    color_array = vtk.vtkUnsignedCharArray()
    color_array.SetNumberOfComponents(3)
    color_array.SetName("Colors")

    if 'quad' in mesh.cells_dict:
        cells_quad = mesh.cells_dict['quad']
    if 'triangle' in mesh.cells_dict:
        cells_triangle = mesh.cells_dict['triangle']

    if len(mesh.cell_sets_dict) > 1:
        # Set exists
        ID = 0
        for key, value in mesh.cell_sets_dict.items():
            if key == 'GMSH:BOUNDING_ENTITIES' or key == 'gmsh:bounding_entities':
                continue
            if 'triangle' in value:
                tri = cells_triangle[value['triangle'], :]
                for t in tri:
                    cellarray.InsertNextCell(3, t)
                    color_array.InsertNextTuple3(color_list[ID][0], color_list[ID][1], color_list[ID][2])

            if 'quad' in value:
                quad = cells_quad[value['quad'], :]
                for q in quad:
                    cellarray.InsertNextCell(4, q)
                    color_array.InsertNextTuple3(color_list[ID][0], color_list[ID][1], color_list[ID][2])
            ID += 1
    else:
        for key, value in mesh.cells_dict.items():
            if key == 'GMSH:BOUNDING_ENTITIES' or key == 'gmsh:bounding_entities':
                continue
            if key == 'triangle':
                for t in value:
                    cellarray.InsertNextCell(3, t)
                    color_array.InsertNextTuple3(color_list[0][0], color_list[0][1], color_list[0][2])
            if key == 'quad':
                for t in value:
                    cellarray.InsertNextCell(4, t)
                    color_array.InsertNextTuple3(color_list[0][0], color_list[0][1], color_list[0][2])

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(vtkpoints)
    polydata.SetPolys(cellarray)
    polydata.GetCellData().SetScalars(color_array)

    return polydata


def vtk_numpy(vtkobject):
    cells = vtkobject.GetPolys()
    if vtkobject.GetNumberOfCells() > 0:
        array = cells.GetData()
        tri = vtk_to_numpy(array)

        triangles = [tri[i + 1:i + 4] for i in range(0, len(tri), 4) if tri[i] == 3]
        quads = [tri[i + 1:i + 5] for i in range((len(triangles) - 1) * 4, len(tri), 5) if tri[i] == 4]

        # if tri.size > 0:
        #     tri = tri.reshape((cells.GetNumberOfCells(), -1))[:, 1:]
        vertices = vtk_to_numpy(vtkobject.GetPoints().GetData())
        return vertices, np.array(triangles), np.array(quads)
    else:
        vertices = vtk_to_numpy(vtkobject.GetPoints().GetData())
        return vertices, np.empty((0, 3)), np.empty((0, 4))


def numpy_vtk(vertices, tri=np.array([]), quad=np.array([])):
    polys = vtk.vtkCellArray()
    vtkpoints = vtk.vtkPoints()
    vtkpoints.SetData(numpy_to_vtk(np.asarray(vertices)))
    color_array = vtk.vtkUnsignedCharArray()
    color_array.SetNumberOfComponents(3)
    color_array.SetName("Colors")
    for t in tri:
        polys.InsertNextCell(3, t)
        color_array.InsertNextTuple3(color_list[0][0], color_list[0][1], color_list[0][2])
    for q in quad:
        polys.InsertNextCell(4, q)
        color_array.InsertNextTuple3(color_list[0][0], color_list[0][1], color_list[0][2])
    mesh = vtk.vtkPolyData()
    mesh.SetPoints(vtkpoints)
    mesh.SetPolys(polys)
    mesh.GetCellData().SetScalars(color_array)
    return mesh


def vtk_image_to_numpy(vtk_image):
    cols, rows, levels = vtk_image.GetDimensions()
    sc = vtk_image.GetPointData().GetScalars()
    imageArr = vtk_to_numpy(sc)
    image3D = imageArr.reshape(levels, rows, cols)
    return image3D


def vtk2sitk(vtkimg):
    """Takes a VTK image, returns a SimpleITK image."""
    sd = vtkimg.GetPointData().GetScalars()
    npdata = vtk_to_numpy(sd)

    dims = list(vtkimg.GetDimensions())
    origin = vtkimg.GetOrigin()
    spacing = vtkimg.GetSpacing()

    dims.reverse()
    npdata.shape = tuple(dims)

    sitkimg = sitk.GetImageFromArray(npdata)
    sitkimg.SetSpacing(spacing)
    sitkimg.SetOrigin(origin)

    if vtk.vtkVersion.GetVTKMajorVersion() >= 9:
        direction = vtkimg.GetDirectionMatrix()
        d = []
        for y in range(3):
            for x in range(3):
                d.append(direction.GetElement(y, x))
        sitkimg.SetDirection(d)
    return sitkimg


def generate_unique_key(base_key, key_list):
    new_key = base_key
    count = 1
    while new_key in key_list:
        new_key = f"{base_key}-{count}"
        count += 1
    return new_key


def update_tree(tree_item, new_key):
    item_names = []
    for i in range(tree_item.childCount()):
        child_item = tree_item.child(i)
        item_names.append(child_item.text(0))
    if new_key not in item_names:
        child = QTreeWidgetItem(tree_item)
        child.setText(0, new_key)
        child.setFont(0, QFont('Times', 10, QFont.Black))


def mesh_quality(vtkmesh):
    num_cells = vtkmesh.GetNumberOfCells()

    tri = []
    quad = []
    for cell_id in range(num_cells):
        cell_type = vtkmesh.GetCellType(cell_id)
        cell = vtkmesh.GetCell(cell_id)
        num_points = cell.GetNumberOfPoints()
        node_ids = [cell.GetPointId(i) for i in range(num_points)]
        if num_points == 3 and cell_type == 5:
            tri.append(node_ids)
        elif num_points == 4 and cell_type == 9:
            quad.append(node_ids)

    V = vtk_to_numpy(vtkmesh.GetPoints().GetData())
    tri_qua = tri_quality(V, np.array(tri))
    quad_qua = quad_quality(V, np.array(quad))

    return tri_qua,quad_qua


def tri_quality(V, T):
    if T.shape[0] == 0:
        return np.array([])
    a = np.sqrt(np.sum((V[T[:, 1], :] - V[T[:, 0], :]) ** 2, axis=1))
    b = np.sqrt(np.sum((V[T[:, 2], :] - V[T[:, 0], :]) ** 2, axis=1))
    c = np.sqrt(np.sum((V[T[:, 2], :] - V[T[:, 1], :]) ** 2, axis=1))
    p = (a + b + c) / 2
    S = np.sqrt(p * (p - a) * (p - b) * (p - c))
    alpha = 4 * np.sqrt(3) * S / (a ** 2 + b ** 2 + c ** 2)
    return alpha


def quad_quality(V, Q):
    if Q.shape[0] == 0:
        return np.array([])
    a = np.sqrt(np.sum((V[Q[:, 1], :] - V[Q[:, 0], :]) ** 2, axis=1))
    b = np.sqrt(np.sum((V[Q[:, 2], :] - V[Q[:, 1], :]) ** 2, axis=1))
    c = np.sqrt(np.sum((V[Q[:, 3], :] - V[Q[:, 2], :]) ** 2, axis=1))
    d = np.sqrt(np.sum((V[Q[:, 0], :] - V[Q[:, 3], :]) ** 2, axis=1))

    X = V[Q, 0]
    Y = V[Q, 1]
    S = np.zeros(X.shape[0])
    for i in range(X.shape[0]):
        x = X[i, :]
        y = Y[i, :]
        S[i] = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    alpha = 4 * S / (a ** 2 + b ** 2 + c ** 2 + d ** 2)
    return alpha


def isInPolygon(point, polygon):
    x, y = point[0], point[1]
    nCross = 0
    for i in range(len(polygon)):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % len(polygon)]

        if p1[1] == p2[1]: continue

        if y < min(p1[1], p2[1]): continue

        if y >= max(p1[1], p2[1]): continue

        crossx = (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1]) + p1[0]

        if crossx >= x:
            nCross = nCross + 1
    return nCross % 2 == 1


def create_nodes_inpolygon(V, gridsize, threshold, holes):
    min_x, max_x = min(V[:, 0]), max(V[:, 0])

    min_y, max_y = min(V[:, 1]), max(V[:, 1])

    x_coords_1 = np.arange(min_x, max_x, gridsize)
    x_coords_2 = np.arange(min_x + gridsize / 2, max_x, gridsize)

    y_coords_1 = np.arange(min_y, max_y, 2 * 0.866 * gridsize)
    y_coords_2 = np.arange(min_y + 0.866 * gridsize, max_y, 2 * 0.866 * gridsize)

    grid_points1_x = np.array(np.tile(x_coords_1, y_coords_1.shape[0]))
    grid_points1_y = np.array(np.repeat(y_coords_1, x_coords_1.shape[0]))

    grid_points1 = np.hstack((grid_points1_x.reshape([-1, 1]), grid_points1_y.reshape([-1, 1])))

    grid_points2_x = np.array(np.tile(x_coords_2, y_coords_2.shape[0]))
    grid_points2_y = np.array(np.repeat(y_coords_2, x_coords_2.shape[0]))

    grid_points2 = np.hstack((grid_points2_x.reshape([-1, 1]), grid_points2_y.reshape([-1, 1])))

    grid_points = np.vstack((grid_points1, grid_points2))
    grid_points = np.hstack((grid_points, np.full((grid_points.shape[0], 1), V[0, 2])))

    p_keep = np.zeros(grid_points.shape[0], dtype=bool)

    polygon = Polygon(V)
    holes_polygons = [Polygon(hole) for hole in holes]

    for ind in range(grid_points.shape[0]):
        p = grid_points[ind]
        distances = np.sqrt(np.sum((p - V) ** 2, axis=1))

        point = Point(p[:2])

        # If in polygon
        if point.within(polygon) and all(not point.within(hole) for hole in holes_polygons) \
                and min(distances) > gridsize * threshold:
            p_keep[ind] = True
    return grid_points[p_keep, :]


def mesh_union(V1, T1, V2, T2):
    V = np.vstack((V1, V2))
    T = np.vstack((T1, T2 + np.size(V1, 0)))
    T = np.unique(T, axis=0)

    AA, BB, CC = np.unique(V, axis=0, return_index=True, return_inverse=True)

    order_idx = np.argsort(BB)
    V_out = V[BB[order_idx]]

    sorter = np.argsort(order_idx)
    CC = sorter[np.searchsorted(order_idx, CC, sorter=sorter)]
    T_out = CC[T]

    return V_out, T_out


def point2polygon(bound, threshold, size):
    bound_new, featurepoints = extract_feature_points(bound, threshold)
    featurepoints = featurepoints.tolist()
    bound_new = bound_new.tolist()
    qualify_list = [bound_new[0]]

    dis_accu = 0
    for i in range(1, len(bound_new) - 1):
        dis = np.sqrt(np.sum([(bound_new[i][0] - bound_new[i + 1][0]) ** 2,
                              (bound_new[i][1] - bound_new[i + 1][1]) ** 2]))
        dis_accu += dis
        if dis_accu > size or (bound_new[i] in featurepoints and dis_accu > size / 2):
            qualify_list.append(bound_new[i])
            dis_accu = 0
    dis_end = np.sqrt(np.sum([(qualify_list[0][0] - qualify_list[-1][0]) ** 2,
                              (qualify_list[0][1] - qualify_list[-1][1]) ** 2]))
    if dis_end < size / 2:
        qualify_list.pop()
    return qualify_list


def extract_feature_points(bound, threshold):
    # Calculate the convex hull
    hull = ConvexHull(bound)
    candidates = bound[hull.vertices]

    dist_mat = distance_matrix(candidates, candidates)
    i, j = np.unravel_index(dist_mat.argmax(), dist_mat.shape)

    point_i = candidates[i]
    point_j = candidates[j]

    point_i_index = np.where((bound == candidates[i]).all(axis=1))[0][0]
    point_j_index = np.where((bound == candidates[j]).all(axis=1))[0][0]

    # Split the contour
    part_i = bound[point_i_index:point_j_index + 1, :]
    part_j = np.vstack((bound[point_j_index:, :], bound[:point_j_index + 1, :]))

    featurepoints_i = douglas_peuker(part_i, threshold)
    featurepoints_j = douglas_peuker(part_j, threshold)

    featurepoints = np.vstack((featurepoints_i, featurepoints_j, point_i, point_j))

    bound_new = np.vstack((bound[point_i_index:], bound[:point_i_index]))

    return bound_new, featurepoints


def douglas_peuker(points, epsilon):
    if len(points) <= 2:
        return points
    max_distance = 0
    max_index = 0
    for i in range(1, len(points) - 1):
        distance = point_2_line_distance(points[i], points[0], points[-1])
        if distance > max_distance:
            max_distance = distance
            max_index = i
    if max_distance > epsilon:
        # Recursive call on the left and right segments
        left_simplified = douglas_peuker(points[:max_index + 1], epsilon)
        right_simplified = douglas_peuker(points[max_index:], epsilon)

        # Combine the results
        return np.vstack((left_simplified[:-1], right_simplified))
    else:
        # Return just the endpoints if the maximum distance is small enough
        return np.array([points[0], points[-1]])


def point_2_line_distance(point_a, point_b, point_c):
    if point_b[0] == point_c[0]:
        return 9999999
    slope = (point_b[1] - point_c[1]) / (point_b[0] - point_c[0])
    intercept = point_b[1] - slope * point_b[0]

    distance = abs(slope * point_a[0] - point_a[1] + intercept) / np.sqrt(1 + pow(slope, 2))
    return distance


def calculate_R(vertices, t):
    a = np.sqrt(np.sum((vertices[t[:, 1], :] - vertices[t[:, 0], :]) ** 2, axis=1))
    b = np.sqrt(np.sum((vertices[t[:, 2], :] - vertices[t[:, 0], :]) ** 2, axis=1))
    c = np.sqrt(np.sum((vertices[t[:, 2], :] - vertices[t[:, 1], :]) ** 2, axis=1))

    p = (a + b + c) / 2
    S = np.sqrt(p * (p - a) * (p - b) * (p - c))
    R = (a * b * c) / (4 * S)

    return R


def connectivity(tetr):
    numt = tetr.shape[0]
    vect = np.arange(0, numt)

    # Create t matrix
    t = np.vstack((tetr[:, [0, 1, 2]], tetr[:, [1, 2, 3]], tetr[:, [0, 2, 3]], tetr[:, [0, 1, 3]]))
    t = np.sort(t, axis=1)

    # Find unique rows and their indices
    t, ia, j = np.unique(t, axis=0, return_index=True, return_inverse=True)

    t2tetr = np.column_stack((j[vect], j[vect + numt], j[vect + 2 * numt], j[vect + 3 * numt]))

    # Initialize tetr2t and count arrays
    nume = t.shape[0]
    tetr2t = np.full((nume, 2), -1, dtype=np.int32)
    count = np.zeros((nume,), dtype=np.int32)

    # Calculate tetr2t
    for k in range(numt):
        for j in range(4):
            ce = t2tetr[k, j]
            tetr2t[ce, count[ce]] = k
            count[ce] += 1

    return tetr2t, t2tetr, t


def tri_angle(p1, p2, p3, p4):
    # Compute angle between two triangles(method in robust crust)
    v21 = (p1 - p2)
    v31 = (p3 - p1)

    tnorm1 = np.array([v21[1] * v31[2] - v21[2] * v31[1],
                       v21[2] * v31[0] - v21[0] * v31[2],
                       v21[0] * v31[1] - v21[1] * v31[0]])

    tnorm1 = tnorm1 / np.linalg.norm(tnorm1)

    v41 = (p4 - p1)
    tnorm2 = np.array([v21[1] * v41[2] - v21[2] * v41[1],
                       v21[2] * v41[0] - v21[0] * v41[2],
                       v21[0] * v41[1] - v21[1] * v41[0]])

    tnorm2 = tnorm2 / np.linalg.norm(tnorm2)

    alpha = np.dot(tnorm1, tnorm2)

    if alpha > 1:
        alpha = 1
    if alpha < -1:
        alpha = -1

    return alpha


def tri_angle2(p1, p2, p3, p4, planenorm):
    # Check if p4 is above or below the plane defined by planenorm and p3
    test = np.sum(planenorm * (p4 - p3))

    # Compute angle between two triangles
    v21 = p1 - p2
    v31 = p3 - p1
    tnorm1 = np.cross(v21, v31)
    tnorm1 /= np.linalg.norm(tnorm1)

    v41 = p4 - p1
    tnorm2 = np.cross(v21, v41)
    tnorm2 /= np.linalg.norm(tnorm2)

    temp = np.dot(tnorm1, np.transpose(tnorm2))
    if temp > 1:
        temp = 1
    elif temp < -1:
        temp = -1

    alpha = np.arccos(temp)

    # If p4 is below the plane, adjust the angle
    if test < 0:
        alpha = alpha + 2 * (np.pi - alpha)

    # Check the orientation of the second triangle
    planenorm = np.squeeze(np.asarray(planenorm))

    tnorm1 = np.squeeze(np.asarray(tnorm1))

    testor = np.dot(planenorm, tnorm1)
    if testor > 0:
        tnorm2 = -tnorm2

    return alpha, tnorm2


def tri_angle3(p1, p2, p3, p4):
    # Compute angle between two triangles(my method)
    v12 = p1 - p2
    v32 = p3 - p2
    tnorm1 = np.cross(v12, v32)
    tnorm1 /= np.linalg.norm(tnorm1)

    v42 = p4 - p2
    tnorm2 = np.cross(v42, v12)
    tnorm2 /= np.linalg.norm(tnorm2)

    temp = np.dot(tnorm1, tnorm2)
    if temp > 1:
        temp = 1
    elif temp < -1:
        temp = -1

    alpha = np.arccos(temp)

    return alpha


def t_norm(p, t):
    numt = t.shape[0]
    tnorm1 = np.zeros((numt, 3))

    v21 = p[t[:, 0]] - p[t[:, 1]]
    v31 = p[t[:, 2]] - p[t[:, 0]]

    tnorm1[:, 0] = v21[:, 1] * v31[:, 2] - v21[:, 2] * v31[:, 1]
    tnorm1[:, 1] = v21[:, 2] * v31[:, 0] - v21[:, 0] * v31[:, 2]
    tnorm1[:, 2] = v21[:, 0] * v31[:, 1] - v21[:, 1] * v31[:, 0]

    L = np.sqrt(np.sum(tnorm1 ** 2, axis=1))

    tnorm1[:, 0] = tnorm1[:, 0] / L
    tnorm1[:, 1] = tnorm1[:, 1] / L
    tnorm1[:, 2] = tnorm1[:, 2] / L

    return tnorm1


def py_delaunay(p):
    N = 3  # The dimensions of our points
    options = 'Qt Qbb Qc' if N <= 3 else 'Qt Qbb Qc Qx'  # Set the QHull options
    t = Delaunay(p, qhull_options=options).simplices
    keep = np.ones(len(t), dtype=bool)
    for i, j in enumerate(t):
        if abs(np.linalg.det(np.hstack((p[j], np.ones([1, N + 1]).T)))) < 1E-15:
            keep[i] = False  # Point is coplanar, we don't want to keep it
    t = t[keep, :]
    return t


def front_view(render_window):
    renderer = render_window.GetRenderers().GetFirstRenderer()
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(0, 0, 0)
    camera.SetPosition(0, 0, 1)
    camera.SetViewUp(0, 1, 0)
    renderer.ResetCamera()
    render_window.Render()


def back_view(render_window):
    renderer = render_window.GetRenderers().GetFirstRenderer()
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(0, 0, 0)
    camera.SetPosition(0, 0, -1)
    camera.SetViewUp(0, 1, 0)
    renderer.ResetCamera()
    render_window.Render()


def left_view(render_window):
    renderer = render_window.GetRenderers().GetFirstRenderer()
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(0, 0, 0)
    camera.SetPosition(-1, 0, 0)
    camera.SetViewUp(0, 1, 0)
    renderer.ResetCamera()
    render_window.Render()


def right_view(render_window):
    renderer = render_window.GetRenderers().GetFirstRenderer()
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(0, 0, 0)
    camera.SetPosition(1, 0, 0)
    camera.SetViewUp(0, 1, 0)
    renderer.ResetCamera()
    render_window.Render()


def top_view(render_window):
    renderer = render_window.GetRenderers().GetFirstRenderer()
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(0, 0, 0)
    camera.SetPosition(0, 1, 0)
    camera.SetViewUp(0, 0, -1)
    renderer.ResetCamera()
    render_window.Render()


def bottom_view(render_window):
    renderer = render_window.GetRenderers().GetFirstRenderer()
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(0, 0, 0)
    camera.SetPosition(0, -1, 0)
    camera.SetViewUp(0, 0, 1)
    renderer.ResetCamera()
    render_window.Render()


def iso_view(render_window):
    renderer = render_window.GetRenderers().GetFirstRenderer()
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(0, 0, 0)
    camera.SetPosition(-1, 1, 1)
    camera.SetViewUp(1, 0, 0)
    renderer.ResetCamera()
    render_window.Render()


# Mesh Hole Filling：https://github.com/kentechx/hole-filling
import numpy as np
import igl
import scipy
import scipy.sparse
import scipy.sparse.linalg
from typing import List, Tuple

_epsilon = 1e-16


def close_hole(vs: np.ndarray, fs: np.ndarray, hole_vids, fast=True) -> np.ndarray:
    """
    :param hole_vids: the vid sequence
    :return:
        out_fs:
    """

    def hash_func(edges):
        # edges: (n, 2)
        edges = np.core.defchararray.chararray.encode(edges.astype('str'))
        edges = np.concatenate([edges[:, 0:1], np.full_like(edges[:, 0:1], "_", dtype=str), edges[:, 1:2]], axis=1)
        edges_hash = np.core.defchararray.add(np.core.defchararray.add(edges[:, 0], edges[:, 1]), edges[:, 2])
        return edges_hash

    # create edge hash
    if not fast:
        edges = igl.edges(fs)
        edges_hash = hash_func(edges)

    hole_vids = np.array(hole_vids)
    if len(hole_vids) < 3:
        return fs.copy()

    if len(hole_vids) == 3:
        # fill one triangle
        out_fs = np.concatenate([fs, hole_vids[::-1][None]], axis=0)
        return out_fs

    # heuristically divide the hole
    queue = [hole_vids[::-1]]
    out_fs = []
    while len(queue) > 0:
        cur_vids = queue.pop(0)
        if len(cur_vids) == 3:
            out_fs.append(cur_vids)
            continue

        # current hole
        hole_edge_len = np.linalg.norm(vs[np.roll(cur_vids, -1)] - vs[cur_vids], axis=1)
        hole_len = np.sum(hole_edge_len)
        min_concave_degree = np.inf
        tar_i, tar_j = -1, -1
        for i in range(len(cur_vids)):
            eu_dists = np.linalg.norm(vs[cur_vids[i]] - vs[cur_vids], axis=1)
            if not fast:
                # check if the edge exists
                _edges = np.sort(np.stack([np.tile(cur_vids[i], len(cur_vids)), cur_vids], axis=1), axis=1)
                _edges_hash = hash_func(_edges)
                eu_dists[np.isin(_edges_hash, edges_hash, assume_unique=True)] = np.inf

            geo_dists = np.roll(np.roll(hole_edge_len, -i).cumsum(), i)
            geo_dists = np.roll(np.minimum(geo_dists, hole_len - geo_dists), 1)
            concave_degree = eu_dists / (geo_dists ** 2 + _epsilon)
            concave_degree[i] = -np.inf  # there may exist two duplicate vertices

            _idx = 1
            j = np.argsort(concave_degree)[_idx]
            while min((j + len(cur_vids) - i) % len(cur_vids), (i + len(cur_vids) - j) % len(cur_vids)) <= 1:
                _idx += 1
                j = np.argsort(concave_degree)[_idx]

            if concave_degree[j] < min_concave_degree:
                min_concave_degree = concave_degree[j]
                tar_i, tar_j = min(i, j), max(i, j)

        queue.append(cur_vids[tar_i:tar_j + 1])
        queue.append(np.concatenate([cur_vids[tar_j:], cur_vids[:tar_i + 1]]))

    out_fs = np.concatenate([fs, np.array(out_fs)], axis=0)
    return out_fs


def close_holes(vs: np.ndarray, fs: np.ndarray, hole_len_thr: float = 10000., fast=True) -> np.ndarray:
    """
    Close holes whose length is less than a given threshold.
    :param edge_len_thr:
    :return:
        out_fs: output faces
    """
    out_fs = fs.copy()
    while True:
        updated = False
        for b in igl.all_boundary_loop(out_fs):
            hole_edge_len = np.linalg.norm(vs[np.roll(b, -1)] - vs[b], axis=1).sum()
            if len(b) >= 3 and hole_edge_len <= hole_len_thr:
                out_fs = close_hole(vs, out_fs, b, fast)
                updated = True

        if not updated:
            break

    return out_fs


def get_mollified_edge_length(vs: np.ndarray, fs: np.ndarray, mollify_factor=1e-5) -> np.ndarray:
    lin = igl.edge_lengths(vs, fs)
    if mollify_factor == 0:
        return lin
    delta = mollify_factor * np.mean(lin)
    eps = np.maximum(0, delta - lin[:, 0] - lin[:, 1] + lin[:, 2])
    eps = np.maximum(eps, delta - lin[:, 0] - lin[:, 2] + lin[:, 1])
    eps = np.maximum(eps, delta - lin[:, 1] - lin[:, 2] + lin[:, 0])
    eps = eps.max()
    lin += eps
    return lin


def mesh_fair_laplacian_energy(vs: np.ndarray, fs: np.ndarray, vids: np.ndarray, alpha=0.05, k=2):
    L, M = robust_laplacian(vs, fs)
    Q = igl.harmonic_weights_integrated_from_laplacian_and_mass(L, M, k)

    a = np.full(len(vs), 0.)  # alpha
    a[vids] = alpha
    a = scipy.sparse.diags(a)
    out_vs = scipy.sparse.linalg.spsolve(a * Q + M - a * M, (M - a * M) @ vs)
    return np.ascontiguousarray(out_vs)


def robust_laplacian(vs, fs, mollify_factor=1e-5) -> Tuple[scipy.sparse.csc_matrix, scipy.sparse.csc_matrix]:
    """
    Get a laplcian with iDT (intrinsic Delaunay triangulation) and intrinsic mollification.
    Ref https://www.cs.cmu.edu/~kmcrane/Projects/NonmanifoldLaplace/NonmanifoldLaplace.pdf
    :param mollify_factor: the mollification factor.
    """
    lin = get_mollified_edge_length(vs, fs, mollify_factor)
    lin, fin = igl.intrinsic_delaunay_triangulation(lin.astype('f8'), fs)
    L = igl.cotmatrix_intrinsic(lin, fin)
    M = igl.massmatrix_intrinsic(lin, fin, igl.MASSMATRIX_TYPE_VORONOI)
    return L, M


def triangulation_refine_leipa(vs: np.ndarray, fs: np.ndarray, fids: np.ndarray, density_factor: float = np.sqrt(2)):
    """
    Refine the triangles using barycentric subdivision and Delaunay triangulation.
    You should remove unreferenced vertices before the refinement.
    See "Filling holes in meshes." [Liepa 2003].

    :return:
        out_vs: (n, 3), the added vertices are appended to the end of the original vertices.
        out_fs: (m, 3), the added faces are appended to the end of the original faces.
        FI: (len(fs), ), face index mapping from the original faces to the refined faces, where
            fs[i] = out_fs[FI[i]], and FI[i]=-1 means the i-th face is deleted.
    """
    out_vs = np.copy(vs)
    out_fs = np.copy(fs)

    if fids is None or len(fids) == 0:
        return out_vs, out_fs, np.arange(len(fs))

    # initialize sigma
    edges = igl.edges(np.delete(out_fs, fids, axis=0))  # calculate the edge length without faces to be refined
    edges = np.concatenate([edges, edges[:, [1, 0]]], axis=0)
    edge_lengths = np.linalg.norm(out_vs[edges[:, 0]] - out_vs[edges[:, 1]], axis=-1)
    edge_length_vids = edges[:, 0]
    v_degrees = np.bincount(edge_length_vids, minlength=len(out_vs))
    v_sigma = np.zeros(len(out_vs))
    v_sigma[v_degrees > 0] = np.bincount(edge_length_vids, weights=edge_lengths,
                                         minlength=len(out_vs))[v_degrees > 0] / v_degrees[v_degrees > 0]
    if np.any(v_sigma == 0):
        v_sigma[v_sigma == 0] = np.median(v_sigma[v_sigma != 0])
        # print("Warning: some vertices have no adjacent faces, the refinement may be incorrect.")

    all_sel_fids = np.copy(fids)
    for _ in range(100):
        # calculate sigma of face centers
        vc_sigma = v_sigma[out_fs].mean(axis=1)  # nf

        # check edge length
        s = density_factor * np.linalg.norm(
            out_vs[out_fs[all_sel_fids]].mean(1, keepdims=True) - out_vs[out_fs[all_sel_fids]], axis=-1)
        cond = np.all(np.logical_and(s > vc_sigma[all_sel_fids, None], s > v_sigma[out_fs[all_sel_fids]]), axis=1)
        sel_fids = all_sel_fids[cond]  # need to subdivide

        if len(sel_fids) == 0:
            break

        # subdivide
        out_vs, added_fs = igl.false_barycentric_subdivision(out_vs, out_fs[sel_fids])

        # update v_sigma after subdivision
        v_sigma = np.concatenate([v_sigma, vc_sigma[sel_fids]], axis=0)
        assert len(v_sigma) == len(out_vs)

        # delete old faces from out_fs and all_sel_fids
        out_fs[sel_fids] = -1
        all_sel_fids = np.setdiff1d(all_sel_fids, sel_fids)

        # add new vertices, faces & update selection
        out_fs = np.concatenate([out_fs, added_fs], axis=0)
        sel_fids = np.arange(len(out_fs) - len(added_fs), len(out_fs))
        all_sel_fids = np.concatenate([all_sel_fids, sel_fids], axis=0)

        # delaunay
        l = get_mollified_edge_length(out_vs, out_fs[all_sel_fids])
        _, add_fs = igl.intrinsic_delaunay_triangulation(l.astype('f8'), out_fs[all_sel_fids])
        out_fs[all_sel_fids] = add_fs

    # update FI, remove deleted faces
    FI = np.arange(len(fs))
    FI[out_fs[:len(fs), 0] < 0] = -1
    idx = np.where(FI >= 0)[0]
    FI[idx] = np.arange(len(idx))
    out_fs = out_fs[out_fs[:, 0] >= 0]
    return out_vs, out_fs, FI


def triangulate_refine_fair(vs, fs, hole_len_thr=1000000, close_hole_fast=True, density_factor=np.sqrt(2),
                            fair_alpha=0.05):
    # fill
    out_fs = close_holes(vs, fs, hole_len_thr, close_hole_fast)
    add_fids = np.arange(len(fs), len(out_fs))

    # refine
    nv = len(vs)
    out_vs, out_fs, FI = triangulation_refine_leipa(vs, out_fs, add_fids, density_factor)
    add_vids = np.arange(nv, len(out_vs))

    # # fairing
    # out_vs = mesh_fair_laplacian_energy(out_vs, out_fs, add_vids, fair_alpha)
    return out_vs, out_fs
