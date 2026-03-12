# 🔬 Automated ODMR Image Analyzer
**Author:** Minhao Liu - PhD Researcher

An automated, statistically rigorous image processing pipeline designed to extract Optically Detected Magnetic Resonance (ODMR) signals from time-lapse fluorescence microscopy sequences of Fluorescent Nanodiamonds (FNDs).

---

## 📖 The Problem: Why not use ImageJ / "Max Pixel"?
Traditional manual image analysis (such as finding the single highest pixel value in ImageJ) is fundamentally incompatible with the precision required for quantum sensing. 
* **Extreme Value Vulnerability:** The single maximum pixel is often an artifact of camera shot noise, read noise, or hardware clipping (e.g., sensor saturation). 
* **Spatial Bias:** Drawing manual ROI boxes leads to inconsistent background integration, artificially altering the calculated mean brightness.
* **Thermal Drift:** Without automated target tracking, slight mechanical or thermal drifts in the microscope stage will cause the FNDs to move or blur, destroying the $1/f$ baseline over time.

## 🚀 The Solution: This Automated Pipeline
This application mathematically eliminates human bias and camera artifacts through three key physical principles:

### 1. Spatial Coordinate Locking
To ensure true differential measurements, the software uses the very first microwave "OFF" frame as an unperturbed baseline. 
* It calculates the $(X, Y)$ coordinates of every glowing nanodiamond.
* It calculates the exact shape of the background (non-glowing) mask.
* **The Lock:** It permanently locks these coordinates and applies them identically to every subsequent "ON" and "OFF" frame. This guarantees that frame 30 is measured at the exact same physical location as frame 1, regardless of optical blurring.

### 2. Dynamic Background Subtraction
Even with locked coordinates, laser power can drift during a 100-second experiment. To fix this, the software calculates a *brand new* background average for every single frame using the locked background mask. It subtracts this localized noise floor from the locked FND coordinates, perfectly flattening laser drift.

### 3. Dual Integration Modes
The app provides two statistically robust methods to extract the quantum signal:
* **Whole-ROI Average (Recommended):** Uses a threshold to mask the exact shape of the glowing dot. It averages all pixels within that specific shape, maximizing the Signal-to-Noise Ratio (SNR) by ignoring dark pixels.
* **Multi-Peak Local Maximum:** A rigorous upgrade to the "Max Pixel" method. It scans the baseline image to find all distinct local maxima. It then draws a customizable $N \times N$ micro-box around each peak, averaging the local neighborhood to suppress single-pixel digital artifacts while maintaining a peak-centric measurement.

---

## 🛠️ How to Use the App

### 1. Uploading Data
1. Export your time-lapse frames as raw, lossless `.tif` or `.tiff` files. Do not use `.jpg` or `.png`.
2. Separate your frames into two folders: one for Microwave ON states, and one for Microwave OFF states.
3. Drag and drop the files into their respective columns in the web interface.

### 2. Tuning the Mask
Use the sidebar sliders to ensure the software is correctly tracking your FNDs:
* **Gaussian Smoothing (Sigma):** Slightly blurs the image *only* for the mask-drawing step. This prevents a single noisy camera pixel from being mistaken for a nanodiamond.
* **Threshold Multiplier:** Adjusts how tightly the mask hugs the bright dots. 
* **Minimum Peak Brightness (%):** (Multi-Peak Mode Only) Filters out dim background noise. Set this so the software only tracks distinct, bright FND clusters.

### 3. Verifying and Exporting
* Check the **ROI Mask Preview** pane. The software will display the baseline image with the active mask overlaid in yellow (or tracked peaks marked in red). Verify it is tracking the correct targets.
* Review the **Results Dashboard** to see the Welch's T-Test $p$-value and the generated boxplot.
* Click **Download Comprehensive Analysis Table** to export a publication-ready `.csv` containing the statistical summary, variances, and raw padded data.

---

## 💻 Local Installation & Development

This app is built using `streamlit`, `numpy`, `scipy`, `skimage`, and `matplotlib`. 

To run this application locally on your machine instead of the cloud:

1. Clone this repository:
   ```bash
   git clone [https://github.com/YourUsername/ODMR-Automated-Analyzer.git](https://github.com/YourUsername/ODMR-Automated-Analyzer.git)
   cd ODMR-Automated-Analyzer
   ```
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the Streamlit dashboard:
   ```bash
   streamlit run app.py
   ```

