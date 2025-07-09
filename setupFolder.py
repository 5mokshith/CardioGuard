# setup.py
import os

# Define project structure
directories = [
    'data',
    'models',
    'notebooks',
    'src/preprocessing',
    'src/features',
    'src/models',
    'src/visualization'
]

# Create directories
for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"Created directory: {directory}")

# Create empty __init__.py files for proper Python package structure
for directory in directories:
    if directory.startswith('src'):
        init_file = os.path.join(directory, '__init__.py')
        with open(init_file, 'w') as f:
            pass
        print(f"Created: {init_file}")

# Create requirements.txt
requirements = [
    'numpy',
    'pandas',
    'matplotlib',
    'scipy',
    'scikit-learn',
    'wfdb',  # For reading MIT-BIH database
    'tensorflow',  # For deep learning models
    'PyWavelets',  # For wavelet transforms
    'requests',  # For downloading data
    'joblib',     # For model persistence
    'ipykernel'   # For Jupyter notebook support
]

with open('requirements.txt', 'w') as f:
    f.write('\n'.join(requirements))
print("Created: requirements.txt")