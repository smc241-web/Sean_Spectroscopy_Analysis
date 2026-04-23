import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d
from scipy.signal import find_peaks

def find_peak_start(smoothed_data, peak_index, n_sigma=6, min_baseline_samples=200,
                    window=50, apex_exclusion_window=1000):

    derivative = np.gradient(smoothed_data.astype(float))

    baseline_deriv = derivative[:min_baseline_samples]
    deriv_std      = np.std(baseline_deriv)
    flat_threshold = n_sigma * deriv_std

    min_allowed_centre = peak_index - apex_exclusion_window
    max_allowed_centre = peak_index + apex_exclusion_window

    for i in range(peak_index, window, -1):
        window_deriv = derivative[i - window : i]
        centre = i - window // 2
        if np.mean(np.abs(window_deriv)) <= flat_threshold and not (min_allowed_centre <= centre <= max_allowed_centre):
            return centre

    return 0


def plot_derivative_threshold(smoothed_data, peak_index, n_sigma=6, min_baseline_samples=200,
                               window=50, apex_exclusion_window=1000, time_axis=None):

    derivative = np.gradient(smoothed_data.astype(float))

    baseline_deriv = derivative[:min_baseline_samples]
    deriv_std      = np.std(baseline_deriv)
    flat_threshold = n_sigma * deriv_std

    min_allowed_centre = peak_index - apex_exclusion_window
    max_allowed_centre = peak_index + apex_exclusion_window

    peak_start_centre = 0
    for i in range(peak_index, window, -1):
        window_deriv = derivative[i - window : i]
        centre = i - window // 2
        if np.mean(np.abs(window_deriv)) <= flat_threshold and not (min_allowed_centre <= centre <= max_allowed_centre):
            peak_start_centre = centre
            break

    x = time_axis if time_axis is not None else np.arange(len(smoothed_data))

    fig, axes = plt.subplots(2, 1, figsize=(12, 7), tight_layout=True, sharex=True)

    # ── Top: smoothed signal ─────────────────────────────────────────────────
    axes[0].plot(x, smoothed_data, color='steelblue', linewidth=1.5, label='Smoothed signal')
    axes[0].axvline(x[peak_index],         color='red',    linestyle='--', linewidth=1.2, label=f'Apex: {x[peak_index]:.2f}')
    axes[0].axvline(x[peak_start_centre],  color='orange', linestyle='--', linewidth=1.2, label=f'Peak start: {x[peak_start_centre]:.2f}')
    axes[0].axvspan(x[max(0, min_allowed_centre)], x[min(len(x)-1, max_allowed_centre)],
                    alpha=0.1, color='red', label=f'Exclusion zone (±{apex_exclusion_window} pts)')
    axes[0].set_ylabel('Signal (mV)', fontweight='bold')
    axes[0].legend(fontsize=8, loc='upper right')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_title('Smoothed Signal')

    # ── Bottom: derivative ───────────────────────────────────────────────────
    axes[1].plot(x, np.abs(derivative), color='steelblue', linewidth=1.0, label='|derivative|')
    axes[1].axhline( flat_threshold, color='crimson',  linestyle='-',  linewidth=1.5, label=f'Threshold (n_sigma={n_sigma}): {flat_threshold:.5f}')
    axes[1].axhline(-flat_threshold, color='crimson',  linestyle='-',  linewidth=1.5)
    axes[1].axvline(x[peak_index],        color='red',    linestyle='--', linewidth=1.2, label=f'Apex')
    axes[1].axvline(x[peak_start_centre], color='orange', linestyle='--', linewidth=1.2, label=f'Peak start: {x[peak_start_centre]:.2f}')
    axes[1].axvspan(x[max(0, min_allowed_centre)], x[min(len(x)-1, max_allowed_centre)],
                    alpha=0.1, color='red', label=f'Exclusion zone')
    axes[1].axvspan(x[0], x[min_baseline_samples], alpha=0.1, color='green', label='Baseline region')
    axes[1].set_xlabel(r'Time ($\mu$s)' if time_axis is not None else 'Sample index', fontweight='bold')
    axes[1].set_ylabel('|Derivative|', fontweight='bold')
    axes[1].legend(fontsize=8, loc='upper right')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_title(f'First Derivative  —  baseline std={deriv_std:.5f},  threshold={flat_threshold:.5f}')

    plt.suptitle('Derivative Threshold Diagnostic', fontsize=13, fontweight='bold')
    plt.show()

    
def find_pulse_height(raw_data, smoothed_data, peak_index, n_sigma=6,
                      min_baseline_samples=200, baseline_window=200,
                      derivative_window=50):
    raw_data      = np.array(raw_data).flatten()
    smoothed_data = np.array(smoothed_data).flatten()

    peak_start_index = find_peak_start(
        smoothed_data        = smoothed_data,
        peak_index           = peak_index,
        n_sigma              = n_sigma,
        min_baseline_samples = min_baseline_samples,
        window               = derivative_window,
    )

    baseline_left = max(0, peak_start_index - baseline_window)
    baseline      = float(np.mean(raw_data[baseline_left : peak_start_index]))
    peak_value    = float(raw_data[peak_index])
    pulse_height  = peak_value - baseline

    return pulse_height, peak_start_index, baseline, peak_value

def plot_accepted_pulses(data, smoothed_data, accepted_peaks, threshold=3, window_size=200,
                         min_pulse_height=0.0, smooth=False, smooth_size=5, time_axis=None):

    data          = np.array(data).flatten()
    smoothed_data = np.array(smoothed_data).flatten()

    # If caller wants an extra smoothing pass on top, apply it
    work_smoothed = uniform_filter1d(smoothed_data, size=smooth_size) if smooth else smoothed_data

    accepted = []
    for peak_idx in accepted_peaks:
        pulse_height, peak_start_idx, baseline, peak_value = find_pulse_height(
            raw_data=data,
            smoothed_data=work_smoothed,   # ← was missing entirely
            peak_index=peak_idx,
            n_sigma=threshold,
            min_baseline_samples=window_size,
            baseline_window=window_size,
        )

        if pulse_height is not None and float(pulse_height) >= min_pulse_height:
            accepted.append({
                "peak_idx":       peak_idx,
                "peak_start_idx": peak_start_idx,
                "baseline":       baseline,
                "peak_value":     peak_value,
                "pulse_height":   pulse_height,
            })

        
    n = len(accepted)
    if n == 0:
        print("No accepted pulses to plot.")
        return

    cols = min(3, n)
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes = np.array(axes).flatten()  # always iterable

    for ax, pulse in zip(axes, accepted):
        peak_idx      = pulse["peak_idx"]
        peak_start_idx = pulse["peak_start_idx"]
        baseline      = pulse["baseline"]
        peak_value    = pulse["peak_value"]
        pulse_height  = pulse["pulse_height"]

        # Show entire pulse
        x = time_axis if time_axis is not None else np.arange(len(data))
        y = data

        # --- Signal ---
        ax.plot(x, y, color="steelblue", linewidth=1.8, label="Signal")

        # --- Baseline ---
        ax.axhline(baseline, color="gray", linestyle="--",
                   linewidth=1.2, label=f"Baseline: {baseline:.3f}")

        # --- Peak start marker ---
        ax.axvline(x[peak_start_idx], color="orange", linestyle=":",
                   linewidth=1.4, label=f"Peak start: {x[peak_start_idx]:.2f}")

        # --- Smoothed Pulse ---
        ax.plot(x, data, color="steelblue", linewidth=1.8, label="Raw signal")
        ax.plot(x, smoothed_data, color="darkorange", linewidth=1.2, linestyle="--", label="Smoothed signal")
        
        # --- Peak apex marker ---
        ax.plot(x[peak_idx], peak_value, "rv", markersize=10, label=f"Apex: {peak_value:.3f}")

        # --- Pulse height arrow ---
        ax.annotate(
            "",
            xy=(peak_idx, peak_value),
            xytext=(peak_idx, baseline),
            arrowprops=dict(arrowstyle="<->", color="crimson", lw=1.8),
        )

        # --- Pulse height label ---
        ax.text(
            x[peak_idx] + (x[-1]-x[0])*0.02, baseline + pulse_height / 2,
            f"PH = {pulse_height:.3f}",
            color="crimson", fontsize=9, va="center"
        )

        ax.set_title(f"Pulse @ {x[peak_idx]:.1f} µs", fontsize=10)
        ax.set_xlabel(r"Time ($\mu$s)" if time_axis is not None else "Sample index")
        ax.set_ylabel("Signal (mV)")
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(True, alpha=0.3)

    # Hide any unused subplots
    for ax in axes[n:]:
        ax.set_visible(False)

    fig.suptitle(
        f"Accepted Pulses",
        fontsize=13, fontweight="bold", y=1.01
    )
    plt.tight_layout()
    plt.show()