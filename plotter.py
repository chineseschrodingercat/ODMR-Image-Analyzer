import matplotlib.pyplot as plt
import numpy as np

def draw_preview_pane(baseline_img, mask, peaks_xy, mode):
    """Draws the side-by-side locked coordinate preview."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    ax1.imshow(baseline_img, cmap='gray')
    ax1.set_title("Raw Baseline (OFF Frame 1)")
    ax1.axis('off')
    
    ax2.imshow(baseline_img, cmap='gray')
    ax2.imshow(mask, cmap='Wistia', alpha=0.4) 
    
    if mode == "Multi-Peak Local Maximum":
        ax2.set_title(f"Tracked Peaks: {len(peaks_xy)} Detected")
        for (y, x) in peaks_xy:
            ax2.plot(x, y, marker='o', color='red', markersize=3)
    else:
        ax2.set_title("Active ROI Mask (Whole Area)")
        
    ax2.axis('off')
    
    fig.text(0.98, 0.02, 'provided by Minhao Liu', ha='right', va='bottom', fontsize=9, color='gray', style='italic')
    return fig

def draw_boxplot(on_data, off_data, p_value, mode, n_size, metrics, denoise_mode="None (Raw Data)"):
    """Draws a publication-ready boxplot with significance brackets."""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    labels = [f"Microwave ON (N={metrics['n_on']})", f"Microwave OFF (N={metrics['n_off']})"]
    ax.boxplot([on_data, off_data], labels=labels, patch_artist=True)
    
    if mode == "Multi-Peak Local Maximum":
        ax.set_ylabel(f'Mean of Peak Brightnesses ({n_size}x{n_size} px)')
    else:
        ax.set_ylabel('Integrated Brightness')
        
    # Document active filtering in graph title
    if denoise_mode != "None (Raw Data)":
        ax.set_title(f'Fluorescence Comparison\n(Filter: {denoise_mode})', fontsize=11)
    else:
        ax.set_title('Fluorescence Comparison')
        
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    if p_value <= 0.0001: sig_symbol = "****"
    elif p_value <= 0.001: sig_symbol = "***"
    elif p_value <= 0.01: sig_symbol = "**"
    elif p_value <= 0.05: sig_symbol = "*"
    else: sig_symbol = "ns"
    
    y_max = max(np.max(on_data), np.max(off_data))
    y_min = min(np.min(on_data), np.min(off_data))
    y_range = y_max - y_min
    
    bracket_y = y_max + (y_range * 0.05)
    bracket_height = y_range * 0.02
    
    x1, x2 = 1, 2 
    ax.plot([x1, x1, x2, x2], [bracket_y, bracket_y + bracket_height, bracket_y + bracket_height, bracket_y], lw=1.5, c='black')
    font_color = 'red' if sig_symbol == 'ns' else 'black'
    ax.text((x1+x2)*.5, bracket_y + bracket_height, sig_symbol, ha='center', va='bottom', color=font_color, fontsize=12, fontweight='bold')
    ax.set_ylim(bottom=ax.get_ylim()[0], top=bracket_y + (y_range * 0.15))

    fig.text(0.98, 0.02, 'provided by Minhao Liu', ha='right', va='bottom', fontsize=9, color='gray', style='italic')
    return fig
