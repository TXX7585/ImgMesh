"""
-*- coding: utf-8 -*-
@Author: Xuanxin Tian
@Email  : 17710116575@163.com
@Create  : 2022/11/21 19:50
"""
import numpy as np
from ImgMesh.tools import connectivity, tri_angle, tri_angle2, t_norm, py_delaunay
import open3d as o3d

np.seterr(divide='ignore', invalid='ignore')

class Greedy_Crust(object):
    def __init__(self):
        super().__init__()
        self.vertices = None
        # add_Shield parameters
        self.offset = 1
        self.N_shield = 20  # Number of points of the shield edge

        self.ifact_factor = -0.8
        self.alpha_factor = 0.5
        self.alpha_flat = -1

    def perform_reconstruction(self):
        if len(self.vertices.shape) != 2 or self.vertices.shape[1] != 3:
            raise ValueError("Input 3D points must be stored in a 2D array of shape (N, 3).")
        else:
            self.p = self.vertices
            nshield = self.add_Shield()

            # Delaunay 3D triangulation
            self.tetr = py_delaunay(self.p)

            # Get connectivity relationship among tetrahedra
            tetr2t, t2tetr, self.t = connectivity(self.tetr)

            # Get circumcircle of tetrahedra
            cctetr, rtetr = self.CCTetra(self.tetr)

            # Get intersection factor
            self.intersection_factor(tetr2t, cctetr, rtetr)

            self.greedy_walking()

            self.t = self.t[np.all(self.t <= self.p.shape[0] - nshield, axis=1)
                            & self.tkeep, :]

            if self.t.shape[0] > 0:
                self.ManifoldExtraction()

    def add_Shield(self):
        # Find the bounding box
        maxx = np.max(self.p[:, 0])
        maxy = np.max(self.p[:, 1])
        maxz = np.max(self.p[:, 2])
        minx = np.min(self.p[:, 0])
        miny = np.min(self.p[:, 1])
        minz = np.min(self.p[:, 2])

        # Give offset to the bounding box
        stepx = (maxx - minx) * self.offset
        stepy = (maxy - miny) * self.offset
        stepz = (maxz - minz) * self.offset

        maxx += stepx
        maxy += stepy
        maxz += stepz
        minx -= stepx
        miny -= stepy
        minz -= stepz

        N = self.N_shield
        stepx /= N  # Decrease step, avoids not unique points
        stepz /= N

        nshield = N * N * 6

        # Creating a grid lying on the bounding box
        vx = np.linspace(minx, maxx, N)
        vy = np.linspace(miny, maxy, N)
        vz = np.linspace(minz, maxz, N)

        x, y = np.meshgrid(vx, vy)
        x = x.reshape(-1, order='F')
        y = y.reshape(-1, order='F')
        facez1 = np.column_stack((x, y, np.full(N * self.N_shield, maxz)))
        facez2 = np.column_stack((x, y, np.full(N * N, minz)))

        x, y = np.meshgrid(vy, vz - stepz)
        x = x.reshape(-1, order='F')
        y = y.reshape(-1, order='F')
        facex1 = np.column_stack((np.full(N * N, maxx), x, y))
        facex2 = np.column_stack((np.full(N * N, minx), x, y))

        x, y = np.meshgrid(vx - stepx, vz)
        x = x.reshape(-1, order='F')
        y = y.reshape(-1, order='F')
        facey1 = np.column_stack((x, np.full(N * N, maxy), y))
        facey2 = np.column_stack((x, np.full(N * N, miny), y))

        # Add points to the p array
        self.p = np.vstack((self.p, facex1, facex2, facey1, facey2, facez1, facez2))

        return nshield

    def CCTetra(self, tetr):
        # Points of tetrahedra
        p1 = self.p[tetr[:, 0], :]
        p2 = self.p[tetr[:, 1], :]
        p3 = self.p[tetr[:, 2], :]
        p4 = self.p[tetr[:, 3], :]

        # Vectors of tetrahedra edges
        v21 = self.p[tetr[:, 0], :] - self.p[tetr[:, 1], :]
        v31 = self.p[tetr[:, 2], :] - self.p[tetr[:, 0], :]
        v41 = self.p[tetr[:, 3], :] - self.p[tetr[:, 0], :]

        # Preallocation
        cc = np.zeros((tetr.shape[0], 3))

        # Solve the system using Cramer's method
        d1 = np.sum(v41 * (p1 + p4) * 0.5, axis=1)
        d2 = np.sum(v21 * (p1 + p2) * 0.5, axis=1)
        d3 = np.sum(v31 * (p1 + p3) * 0.5, axis=1)

        det23 = (v21[:, 1] * v31[:, 2]) - (v21[:, 2] * v31[:, 1])
        det13 = (v21[:, 2] * v31[:, 0]) - (v21[:, 0] * v31[:, 2])
        det12 = (v21[:, 0] * v31[:, 1]) - (v21[:, 1] * v31[:, 0])

        Det = v41[:, 0] * det23 + v41[:, 1] * det13 + v41[:, 2] * det12

        detx = d1 * det23 + \
               v41[:, 1] * (-(d2 * v31[:, 2]) + (v21[:, 2] * d3)) + \
               v41[:, 2] * ((d2 * v31[:, 1]) - (v21[:, 1] * d3))

        dety = v41[:, 0] * ((d2 * v31[:, 2]) - (v21[:, 2] * d3)) + \
               d1 * det13 + v41[:, 2] * ((d3 * v21[:, 0]) - (v31[:, 0] * d2))

        detz = v41[:, 0] * ((v21[:, 1] * d3) - (d2 * v31[:, 1])) + \
               v41[:, 1] * (d2 * v31[:, 0] - v21[:, 0] * d3) + \
               d1 * det12

        # Circumcenters
        cc[:, 0] = detx / Det
        cc[:, 1] = dety / Det
        cc[:, 2] = detz / Det

        # Circumradius
        r = np.sqrt(np.sum((p2 - cc) ** 2, axis=1))  # squared radius

        return cc, r

    def intersection_factor(self, tetr2t, cc, r):
        nt = tetr2t.shape[0]
        self.Ifact = np.zeros((nt, 1), dtype=float)  # Intersection factor

        i = tetr2t[:, 1] > 0
        distcc = np.sum((cc[tetr2t[i, 0], :] - cc[tetr2t[i, 1], :]) ** 2, axis=1)  # Distance between circumcenters

        self.Ifact[i, 0] = (-distcc + r[tetr2t[i, 0]] ** 2 + r[tetr2t[i, 1]] ** 2) / (
                2 * r[tetr2t[i, 0]] * r[tetr2t[i, 1]])
        self.Ifact[np.isnan(self.Ifact)] = 0

    def bound_triangles(self, tetr2t, deleted):
        # Extracts boundary triangles from a set of tetr2t connectivity
        # and the deleted vector which marks tetrahedra that are marked as out.
        nt = tetr2t.shape[0]  # Number of total triangles

        tbound = np.ones((nt, 2), dtype=bool)  # Initialize to keep shape for the next operation

        ind = tetr2t > 0  # Avoid null index
        tbound[ind] = deleted[tetr2t[ind]]  # Mark 1 for deleted, 0 for kept tetrahedra

        tbound = np.sum(tbound, axis=1) == 1  # Boundary triangles only have one tetrahedron

        return tbound

    def search_point(self, p1, p2, p3):
        v21 = p1 - p2
        v31 = p3 - p1

        n1 = np.cross(v21, v31)  # Normal to the triangle
        v31 = n1
        cosdir = np.cross(v21, v31)  # Direction cosines of the line
        cosdir /= np.linalg.norm(cosdir)

        pm = (p1 + p2) * 0.5
        lenge = np.linalg.norm(p1 - p2)
        sp = pm + cosdir * (lenge * 0.866)  # Search point
        sr = lenge  # Search radius

        return sp, sr

    def ManifoldExtraction(self):
        numt = self.t.shape[0]
        vect = np.arange(numt)
        e = np.vstack((self.t[:, [0, 1]], self.t[:, [1, 2]], self.t[:, [2, 0]]))
        e = np.sort(e, axis=1)
        e, _, j = np.unique(e, axis=0, return_index=True, return_inverse=True)

        te = np.column_stack((j[vect], j[vect + numt], j[vect + 2 * numt]))
        nume = e.shape[0]
        e2t = np.full((nume, 2), -1, dtype=np.int32)

        ne = e.shape[0]
        npoints = self.p.shape[0]

        count = np.zeros(ne, dtype=np.int32)
        etmapc = np.full((ne, 10), -1, dtype=np.int32)

        for i in range(numt):
            i1, i2, i3 = te[i, :]

            etmapc[i1, count[i1]] = i
            etmapc[i2, count[i2]] = i
            etmapc[i3, count[i3]] = i

            count[i1] += 1
            count[i2] += 1
            count[i3] += 1

        etmap = [[] for _ in range(nume)]
        for i in range(nume):
            etmap[i] = etmapc[i, :count[i]]

        tkeep = np.zeros(numt, dtype=bool)  # All triangles initially not selected

        efront = np.full(nume, -1, dtype=np.int32)
        tnorm = t_norm(self.p, self.t)

        # Find the highest triangle
        z_avg_per_triangle = (self.p[self.t[:, 0], 2] + self.p[self.t[:, 1], 2] + self.p[self.t[:, 2], 2]) / 3

        # Find the maximum value and its corresponding index
        # foo = np.max(z_avg_per_triangle)
        t1 = np.argmax(z_avg_per_triangle)

        if tnorm[t1, 2] < 0:
            tnorm[t1, :] = -tnorm[t1, :]

        tkeep[t1] = True
        efront[:3] = te[t1, :3]
        e2t[te[t1, :3], 0] = t1
        nf = 2

        while nf > 0:
            k = efront[nf]

            if e2t[k, 1] > -1 or e2t[k, 0] < 0 or count[k] < 2:
                nf -= 1
                continue

            idtcandidate = etmap[k]

            t1 = e2t[k, 0]
            alphamin = np.inf
            ttemp = self.t[t1, :]
            etemp = e[k, :]
            p1, p2 = etemp[0], etemp[1]
            p3 = ttemp[np.logical_and(ttemp != p1, ttemp != p2)]  # ID of the third point

            for i in range(len(idtcandidate)):
                t2 = idtcandidate[i]
                if t2 == t1:
                    continue

                ttemp = self.t[t2, :]
                p4 = ttemp[np.logical_and(ttemp != p1, ttemp != p2)]

                alpha, tnorm2 = tri_angle2(self.p[p1, :], self.p[p2, :], self.p[p3, :], self.p[p4, :], tnorm[t1, :])

                if alpha < alphamin:
                    alphamin = alpha
                    idt = t2
                    tnorm[t2, :] = tnorm2

            # Update the front according to the selected triangle
            tkeep[idt] = True
            for j in range(3):
                ide = te[idt, j]
                if e2t[ide, 0] < 0:
                    efront[nf] = ide
                    nf += 1
                    e2t[ide, 0] = idt
                else:
                    efront[nf] = ide
                    nf += 1
                    e2t[ide, 1] = idt

            nf -= 1

        self.t = self.t[tkeep, :]

    def greedy_walking(self):
        numt = self.t.shape[0]
        vect = np.arange(numt)  # Triangle indices
        e = np.vstack((self.t[:, [0, 1]], self.t[:, [1, 2]], self.t[:, [2, 0]]))  # Edges - not unique
        e, _, j = np.unique(np.sort(e, axis=1), axis=0, return_index=True, return_inverse=True)  # Unique edges
        te = np.column_stack((j[vect], j[vect + numt], j[vect + 2 * numt]))
        nume = e.shape[0]
        e2t = np.full((nume, 2), -1, dtype=np.int32)

        count = np.zeros(nume, dtype='int32')  # Number of candidate triangles per edge
        etmapc = np.full((nume, 4), -1, dtype=np.int32)

        for i in range(numt):
            i1, i2, i3 = te[i, :]
            max_i = max(count[i1], count[i2], count[i3])
            if max_i > etmapc.shape[1] - 1:
                new_columns = np.full((etmapc.shape[0], max_i - etmapc.shape[1] + 1), -1, dtype='int32')
                etmapc = np.hstack((etmapc, new_columns))

            etmapc[i1, count[i1]] = i
            etmapc[i2, count[i2]] = i
            etmapc[i3, count[i3]] = i
            count[i1] += 1
            count[i2] += 1
            count[i3] += 1

        etmap = [etmapc[i, :count[i]] for i in range(nume)]

        self.tkeep = np.zeros(numt, dtype=bool)  # At the beginning, no triangle is selected
        pchecked = np.zeros(self.p.shape[0], dtype=bool)

        efront = np.full(nume * 2, -1, dtype='int32')  # Estimated length of the queue
        iterf = 0  # Edge queue iterator
        nf = -1  # Number of edges on the front

        index = np.argsort(self.Ifact, axis=0)

        for i in range(numt):
            t1 = index[i]
            if self.Ifact[t1] > self.ifact_factor:
                break
            if not np.any(pchecked[self.t[t1, :]]) and self.Ifact[t1] < self.ifact_factor:
                self.tkeep[t1] = True
                pchecked[self.t[t1, :]] = True
                efront[nf + 1:nf + 4] = te[t1, :3]
                e2t[te[t1, :3], 0] = t1
                nf += 3

        if nf == 0:
            raise ValueError('Front does not start. Please send a report to the author.')

        while iterf <= nf:
            k = efront[iterf]  # Edge ID on the front

            if e2t[k, 1] > -1 or e2t[k, 0] < 0 or count[k] < 2:
                iterf += 1
                continue

            idtcandidate = etmap[k]
            idtcandidate = [i for i in idtcandidate if i != e2t[k, 0]]  # Remove the triangle we came from

            if not idtcandidate:
                iterf += 1
                continue

            ttemp = self.t[e2t[k, 0], :]
            etemp = e[k, :]
            pt = ttemp[
                np.logical_and(ttemp != etemp[0], ttemp != etemp[1])]  # Opposite point to the edge we are studying
            sp, sr = self.search_point(self.p[e[k, 0], :], self.p[e[k, 1], :], self.p[pt, :])

            dist = np.zeros(len(idtcandidate))
            for c in range(len(idtcandidate)):
                idt = idtcandidate[c]
                idp = self.t[idt, np.logical_and(self.t[idt, :] != etemp[0], self.t[idt, :] != etemp[1])]
                dist[c] = np.sum((sp - self.p[idp, :]) ** 2)

            ind = dist > sr ** 2
            idtcandidate = [idtcandidate[i] for i in range(len(idtcandidate)) if not ind[i]]
            if not idtcandidate:
                iterf += 1
                continue
            else:
                dist = [dist[i] for i in range(len(dist)) if not ind[i]]

            id = np.argsort(self.Ifact[idtcandidate], axis=0)
            idtcandidate = np.array(idtcandidate)[id]

            alpha_list = np.zeros(len(idtcandidate))
            keep = np.zeros(len(idtcandidate), dtype=bool)
            Flat = False

            for c in range(len(idtcandidate)):
                idt = idtcandidate[c]
                conformity = True

                for ii in range(3):
                    e1 = te[idt, ii]

                    if e2t[e1, 1] > -1 and e1 != k:
                        conformity = False
                        break
                    elif e2t[e1, 0] > -1:
                        t1 = e2t[e1, 0]
                        t2 = idt
                        ttemp = self.t[t1, :][0]
                        etemp = e[e1, :][0]
                        pt1 = ttemp[(ttemp != etemp[0]) & (ttemp != etemp[1])]  # terzo id punto
                        ttemp = self.t[t2, :][0]
                        pt2 = ttemp[(ttemp != etemp[0]) & (ttemp != etemp[1])]  # terzo id punto

                        alpha = tri_angle(self.p[e[e1, 0], :][0], self.p[e[e1, 1], :][0], self.p[pt1[0], :],
                                          self.p[pt2[0], :])

                        if alpha > self.alpha_factor:
                            conformity = False
                            break

                        if e1 == k:
                            alpha_list[c] = alpha

                if conformity:
                    if self.alpha_flat <= -1:
                        keep[c] = True
                        break
                    else:
                        if alpha_list[c] < self.alpha_flat:
                            Flat = True
                            break
                        else:
                            keep[c] = True

            if Flat:
                idt = idtcandidate[c]
                self.tkeep[idt] = True
                e2t[k, 1] = idt
                for j in range(3):
                    ide = te[idt, j]
                    if e2t[ide, 0] < 0:
                        efront[nf + 1] = ide
                        nf += 1
                        e2t[ide, 0] = idt
                    else:
                        efront[nf + 1] = ide
                        nf += 1
                        e2t[ide, 1] = idt
            elif np.any(keep):
                idt = idtcandidate[keep][0][0]
                self.tkeep[idt] = True
                e2t[k, 1] = idt
                for j in range(3):
                    ide = te[idt, j]
                    if e2t[ide, 0] < 0:
                        efront[nf + 1] = ide
                        nf += 1
                        e2t[ide, 0] = idt
                    else:
                        efront[nf + 1] = ide
                        nf += 1
                        e2t[ide, 1] = idt
            iterf += 1


class O3d_Reconstruction(object):
    def __init__(self):
        super().__init__()
        self.vertices = None
        self.method = 'Alpha shapes'
        self.para = 0.5
        self.knn = 30

    def perform_reconstruction(self):
        if self.vertices is not None:
            self.pcd = o3d.geometry.PointCloud()
            self.pcd.points = o3d.utility.Vector3dVector(self.vertices)
            self.pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamKNN(knn=self.knn))
            if self.method == 'Alpha shapes':
                mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(self.pcd, alpha=self.para)
            elif self.method == 'Poisson':
                mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(self.pcd, depth=self.para)
            else:
                mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
                    self.pcd, o3d.utility.DoubleVector(self.para))
            self.t = np.asarray(mesh.triangles)
            self.v = np.asarray(mesh.vertices)
