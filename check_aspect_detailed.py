import matplotlib.pyplot as plt
import numpy as np

fig, axs = plt.subplots(2, 2, figsize=(6, 4))
for ax in axs.flat:
    pcm = ax.pcolormesh(np.random.rand(10, 10))

# Create colorbar with shrink=0.6
cbar = fig.colorbar(pcm, ax=axs, location='right', shrink=0.6)
cax = cbar.ax

print("_colorbar_info contents:")
if hasattr(cax, '_colorbar_info'):
    for key, val in cax._colorbar_info.items():
        print(f"  {key}: {val}")

print("\nColorbar axes box_aspect:", cax.get_box_aspect())

# Do a layout to position everything
fig.canvas.draw()

# Now check actual dimensions
pos = cax.get_position()
print(f"\nColorbar position (figure coords):")
print(f"  x0={pos.x0:.4f}, y0={pos.y0:.4f}, x1={pos.x1:.4f}, y1={pos.y1:.4f}")
print(f"  width={pos.width:.4f}, height={pos.height:.4f}")
print(f"  aspect (h/w) = {pos.height/pos.width:.2f}")

# Convert to inches
fig_w, fig_h = fig.get_size_inches()
w_in = pos.width * fig_w
h_in = pos.height * fig_h
print(f"\nColorbar dimensions in inches:")
print(f"  width={w_in:.3f}\", height={h_in:.3f}\"")
print(f"  aspect (h/w) = {h_in/w_in:.2f}")
