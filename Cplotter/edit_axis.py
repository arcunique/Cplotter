from matplotlib import colors
import numpy as np
from Cplotter.shared.nearest_algo import find_nearest_point_or_line


class EditAxis(object):

    def __init__(self, ax):
        self.ax = ax
        self.lines = ax.lines
        self.collections = [[None, None] for _ in self.lines]
        for i, l in enumerate(self.lines):
            if ax.collections != []:
                for c in ax.collections:
                    xy = list(map(list, [path.vertices.mean(0) for path in c.get_paths()]))
                    ind = list(c.get_paths()[0].vertices[1, :] - c.get_paths()[0].vertices[0, :]).index(0)
                    if np.round(l.get_xydata(), 4).tolist() == np.round(xy, 4).tolist() and colors.to_hex(
                            l.get_c()) == colors.to_hex(c.get_color()[0]): self.collections[i][ind] = c
                    if self.collections[i][0] is not None and self.collections[i][1] is not None: break

    def get_err(self):
        err = []
        for collec in self.collections:
            e = []
            for i, c in enumerate(collec):
                if c is not None and c.get_paths() != []:
                    vert = [path.vertices for path in c.get_paths()]
                    e.append(np.array([(v[1, 1 - i] - v[0, 1 - i]) / 2. for v in vert]))
                else:
                    e.append([])
            err.append(e)
        return err

    def get_nearest_PointnLine(self, x, y, distfrom='point'):
        return find_nearest_point_or_line(self.lines, self.get_err(), self.ax.get_xlim(), self.ax.get_ylim(), x, y,
                                          distfrom)
