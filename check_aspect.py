import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots()
dx, dy = 0.6, 0.6
y, x = np.mgrid[slice(-3, 3 + dy, dy), slice(-3, 3 + dx, dx)]
z = (1 - x / 2. + x**5 + y**3) * np.exp(-x**2 - y**2)
pcm = ax.pcolormesh(x, y, z[:-1, :-1], cmap='RdBu_r', vmin=-1., vmax=1.)

cbar = fig.colorbar(pcm, ax=ax, shrink=0.6)
cax = cbar.ax
if hasattr(cax, '_colorbar_info'):
    info = cax._colorbar_info
    print('aspect:', info.get('aspect'))
    print('shrink:', info.get('shrink'))
    print('fraction:', info.get('fraction'))
    print('pad:', info.get('pad'))
