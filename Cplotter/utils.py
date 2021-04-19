import numpy as np

def get_ind(l, x, y):
    xy = l.get_xydata().tolist()
    return xy.index([x, y])


def delete_points(index, lines, collections):
    lineset = list(set(lines))
    indexset = [[] for _ in lineset]
    collectionset = [None for _ in lineset]
    for i in range(len(lines)):
        for j in range(len(lineset)):
            if lines[i] == lineset[j]:
                indexset[j].append(index[i])
                collectionset[j] = collections[i]
                break
    dataset = []
    for indices, line, collec in zip(indexset, lineset, collectionset):
        xdata = np.delete(line.get_xdata(), indices)
        ydata = np.delete(line.get_ydata(), indices)
        line.set_data([xdata, ydata])
        err = []
        for i, c in enumerate(collec):
            if c is not None:
                vert = np.delete([path.vertices for path in c.get_paths()], indices, 0)
                c.set_verts(vert)
                err.append(np.array([(v[1, 1 - i] - v[0, 1 - i]) / 2. for v in vert]))
            else:
                err.append([])
        dataset.append([xdata, ydata] + err)
    return lineset, dataset


def add_points(index, x, y, verty, vertx, lines, collections):
    lineset = list(set(lines))
    indexset = [[] for _ in lineset]
    xset = [[] for _ in lineset]
    yset = [[] for _ in lineset]
    vertyset = [[] for _ in lineset]
    vertxset = [[] for _ in lineset]
    collectionset = [None for _ in lineset]
    for i in range(len(lines)):
        for j in range(len(lineset)):
            if lines[i] == lineset[j]:
                indexset[j].append(index[i])
                xset[j].append(x[i])
                yset[j].append(y[i])
                vertyset[j].append(verty[i])
                vertxset[j].append(vertx[i])
                collectionset[j] = collections[i]
                break
    dataset = []
    for indices, X, Y, VY, VX, line, collec in zip(indexset, xset, yset, vertyset, vertxset, lineset, collectionset):
        xdata = line.get_xdata()
        ydata = line.get_ydata()
        if collec[0] is not None: verty = [path.vertices for path in collec[0].get_paths()]
        if collec[1] is not None: vertx = [path.vertices for path in collec[1].get_paths()]
        for i, x, y, vy, vx in zip(indices, X, Y, VY, VX):
            xdata = np.insert(xdata, i, x)
            ydata = np.insert(ydata, i, y)
            if collec[0] is not None: verty.insert(i, vy)
            if collec[1] is not None: vertx.insert(i, vx)
        line.set_data([xdata, ydata])
        if collec[0] is not None: collec[0].set_verts(verty)
        if collec[1] is not None: collec[1].set_verts(vertx)
        erry = np.array([(v[1, 1 - i] - v[0, 1 - i]) / 2. for v in verty]) if collec[0] is not None else []
        errx = np.array([(v[1, 1 - i] - v[0, 1 - i]) / 2. for v in vertx]) if collec[1] is not None else []
        dataset.append([xdata, ydata, erry, errx])
    return lineset, dataset
