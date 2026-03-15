import matplotlib.pyplot as plt
import numpy as np

fig, axs = plt.subplots(1, 2, figsize=(8, 4), layout='constrained')

# Left plot: shrink=1.0 (default)
pcm1 = axs[0].pcolormesh(np.random.rand(10, 10))
cbar1 = fig.colorbar(pcm1, ax=axs[0], location='right', shrink=1.0)
axs[0].set_title('shrink=1.0')

# Right plot: shrink=0.6
pcm2 = axs[1].pcolormesh(np.random.rand(10, 10))
cbar2 = fig.colorbar(pcm2, ax=axs[1], location='right', shrink=0.6)
axs[1].set_title('shrink=0.6')

# Get the positions and print dimensions
pos1 = cbar1.ax.get_position()
pos2 = cbar2.ax.get_position()

print('shrink=1.0: width={:.4f}, height={:.4f}, aspect={:.2f}'.format(
    pos1.width, pos1.height, pos1.height/pos1.width if pos1.width > 0 else 0))
print('shrink=0.6: width={:.4f}, height={:.4f}, aspect={:.2f}'.format(
    pos2.width, pos2.height, pos2.height/pos2.width if pos2.width > 0 else 0))

plt.savefig('/Users/jklymak/Dropbox/mpl-direct-layout/test_shrink.png', dpi=100)
print('Saved to test_shrink.png')
