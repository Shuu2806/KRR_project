import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import random

sys.path.insert(0, str(Path.cwd()))
from benchmark.constructive_generator import generate

def main():
    random.seed(42) # Ensure we get a consistent puzzle instance
    try:
        cube_list, symbol_dict, wall_list, region_map = generate(13, 4, 3, 1, 2, max_attempts=5000)
    except RuntimeError as e:
        print("Failed to generate instance:", e)
        return

    n = 4
    fig = plt.figure(figsize=(15, 5))
    
    color_map = {1: 'crimson', 2: 'gold', 3: 'royalblue'}
    titles = {1: 'Région 1 (Rouge)', 2: 'Région 2 (Jaune)', 3: 'Région 3 (Bleu)'}
    
    # Define bounds for the 3D grid so that all subplots have the same scale
    for r_id in range(1, 4):
        ax = fig.add_subplot(1, 3, r_id, projection='3d')
        ax.set_box_aspect([1, 1, 1])
        
        # Set same limits for all so they align visually
        ax.set_xlim([0, n+2])
        ax.set_ylim([0, n+2])
        ax.set_zlim([0, n+2])

        voxels = np.zeros((n+2, n+2, n+2), dtype=bool)
        colors = np.empty((n+2, n+2, n+2), dtype=object)
        
        for (x, y, z) in cube_list:
            if region_map[(x, y, z)] == r_id:
                voxels[x, y, z] = True
                colors[x, y, z] = color_map[r_id]
                
        ax.voxels(voxels, facecolors=colors, edgecolor='k', alpha=0.9)
        
        for (x, y, z), sym in symbol_dict.items():
            if region_map[(x, y, z)] == r_id:
                ax.text(x + 0.5, y + 0.5, z + 1.1, f"Sym {sym}", color='black', fontsize=10, ha='center', weight='bold')

        ax.set_title(titles[r_id], fontsize=14, weight='bold')
    
    plt.suptitle("3DSRP Instance: Régions séparées (c=13, m=3, w=2, k=1)", fontsize=16, weight='bold')
    
    out_path = Path('instance_3dsrp_decoupe.png')
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    print("SAVED:", out_path.absolute())

if __name__ == "__main__":
    main()
