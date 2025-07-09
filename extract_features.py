import os
from pathlib import Path
from src.features.feature_extraction import MIFeatureExtractor

def main():
    # Set up paths
    base_dir = Path(os.getcwd())
    data_dir = base_dir / 'data' / 'mit-bih-st-change-database-1.0.0'
    
    # Verify data directory exists
    if not data_dir.exists():
        print(f"Error: Data directory not found at {data_dir}")
        print("Please ensure you have downloaded the MIT-BIH ST Change Database")
        return
    
    print(f"Starting feature extraction from: {data_dir}")
    try:
        # Initialize feature extractor
        extractor = MIFeatureExtractor(str(data_dir))
        
        # Run feature extraction
        features_df = extractor.extract_all_features()
        
        # Verify results
        if not features_df.empty:
            print("\nFeature extraction completed successfully!")
            print(f"Shape of extracted features: {features_df.shape}")
            print("\nFeature columns:")
            for col in features_df.columns:
                print(f"- {col}")
            
            # Display class distribution
            positive_cases = features_df['label'].sum()
            total_cases = len(features_df)
            print(f"\nClass distribution:")
            print(f"Total samples: {total_cases}")
            print(f"Positive cases (ST episodes): {positive_cases} ({positive_cases/total_cases*100:.2f}%)")
            print(f"Negative cases (Normal): {total_cases-positive_cases} ({(total_cases-positive_cases)/total_cases*100:.2f}%)")
            
    except Exception as e:
        print(f"Error during feature extraction: {str(e)}")
        raise

if __name__ == "__main__":
    main()