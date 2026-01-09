Here is the `README.md` file tailored for your GitHub repository. It is designed to satisfy **Deliverable #2** of your Statement of Work ("documentation required for a qualified peer to recreate your results") by covering both the code execution and the specific manufacturing steps required to replicate the multicolor print shown in your screenshots.

You can create a file named `README.md` in your repository and paste the content below into it.

---

# Kinetic Valley: 3D Visualization of Nuclear Binding Energy

**Artifact Type:** Deliverable #2 (Code & Documentation)

**Status:** Complete

## 1. Project Overview

This project transforms abstract nuclear physics data into a tangible, 3D-printable object. Using the "Valley of Stability" concept, it visualizes the binding energy of atomic nuclei.

The provided Python software fetches live data from the International Atomic Energy Agency (IAEA), calculates the "instability" height for each isotope, applies Gaussian smoothing for manufacturability, and exports a watertight STL mesh ready for 3D printing.

## 2. Prerequisites

To run the generation script, you need a standard Python 3 environment.

### Dependencies

Create a `requirements.txt` file with the following libraries, or install them manually:

```text
pandas
numpy
scipy
numpy-stl
requests

```

**Installation:**

```bash
pip install -r requirements.txt

```

## 3. Usage Guide

### Step 1: Generate the Mesh

Run the main script to fetch the latest AME2020 data and generate the geometry.

```bash
python generate_valley.py

```

* **Input:** Fetches `mass_1.mas20.txt` from the [IAEA Atomic Mass Data Center](https://www-nds.iaea.org/amdc/).
* **Processing:**
* **X/Y Axis:** Neutron () and Proton () counts.
* **Z Axis (Height):** Calculated as the inverse of Binding Energy per Nucleon. Higher points represent lower stability (higher potential energy).
* **Smoothing:** Applies a Gaussian filter () to create a continuous surface printable by FDM printers.


* **Output:** Creates a file named `kinetic_valley_smoothed.stl` in the working directory.

### Step 2: Slicing & Manufacturing (Bambu Studio)

To recreate the multicolor result shown in the project artifacts, follow these slicing instructions.

**Printer Settings:**

* **Printer:** Bambu Lab X1 Carbon (or similar).
* **Nozzle:** 0.4mm.
* **Layer Height:** 0.20mm Standard.
* **Walls:** 2 loops.
* **Infill:** 15% Gyroid.

**Multicolor Setup (The "Heat Map" Effect):**
The STL contains the geometry, but the "instability heat map" colors are applied in the slicer using Layer Height modifiers.

1. **Import:** Drag `kinetic_valley_smoothed.stl` into Bambu Studio.
2. **Orientation:** Ensure the flat base is on the build plate.
3. **Color Painting:** Use the vertical layer slider (right side of "Preview") to add filament changes at these approximate heights (based on Z=60mm max):
* **0.0mm - 2.0mm:** Black (Base/Grid).
* **2.0mm - 10.0mm:** Blue (Stable/Valley Floor).
* **10.0mm - 35.0mm:** Yellow (Transition Zone).
* **35.0mm+:** Red (Highly Unstable/Drip Line).



*Note: Ensure "Flush Volumes" are auto-calculated to prevent color bleeding between high-contrast transitions (e.g., Black to Yellow).*

## 4. Methodology

The visualization logic follows this transformation pipeline:

1. **Data Ingestion:** Parses raw ASCII data from AME2020.
2. **Topography Calculation:**
* Identifies the "Valley Floor" (most stable  for every ).
* Calculates height based on instability: .
* Adds a parabolic wall factor based on distance from stability to ensure printability of edges.


3. **Mesh Generation:** Uses linear interpolation to grid the data, followed by Gaussian filtering to remove single-pixel noise ("spikes") that causes print failures.

## 5. Project Deliverables Checklist

Per the Statement of Work requirements:

* [x] **Scope of Work:** Submitted previously.
* [x] **GitHub Repo:** This repository contains all source code and instructions.
* [ ] **Presentation:** See `presentation/` folder (if applicable).
* [ ] **Time Log:** See `time_log.csv` for breakdown of Design, Dev, Debug, and Comms hours.

---

**Data Source Citation:**
Wang, M., Huang, W.J., Kondev, F.G., Audi, G., Naimi, S. (2021). The AME 2020 atomic mass evaluation. *Chinese Physics C*, 45(3), 030003.
