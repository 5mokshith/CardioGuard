import numpy as np
from scipy.signal import find_peaks
from src.features.mi_feature_extractor import MIFeatureExtractor  # Assuming you rename your current file to mi_feature_extractor.py

def extract_features(signal, sampling_rate):
    """
    Extract features from an ECG signal segment.
    
    Args:
        signal (np.array): Raw ECG signal data
        sampling_rate (int): Sampling rate in Hz
    
    Returns:
        dict: Dictionary containing extracted features
    """
    # Normalize signal
    signal = (signal - np.mean(signal)) / np.std(signal)
    
    # Find R peaks
    peaks, _ = find_peaks(signal, distance=int(0.2 * sampling_rate))  # Minimum 200ms between peaks
    
    features = {}
    
    # Basic statistical features
    features['mean'] = np.mean(signal)
    features['std'] = np.std(signal)
    features['max'] = np.max(signal)
    features['min'] = np.min(signal)
    features['range'] = np.ptp(signal)
    
    # Heart rate features
    if len(peaks) > 1:
        rr_intervals = np.diff(peaks) / sampling_rate
        features['heart_rate'] = 60 / np.mean(rr_intervals)
        features['heart_rate_std'] = np.std(rr_intervals) * 60
        features['rr_interval_mean'] = np.mean(rr_intervals)
        features['rr_interval_std'] = np.std(rr_intervals)
    else:
        features['heart_rate'] = 0
        features['heart_rate_std'] = 0
        features['rr_interval_mean'] = 0
        features['rr_interval_std'] = 0
    
    # Segment analysis
    window_size = int(0.1 * sampling_rate)  # 100ms window
    
    # ST segment features (measured 60-80ms after R peaks)
    st_segments = []
    for peak in peaks:
        st_start = min(len(signal), peak + int(0.06 * sampling_rate))
        st_end = min(len(signal), peak + int(0.08 * sampling_rate))
        if st_end > st_start:
            st_segment = signal[st_start:st_end]
            st_segments.append(np.mean(st_segment))
    
    if st_segments:
        features['st_mean'] = np.mean(st_segments)
        features['st_std'] = np.std(st_segments)
        features['st_max'] = np.max(st_segments)
        features['st_min'] = np.min(st_segments)
    else:
        features['st_mean'] = 0
        features['st_std'] = 0
        features['st_max'] = 0
        features['st_min'] = 0
    
    # Frequency domain features
    fft_vals = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(len(signal), 1/sampling_rate)
    
    # Consider only physiologically relevant frequencies (0.5-40Hz)
    mask = (freqs >= 0.5) & (freqs <= 40)
    fft_vals = fft_vals[mask]
    freqs = freqs[mask]
    
    if len(freqs) > 0:
        features['dominant_frequency'] = freqs[np.argmax(fft_vals)]
        features['spectral_power'] = np.sum(np.square(fft_vals))
        
        # Spectral entropy
        normalized_psd = fft_vals / np.sum(fft_vals)
        features['spectral_entropy'] = -np.sum(normalized_psd * np.log2(normalized_psd + 1e-10))
    else:
        features['dominant_frequency'] = 0
        features['spectral_power'] = 0
        features['spectral_entropy'] = 0
    
    # Convert features to list in fixed order for ML model
    feature_list = [
        features['mean'], features['std'], features['max'], features['min'],
        features['range'], features['heart_rate'], features['heart_rate_std'],
        features['rr_interval_mean'], features['rr_interval_std'],
        features['st_mean'], features['st_std'], features['st_max'], features['st_min'],
        features['dominant_frequency'], features['spectral_power'], features['spectral_entropy']
    ]
    
    return np.array(feature_list).reshape(1, -1)