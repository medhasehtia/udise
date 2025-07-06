import pandas as pd
import os

# Get the directory where this script is located (should be your project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Set the current working directory to the script's directory
os.chdir(script_dir)

print(f"Current Working Directory: {os.getcwd()}")

# Define the paths to your original (large) data files relative to the project root
PROF_FILE_PATH = os.path.join("data", "100_prof1.csv")
FAC_FILE_PATH = os.path.join("data", "100_fac.csv")

# Check if files exist before trying to load them
if not os.path.exists(PROF_FILE_PATH):
    print(f"Error: '{PROF_FILE_PATH}' not found. Please ensure this script is in your project's root directory and the 'data' folder exists.")
    exit()
if not os.path.exists(FAC_FILE_PATH):
    print(f"Error: '{FAC_FILE_PATH}' not found. Please ensure this script is in your project's root directory and the 'data' folder exists.")
    exit()

print(f"Loading original data from '{PROF_FILE_PATH}' (size: {os.path.getsize(PROF_FILE_PATH)/1024**2:.2f} MB) and '{FAC_FILE_PATH}' (size: {os.path.getsize(FAC_FILE_PATH)/1024**2:.2f} MB)...")

prof = pd.read_csv(PROF_FILE_PATH)
fac = pd.read_csv(FAC_FILE_PATH)

print(f"Original prof rows: {len(prof)}")
print(f"Original fac rows: {len(fac)}")

# --- Subsetting the data ---
# Adjust 'frac' (fraction) to get a smaller dataset that fits in Streamlit Cloud's memory.
# Start with a small fraction like 0.05 (5%)
sampling_fraction = 0.05 # Try 5% first, increase if it works and you need more data
random_seed = 42

print(f"Subsetting data to {sampling_fraction*100:.0f}% of original size...")
prof_subset = prof.sample(frac=sampling_fraction, random_state=random_seed)
fac_subset = fac.sample(frac=sampling_fraction, random_state=random_seed)

print(f"Subset prof rows: {len(prof_subset)}")
print(f"Subset fac rows: {len(fac_subset)}")

# --- Saving the subsetted data, OVERWRITING the original files ---
print(f"Saving subsetted data back to '{PROF_FILE_PATH}' (new size: {len(prof_subset)} rows) and '{FAC_FILE_PATH}' (new size: {len(fac_subset)} rows)...")
prof_subset.to_csv(PROF_FILE_PATH, index=False) # index=False prevents writing the DataFrame index as a column
fac_subset.to_csv(FAC_FILE_PATH, index=False)

print("\n------------------------------------------------------------")
print("Data subsetting complete and files overwritten locally.")
print(f"New prof1.csv size: {os.path.getsize(PROF_FILE_PATH)/1024**2:.2f} MB")
print(f"New fac.csv size: {os.path.getsize(FAC_FILE_PATH)/1024**2:.2f} MB")
print("Now, you need to commit these changes and push to GitHub.")
print("------------------------------------------------------------")