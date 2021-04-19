from Cplotter import *
import matplotlib
matplotlib.use('Qt5Agg')

fig, ax = plt.subplots()
ax.plot([1,4,9,16,25], marker='o')
iplot()