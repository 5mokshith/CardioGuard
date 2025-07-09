import numpy as np
import wfdb.io
import wfdb.processing
import os
import pandas as pd
from pathlib import Path

class MIFeatureExtractor:
    def __init__(self, data_dir):
        self.data_dir = data_dir
    
    def get_record_list(self):
        """Get list of available record names"""
        try:
            record_files = [f for f in os.listdir(self.data_dir) if f.endswith('.hea')]
            if not record_files:
                raise ValueError(f"No .hea files found in {self.data_dir}")
            record_names = [f.replace('.hea', '') for f in record_files]
            return record_names
        except Exception as e:
            print(f"Error reading directory {self.data_dir}: {str(e)}")
            return []
    
    def load_record(self, record_name):
        """Load a record and its annotations"""
        try:
            record_path = os.path.join(self.data_dir, record_name)
            record = wfdb.io.rdrecord(record_path)
            annotation = wfdb.rdann(record_path, 'atr')
            return record, annotation
        except Exception as e:
            print(f"Error loading record {record_name}: {e}")
            return None, None

    def identify_st_episodes(self, annotation):
        """Extract ST episodes from annotations"""
        st_episodes = []
        current_episode = None
        
        # Enhanced ST annotation symbols with additional context
        st_symbols = {
            '+': {'type': 'elevation', 'severity': 'high'},    # ST elevation
            '/': {'type': 'depression', 'severity': 'medium'}, # ST depression
            '\\': {'type': 'depression', 'severity': 'medium'}, # ST depression
            's': {'type': 'elevation', 'severity': 'low'},     # ST segment change
            'S': {'type': 'elevation', 'severity': 'medium'}   # ST segment change
        }
        
        for i, symbol in enumerate(annotation.symbol):
            sample = annotation.sample[i]
            
            # Start of ST episode
            if symbol in st_symbols and current_episode is None:
                current_episode = {
                    'start': sample,
                    'start_idx': i,
                    'type': st_symbols[symbol]['type'],
                    'severity': st_symbols[symbol]['severity']
                }
            
            # End of ST episode
            elif symbol in ['N', 'n'] and current_episode is not None:
                current_episode['end'] = sample
                current_episode['end_idx'] = i
                current_episode['duration'] = current_episode['end'] - current_episode['start']
                st_episodes.append(current_episode)
                current_episode = None
        
        # Handle last episode
        if current_episode is not None:
            current_episode['end'] = annotation.sample[-1]
            current_episode['end_idx'] = len(annotation.symbol) - 1
            current_episode['duration'] = current_episode['end'] - current_episode['start']
            st_episodes.append(current_episode)
        
        return st_episodes

    def extract_features_from_beat(self, beat, fs, r_peak_idx):
        """Extract enhanced features from a single heartbeat"""
        features = {}
        
        # Enhanced time windows (in seconds) for more comprehensive segment analysis
        windows = {
            'p_wave': (-0.15, -0.07),  # P wave
            'pq': (-0.07, -0.03),      # PQ segment (baseline)
            'qrs': (-0.03, 0.05),      # QRS complex
            'stp': (0.05, 0.09),       # Early ST segment (ST point)
            'st': (0.09, 0.16),        # ST segment
            't_wave': (0.16, 0.35),    # T wave
            'tp': (0.35, 0.45)         # TP segment (when available)
        }
        
        # Convert windows to sample indices
        indices = {name: (int(start * fs) + r_peak_idx, int(end * fs) + r_peak_idx) 
                  for name, (start, end) in windows.items()}
        
        # Extract enhanced features from each segment
        for name, (start_idx, end_idx) in indices.items():
            if start_idx >= 0 and end_idx < len(beat):
                segment = beat[start_idx:end_idx]
                
                # Basic statistical features
                features[f'{name}_mean'] = np.mean(segment)
                features[f'{name}_median'] = np.median(segment)
                features[f'{name}_std'] = np.std(segment)
                features[f'{name}_range'] = np.ptp(segment)
                features[f'{name}_energy'] = np.sum(np.square(segment))
                
                # Morphology features
                features[f'{name}_max'] = np.max(segment)
                features[f'{name}_min'] = np.min(segment)
                features[f'{name}_area'] = np.trapezoid(y=segment, dx=1/fs)
                
                if len(segment) > 2:
                    # Slope features (using polyfit for robustness)
                    x = np.arange(len(segment))
                    slope, intercept = np.polyfit(x, segment, 1)
                    features[f'{name}_slope'] = slope
                    
                    # Curvature features (2nd derivative approximation)
                    if len(segment) > 4:
                        diff2 = np.diff(np.diff(segment))
                        features[f'{name}_curvature_mean'] = np.mean(np.abs(diff2))
                        features[f'{name}_curvature_max'] = np.max(np.abs(diff2))
        
        # ST segment specific features (ST elevation/depression)
        if 'pq_mean' in features and 'st_mean' in features:
            features['st_deviation'] = features['st_mean'] - features['pq_mean']
            features['st_deviation_normalized'] = features['st_deviation'] / features['qrs_range'] if features['qrs_range'] > 0 else 0
        
        # T wave features relative to baseline
        if 'pq_mean' in features and 't_wave_max' in features:
            features['t_wave_amplitude'] = features['t_wave_max'] - features['pq_mean']
            features['t_wave_symmetry'] = features['t_wave_mean'] / features['t_wave_max'] if features['t_wave_max'] != 0 else 0
        
        # QT interval estimation (when both Q and T are visible)
        if 'qrs_min' in features and 't_wave_max' in features:
            qt_proxy = (end_idx - start_idx) / fs  # Approximate QT interval in seconds
            features['qt_interval'] = qt_proxy
        
        # Frequency domain features using FFT
        if len(beat) > 20:
            fft_vals = np.abs(np.fft.rfft(beat))
            freqs = np.fft.rfftfreq(len(beat), 1/fs)
            if len(freqs) > 1:
                # Limit to physiologically relevant frequencies (0.5-40Hz)
                mask = (freqs >= 0.5) & (freqs <= 40)
                if np.any(mask):
                    fft_vals = fft_vals[mask]
                    freqs = freqs[mask]
                    
                    # Dominant frequency
                    dominant_freq_idx = np.argmax(fft_vals)
                    features['dominant_frequency'] = freqs[dominant_freq_idx]
                    features['spectral_power'] = np.sum(np.square(fft_vals))
                    
                    # Spectral entropy
                    normalized_psd = fft_vals / np.sum(fft_vals)
                    features['spectral_entropy'] = -np.sum(normalized_psd * np.log2(normalized_psd + 1e-10))
        
        return features

    def process_record(self, record_name):
        """Process a single record to extract features"""
        record, annotation = self.load_record(record_name)
        if record is None or annotation is None:
            return pd.DataFrame()
        
        # Get signal data (use all available leads)
        signal_data = record.p_signal
        num_leads = signal_data.shape[1]
        fs = record.fs
        
        # Get ST episodes
        st_episodes = self.identify_st_episodes(annotation)
        
        # Extract features from each normal beat
        features_list = []
        for i, symbol in enumerate(annotation.symbol):
            if symbol in ['N', 'n']:
                sample = annotation.sample[i]
                
                # Extract beat window
                window_before = int(0.3 * fs)  # Increased window to capture P wave
                window_after = int(0.5 * fs)   # Increased window to capture T wave
                
                # Check if beat is during ST episode
                in_st_episode = False
                episode_type = None
                episode_severity = None
                for episode in st_episodes:
                    if episode['start'] <= sample <= episode['end']:
                        in_st_episode = True
                        episode_type = episode['type']
                        episode_severity = episode['severity']
                        break
                
                # Process all available leads
                for lead_idx in range(num_leads):
                    if sample - window_before >= 0 and sample + window_after < signal_data.shape[0]:
                        beat = signal_data[sample - window_before:sample + window_after, lead_idx]
                        
                        # Extract features
                        features = self.extract_features_from_beat(beat, fs, window_before)
                        
                        # Additional metadata
                        features.update({
                            'record': record_name,
                            'sample': sample,
                            'lead': lead_idx,
                            'label': 1 if in_st_episode else 0,
                            'st_type': episode_type if in_st_episode else None,
                            'st_severity': episode_severity if in_st_episode else None,
                            'rr_interval': None  # Will be calculated below
                        })
                        
                        # Calculate RR interval (if possible)
                        if i > 0 and annotation.symbol[i-1] in ['N', 'n']:
                            prev_sample = annotation.sample[i-1]
                            features['rr_interval'] = (sample - prev_sample) / fs
                        
                        features_list.append(features)
        
        return pd.DataFrame(features_list)

    def extract_all_features(self):
        """Extract features from all records"""
        record_names = self.get_record_list()
        print(f"Found {len(record_names)} records")
        
        all_features = []
        for record_name in record_names:
            print(f"Processing record: {record_name}")
            features = self.process_record(record_name)
            if not features.empty:
                all_features.append(features)
                print(f"  Extracted {len(features)} beats, {sum(features['label'])} ST episodes")
        
        if not all_features:
            raise ValueError("No features extracted from any records")
            
        combined_features = pd.concat(all_features, ignore_index=True)
        
        # Apply additional feature engineering
        combined_features = self.engineer_additional_features(combined_features)
        
        # Handle missing values
        combined_features = self.handle_missing_values(combined_features)
        
        # Create output directory if it doesn't exist
        output_dir = Path(r"C:\Users\moksh\classroom\test_ML_deepalert\test\data\extracted")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use Path object for file path construction
        output_path = output_dir / 'mit_st_features.csv'
        combined_features.to_csv(output_path, index=False)
        
        # Print statistics
        total = len(combined_features)
        positives = sum(combined_features['label'])
        print(f"\nDataset statistics:")
        print(f"Total beats: {total}")
        print(f"ST episodes: {positives} ({positives/total*100:.1f}%)")
        print(f"Normal beats: {total-positives} ({(total-positives)/total*100:.1f}%)")
        if 'st_type' in combined_features.columns:
            st_types = combined_features[combined_features['label']==1]['st_type'].value_counts()
            print("\nST episode types:")
            for st_type, count in st_types.items():
                print(f"  {st_type}: {count} ({count/positives*100:.1f}%)")
        print(f"\nFeatures saved to: {output_path}")
        return combined_features

    def engineer_additional_features(self, df):
        """Engineer additional features from existing ones"""
        if df.empty:
            return df
        
        # ST/T ratio (useful for ischemia detection)
        if 'st_mean' in df.columns and 't_wave_mean' in df.columns:
            df['st_t_ratio'] = df['st_mean'] / df['t_wave_mean'].replace(0, np.nan)
        
        # QRS to T-wave amplitude ratio
        if 'qrs_range' in df.columns and 't_wave_range' in df.columns:
            df['qrs_t_amplitude_ratio'] = df['qrs_range'] / df['t_wave_range'].replace(0, np.nan)
        
        # ST integral (area under ST segment)
        if 'st_area' in df.columns and 'pq_mean' in df.columns:
            segment_length = 0.07  # Typical ST segment length in seconds
            baseline_area = df['pq_mean'] * segment_length
            df['st_integral'] = df['st_area'] - baseline_area
        
        # T wave symmetry (T wave morphology is important for ischemia detection)
        if 't_wave_area' in df.columns and 't_wave_max' in df.columns and 't_wave_range' in df.columns:
            t_wave_symmetry = df['t_wave_area'] / (df['t_wave_max'] * df['t_wave_range'])
            df['t_wave_symmetry_index'] = t_wave_symmetry.replace([np.inf, -np.inf], np.nan)
        
        return df

    def handle_missing_values(self, df):
        """Handle missing values in the dataset"""
        if df.empty:
            return df
        
        # For numerical columns, replace NaNs with median
        numerical_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numerical_cols:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
        
        # For categorical columns, replace NaNs with 'unknown'
        categorical_cols = df.select_dtypes(['object']).columns
        for col in categorical_cols:
            df[col] = df[col].fillna('unknown')
        
        return df

if __name__ == "__main__":
    data_dir = r'C:\Users\moksh\classroom\test_ML_deepalert\test\data\mit-bih-st-change-database-1.0.0\mit-bih-st-change-database-1.0.0'
    extractor = MIFeatureExtractor(data_dir)
    extractor.extract_all_features()