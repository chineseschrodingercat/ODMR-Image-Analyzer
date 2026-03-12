import numpy as np
from PIL import Image
from skimage import filters, feature
from scipy import stats

def establish_baseline(image_file, sigma, thresh_mult, mode, peak_thresh_percent):
    """
    Processes the first OFF frame to lock coordinates and background masks.
    """
    baseline_pil = Image.open(image_file)
    baseline_img = np.array(baseline_pil.convert('L'))
    
    # 1. Smooth and Threshold
    blurred_baseline = filters.gaussian(baseline_img, sigma=sigma)
    base_thresh = filters.threshold_otsu(blurred_baseline)
    final_thresh = base_thresh * thresh_mult
    
    baseline_red_mask = blurred_baseline > final_thresh
    baseline_bg_mask = blurred_baseline <= final_thresh
    
    # 2. Extract Locked Coordinates (if Multi-Peak mode is active)
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
    """
    Measures brightness across all frames using the strictly locked coordinates.
    """
    vals = []
    for file in uploaded_files:
        img = np.array(Image.open(file).convert('L'))
        
        # Calculate fresh background average for THIS frame
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

def calculate_statistics(on_data, off_data):
    """Runs Welch's t-test and calculates standard metrics."""
    t_stat, p_value = stats.ttest_ind(on_data, off_data, equal_var=False)
    
    metrics = {
        "n_on": len(on_data),
        "n_off": len(off_data),
        "mean_on": np.mean(on_data),
        "mean_off": np.mean(off_data),
        "std_on": np.std(on_data, ddof=1),
        "std_off": np.std(off_data, ddof=1),
        "t_stat": t_stat,
        "p_value": p_value
    }
    return metrics
