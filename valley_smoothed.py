import pandas as pd
import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from stl import mesh
import requests

# --- Constants for Manufacturing ---
MODEL_SIZE_X_MM = 200.0  # Max width on Bambu plate
BASE_THICKNESS_MM = 2.0  # Thickness of the stable "floor"

def fetch_ame2020_data():
    """Fetches and parses AME2020 data (Same as your original logic)."""
    url = "https://www-nds.iaea.org/amdc/ame2020/mass_1.mas20.txt"
    print(f"Fetching AME2020 data...")
    response = requests.get(url, timeout=30)
    lines = response.text.split('\n')
    
    data_start = next(i for i, line in enumerate(lines) if 'N-Z' in line and 'MASS EXCESS' in line) + 2
    
    data = []
    for line in lines[data_start:]:
        if len(line) < 67: continue
        try:
            n, z, be_str = line[4:9], line[9:14], line[54:67]
            if not n.strip() or not z.strip() or '*' in be_str or '#' in be_str: continue
            data.append({
                'N': int(n), 'Z': int(z), 'BE_per_nucleon': float(be_str) / 1000.0
            })
        except: continue
            
    return pd.DataFrame(data)

def calculate_topography(df):
    """
    Calculates 3D coordinates. 
    X = Neutrons, Y = Protons, Z = Instability (Height).
    """
    # 1. Calculate Valley Floor (Optimal Z for each A)
    valley_z = df.groupby('N').apply(lambda x: x.loc[x['BE_per_nucleon'].idxmax(), 'Z'] if not x.empty else 0).to_dict()
    
    heights = []
    for _, row in df.iterrows():
        n, z, be = row['N'], row['Z'], row['BE_per_nucleon']
        
        # Distance from stability valley (Parabolic walls)
        # We approximate the 'valley center' for this N
        center_z = valley_z.get(n, z) 
        dist_from_center = abs(z - center_z)
        
        # Base Instability (Inverse of Binding Energy)
        # Deepest point is ~8.8 MeV. We invert this so deep = low Z.
        max_be = 8.8
        instability = (max_be - be) ** 2  # Square it to exaggerate the well
        
        # Add wall steepness
        total_height = instability + (dist_from_center * 2.0)
        heights.append(total_height)
        
    df['Height'] = heights
    
    # Normalize Z to physical print height (e.g., max 50mm tall)
    z_max_mm = 60.0 
    df['Z_mm'] = (df['Height'] / df['Height'].max()) * z_max_mm
    
    return df

def generate_solid_mesh(df):
    """
    V3: Smoothed Terrain. 
    Increases Gaussian Blur to remove 'spikes' and 'hair' for printing.
    """
    print("⚙ Generating manifold geometry (V3 - Smoothed)...")
    
    # 1. Setup High-Res Grid
    grid_res = 350
    x_grid = np.linspace(df['N'].min(), df['N'].max(), grid_res)
    y_grid = np.linspace(df['Z'].min(), df['Z'].max(), grid_res)
    X, Y = np.meshgrid(x_grid, y_grid)
    

    Z = griddata((df['N'], df['Z']), df['Z_mm'], (X, Y), method='linear')
    
    # Fill NaNs (outside the data hull) with the minimum height so walls slope down cleanly
    Z = np.nan_to_num(Z, nan=np.nanmin(df['Z_mm'])) 
    

    print("   Applying Gaussian Filter (Sigma=3.0)...")
    Z = gaussian_filter(Z, sigma=3.0)
    
    # Lift everything up by base thickness
    Z = Z + BASE_THICKNESS_MM 
    
    # Scale X/Y to printer bed size
    scale_factor = MODEL_SIZE_X_MM / df['N'].max()
    X = X * scale_factor
    Y = Y * scale_factor
    
    rows, cols = Z.shape
    num_points = rows * cols

    print("⚙ Indexing vertices...")

    # 2. Define ALL Vertices (Top Layer + Bottom Layer)
    top_verts = np.column_stack((X.flatten(), Y.flatten(), Z.flatten()))
    bottom_verts = np.column_stack((X.flatten(), Y.flatten(), np.zeros_like(Z.flatten())))
    all_vertices = np.vstack((top_verts, bottom_verts))
    
    # 3. Define Faces (Standard Stitching Logic)
    faces = []
    def get_top_idx(r, c): return r * cols + c
    def get_bot_idx(r, c): return (r * cols + c) + num_points 

    for r in range(rows - 1):
        for c in range(cols - 1):
            t_tl, t_tr = get_top_idx(r, c), get_top_idx(r, c+1)
            t_bl, t_br = get_top_idx(r+1, c), get_top_idx(r+1, c+1)
            b_tl, b_tr = get_bot_idx(r, c), get_bot_idx(r, c+1)
            b_bl, b_br = get_bot_idx(r+1, c), get_bot_idx(r+1, c+1)

            # Top & Bottom
            faces.append([t_tl, t_bl, t_tr])
            faces.append([t_tr, t_bl, t_br])
            faces.append([b_tl, b_tr, b_bl])
            faces.append([b_tr, b_br, b_bl])
            
            # Walls
            if r == 0: faces.extend([[t_tl, t_tr, b_tr], [t_tl, b_tr, b_tl]])
            if r == rows - 2: faces.extend([[t_bl, b_br, t_br], [t_bl, b_bl, b_br]])
            if c == 0: faces.extend([[t_tl, b_bl, t_bl], [t_tl, b_tl, b_bl]])
            if c == cols - 2: faces.extend([[t_tr, t_br, b_br], [t_tr, b_br, b_tr]])

    print("⚙ Creating mesh object...")
    faces = np.array(faces)
    solid_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            solid_mesh.vectors[i][j] = all_vertices[f[j], :]

    filename = 'kinetic_valley_smoothed.stl'
    solid_mesh.save(filename)
    print(f"✓ SMOOTHED STL generated: {filename}")

if __name__ == "__main__":
    df = fetch_ame2020_data()
    df = calculate_topography(df)
    generate_solid_mesh(df)