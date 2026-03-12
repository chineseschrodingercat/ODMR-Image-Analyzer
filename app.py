# =====================================================================
# Project: Automated ODMR Fluorescence Image Analyzer
# Author: Minhao Liu - PhD Researcher
# Description: Automated ROI integration, local background subtraction, 
#              and statistical analysis for fluorescent nanodiamond (FND) 
#              microwave excitation data.
# =====================================================================

import streamlit as st
import numpy as np
import pandas as pd
from analyzer import establish_baseline, extract_brightness, apply_denoising, calculate_statistics
from plotter import draw_preview_pane, draw_boxplot

st.set_page_config(page_title="ODMR Image Analyzer", layout="wide")

st.title("🔬 Automated ODMR Image Analyzer")
st.markdown("**Author:** Minhao Liu")
st.markdown("Analyze fluorescent nanodiamond (FND) image sequences to detect statistically significant ODMR contrast.")
st.divider()

# --- INTERACTIVE TUNING KNOBS ---
st.sidebar.header("⚙️ Analysis Mode")
analysis_mode = st.sidebar.radio(
    "Select Integration Method:",
    ["Whole-ROI Average (Recommended)", "Multi-Peak Local Maximum"]
)

st.sidebar.header("⚙️ Mask Tuning Parameters")
gaussian_sigma = st.sidebar.slider("Gaussian Smoothing (Sigma)", 0.5, 5.0, 2.0, 0.1)
threshold_multiplier = st.sidebar.slider("Threshold Multiplier", 0.5, 2.0, 1.0, 0.05)

if analysis_mode == "Multi-Peak Local Maximum":
    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Multi-Peak Settings")
    neighborhood_size = st.sidebar.slider(
        "Integration Area around each peak (px)", 
        min_value=1, max_value=21, value=3, step=2,
        help="1 = Raw single-pixel max. Higher values average an NxN box around each peak."
    )
    peak_threshold_percent = st.sidebar.slider(
        "Minimum Peak Brightness (%)", 
        min_value=1, max_value=100, value=20, step=1,
        help="Filters out dim noise. 20% means a peak must be at least 20% as bright as the brightest dot."
    )
else:
    neighborhood_size = None
    peak_threshold_percent = None

st.sidebar.markdown("---")
st.sidebar.header("🛠️ Signal Denoising")
denoise_mode = st.sidebar.selectbox(
    "Select Drift Correction Procedure:",
    ["None (Raw Data)", "Polynomial Detrending (Slow Drift)", "Software Lock-In (Fast Cycle Filter)"],
    help="Algorithms to mathematically flatten thermal drift and laser fluctuations."
)

# --- UI: FILE UPLOADERS ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📡 Microwave ON Frames")
    on_files = st.file_uploader("Upload 'ON' .tif files", type=['tif', 'tiff'], accept_multiple_files=True, key="on")
with col2:
    st.subheader("🔇 Microwave OFF Frames")
    off_files = st.file_uploader("Upload 'OFF' .tif files", type=['tif', 'tiff'], accept_multiple_files=True, key="off")

# --- EXECUTION BLOCK ---
if on_files and off_files:
    if len(on_files) < 3 or len(off_files) < 3:
        st.warning("Please upload at least 3 images per condition to run statistical analysis.")
    else:
        with st.spinner("Establishing baseline and processing images..."):
            
            # 1. ESTABLISH BASELINE
            baseline_img, red_mask, bg_mask, peaks_xy = establish_baseline(
                off_files[0], gaussian_sigma, threshold_multiplier, analysis_mode, peak_threshold_percent
            )

            # 2. EXTRACT RAW DATA USING LOCKED COORDINATES
            raw_on_data = extract_brightness(on_files, red_mask, bg_mask, analysis_mode, peaks_xy, neighborhood_size)
            raw_off_data = extract_brightness(off_files, red_mask, bg_mask, analysis_mode, peaks_xy, neighborhood_size)
            
            # 3. APPLY ALGORITHMIC DENOISING
            on_data, off_data = apply_denoising(raw_on_data, raw_off_data, denoise_mode)
            
            # 4. CALCULATE STATISTICS
            is_paired_test = True if denoise_mode == "Software Lock-In (Fast Cycle Filter)" else False
            metrics = calculate_statistics(on_data, off_data, is_paired=is_paired_test)
            
            st.success("Analysis Complete!")
            st.divider()
            
            # --- MASK PREVIEW PANE ---
            st.subheader("👁️ ROI Mask Preview (Baseline: OFF Frame 1)")
            st.markdown("Coordinates and background masks are locked to this unperturbed baseline image to ensure spatial consistency across all frames.")
            
            fig_preview = draw_preview_pane(baseline_img, red_mask, peaks_xy, analysis_mode)
            st.pyplot(fig_preview)
            
            # --- RESULTS DASHBOARD ---
            st.header("📊 Results")
            st.markdown(f"**Sample Sizes:** Microwave ON ($N={metrics['n_on']}$) | Microwave OFF ($N={metrics['n_off']}$)")
            if denoise_mode != "None (Raw Data)":
                st.info(f"**Active Filter:** {denoise_mode} applied. Data variance has been optimized to remove background drift.")
            
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("Mean ON Brightness", f"{metrics['mean_on']:.2f}", f"±{metrics['std_on']:.2f} SD")
            metric_col2.metric("Mean OFF Brightness", f"{metrics['mean_off']:.2f}", f"±{metrics['std_off']:.2f} SD")
            
            if metrics['p_value'] < 0.05:
                test_name = "Paired T-Test" if is_paired_test else "Welch's T-Test"
                metric_col3.metric(f"P-Value ({test_name})", f"{metrics['p_value']:.4e}", "Statistically Significant", delta_color="normal")
            else:
                test_name = "Paired T-Test" if is_paired_test else "Welch's T-Test"
                metric_col3.metric(f"P-Value ({test_name})", f"{metrics['p_value']:.4f}", "Not Significant", delta_color="inverse")

            # --- DATA VISUALIZATION ---
            fig_box = draw_boxplot(on_data, off_data, metrics['p_value'], analysis_mode, neighborhood_size, metrics, denoise_mode)
            st.pyplot(fig_box)

            # --- CSV EXPORT GENERATION ---
            max_len = max(metrics['n_on'], metrics['n_off'])
            on_data_padded = np.pad(on_data, (0, max_len - metrics['n_on']), constant_values=np.nan)
            off_data_padded = np.pad(off_data, (0, max_len - metrics['n_off']), constant_values=np.nan)
            
            df_raw = pd.DataFrame({"Microwave ON": on_data_padded, "Microwave OFF": off_data_padded})
            raw_csv_string = df_raw.to_csv(index=False)
            
            csv_header = "provided by Minhao Liu\n\n"
            csv_header += f"--- Statistical Summary ({analysis_mode}) ---\n"
            csv_header += f"Filter Applied: {denoise_mode}\n\n"
            csv_header += "Group,Sample Size (N),Mean,Standard Deviation\n"
            csv_header += f"Microwave ON,{metrics['n_on']},{metrics['mean_on']:.4f},{metrics['std_on']:.4f}\n"
            csv_header += f"Microwave OFF,{metrics['n_off']},{metrics['mean_off']:.4f},{metrics['std_off']:.4f}\n\n"
            csv_header += f"T-Statistic,{metrics['t_stat']:.6f}\n"
            csv_header += f"P-Value,{metrics['p_value']:.6e}\n\n"
            csv_header += "--- Raw Brightness Data ---\n"
            
            final_csv_output = (csv_header + raw_csv_string).encode('utf-8')
            st.download_button("📥 Download Comprehensive Analysis Table (.csv)", data=final_csv_output, file_name="ODMR_analysis_provided_by_Minhao_Liu.csv", mime="text/csv")
