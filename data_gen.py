import pandas as pd
import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
import requests
import json

# --- 1. Fetch Data (Your existing logic) ---
def fetch_ame2020_data():
    print("📡 Fetching AME2020 data...")
    url = "https://www-nds.iaea.org/amdc/ame2020/mass_1.mas20.txt"
    response = requests.get(url, timeout=30)
    lines = response.text.split('\n')
    data_start = next(i for i, line in enumerate(lines) if 'N-Z' in line and 'MASS EXCESS' in line) + 2
    data = []
    for line in lines[data_start:]:
        if len(line) < 67: continue
        try:
            n, z = int(line[4:9]), int(line[9:14])
            be_str = line[54:67]
            if '*' in be_str or '#' in be_str: continue
            data.append({'N': n, 'Z': z, 'BE': float(be_str) / 1000.0})
        except: continue
    return pd.DataFrame(data)

# --- 2. Calculate Topography (Your existing logic) ---
def calculate_topography(df):
    valley_z = df.groupby('N').apply(lambda x: x.loc[x['BE'].idxmax(), 'Z'] if not x.empty else 0).to_dict()
    heights = []
    for _, row in df.iterrows():
        center_z = valley_z.get(row['N'], row['Z'])
        instability = (8.8 - row['BE']) ** 2
        dist = abs(row['Z'] - center_z)
        heights.append(instability + (dist * 2.0))
    df['Height'] = heights
    # Normalize to same scale as print
    df['Z_mm'] = (df['Height'] / df['Height'].max()) * 60.0 
    return df

# --- 3. Export for Web ---
def export_json(df):
    print("⚙ Processing Grid for Web...")
    grid_res = 150 # Lower res for web performance, still looks good
    x_grid = np.linspace(df['N'].min(), df['N'].max(), grid_res)
    y_grid = np.linspace(df['Z'].min(), df['Z'].max(), grid_res)
    X, Y = np.meshgrid(x_grid, y_grid)
    
    # Linear interp + Gaussian Smooth (Same as your print)
    Z = griddata((df['N'], df['Z']), df['Z_mm'], (X, Y), method='linear')
    Z = np.nan_to_num(Z, nan=np.nanmin(df['Z_mm']))
    Z = gaussian_filter(Z, sigma=2.0) # Slightly lower sigma for lower grid res

    # Element Lookup (Z -> Symbol)
    elements = {
        1:"H", 2:"He", 6:"C", 8:"O", 26:"Fe", 82:"Pb", 92:"U"
        # (Add full periodic table here if desired, keeping it minimal for demo)
    }

    output = {
        "grid_width": grid_res,
        "grid_depth": grid_res,
        "min_n": float(df['N'].min()),
        "max_n": float(df['N'].max()),
        "min_z": float(df['Z'].min()),
        "max_z": float(df['Z'].max()),
        "heights": Z.flatten().tolist(), # Flatten 2D array to 1D list
        "max_height_mm": 60.0
    }
    
    with open("valley_data.json", "w") as f:
        json.dump(output, f)
    print("✅ Saved valley_data.json")

if __name__ == "__main__":
    df = fetch_ame2020_data()
    df = calculate_topography(df)
    export_json(df)