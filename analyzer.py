import numpy as np
from PIL import Image
from skimage import filters, feature
from scipy import stats

def establish_baseline(image_file, sigma, thresh_mult, mode, peak_thresh_percent):
    """Processes the first OFF frame to lock coordinates and background masks."""
    baseline_pil = Image.open(image_file)
    baseline_img = np.array(baseline_pil.convert('L'))
    
    blurred_baseline = filters.gaussian(baseline_img, sigma=sigma)
    base_thresh = filters.threshold_otsu(blurred_baseline)
    final_thresh = base_thresh * thresh_mult
    
    baseline_red_mask = blurred_baseline > final_thresh
    baseline_bg_mask = blurred_baseline <= final_thresh
    
    peaks_xy = []
    if mode == "Multi-Peak Local Maximum":
        coordinates = feature.peak_local_max(
            blurred_baseline, 
            min_distance=2, 
            threshold_rel=peak_thresh_percent / 100.0, 
            labels=baseline_red_mask
        )
        peaks_xy = [(y, x) for y, x in coordinates]
        
    return baseline_img, baseline_red_mask, baseline_bg_mask, peaks_xy

def extract_brightness(uploaded_files, red_mask, bg_mask, mode, peaks, n_size):
    """Measures brightness across all frames using strictly locked coordinates."""
    vals = []
    for file in uploaded_files:
        img = np.array(Image.open(file).convert('L'))
        
        bg_average = np.mean(img[bg_mask])
        bg_corrected_img = img - bg_average
        
        if mode == "Whole-ROI Average (Recommended)":
            corrected_pixels = bg_corrected_img[red_mask]
            vals.append(np.mean(corrected_pixels))
        else:
            frame_peak_values = []
            half_step = n_size // 2
            
            for (y, x) in peaks:
                y_min = max(0, y - half_step)
                y_max = min(img.shape[0], y + half_step + 1)
                x_min = max(0, x - half_step)
                x_max = min(img.shape[1], x + half_step + 1)
                
                local_neighborhood = bg_corrected_img[y_min:y_max, x_min:x_max]
                frame_peak_values.append(np.mean(local_neighborhood))
                
            if len(frame_peak_values) > 0:
                vals.append(np.mean(frame_peak_values))
            else:
                vals.append(0)
    return vals

def apply_denoising(on_data, off_data, mode):
    """Applies algorithmic denoising to mathematically flatten 1/f thermal and laser drift."""
    on_clean = np.array(on_data)
    off_clean = np.array(off_data)
    
    if mode == "None (Raw Data)":
        return on_clean.tolist(), off_clean.tolist()
        
    # Both advanced denoising methods process data strictly by cycle pairs
    min_len = min(len(on_clean), len(off_clean))
    on_clean = on_clean[:min_len]
    off_clean = off_clean[:min_len]
    
    if mode == "Polynomial Detrending (Slow Drift)":
        # Fits a 2nd-degree polynomial to the unperturbed OFF baseline
        cycles = np.arange(min_len)
        poly_coeffs = np.polyfit(cycles, off_clean, 2)
        trend_line = np.polyval(poly_coeffs, cycles)
        
        # Subtract the drift curve to flatten the data across time
        drift_offset = trend_line - np.mean(off_clean)
        off_clean = off_clean - drift_offset
        on_clean = on_clean - drift_offset
        
    elif mode == "Software Lock-In (Fast Cycle Filter)":
        # Calculates the local DC offset of each specific ON/OFF cycle pair
        cycle_means = (on_clean + off_clean) / 2.0
        global_mean = np.mean(cycle_means)
        
        # Flattens all cycle pairs to the global mean, isolating the AC microwave amplitude
        local_drift = cycle_means - global_mean
        off_clean = off_clean - local_drift
        on_clean = on_clean - local_drift
        
    return on_clean.tolist(), off_clean.tolist()

def calculate_statistics(on_data, off_data, is_paired=False):
    """Runs Welch's or Paired t-test based on the active denoising filter."""
    if is_paired:
        # Software Lock-In inherently aligns data into exact temporal cycle pairs
        t_stat, p_value = stats.ttest_rel(on_data, off_data)
    else:
        t_stat, p_value = stats.ttest_ind(on_data, off_data, equal_var=False)
    
    metrics = {
        "n_on": len(on_data),
        "n_off": len(off_data),
        "mean_on": np.mean(on_data) if len(on_data) > 0 else 0,
        "mean_off": np.mean(off_data) if len(off_data) > 0 else 0,
        "std_on": np.std(on_data, ddof=1) if len(on_data) > 1 else 0,
        "std_off": np.std(off_data, ddof=1) if len(off_data) > 1 else 0,
        "t_stat": t_stat,
        "p_value": p_value
    }
    return metrics
