import os

def list_site_packages(startpath):
    """List only the top-level directories in site-packages and output to a properly titled file."""
    startpath = os.path.abspath(startpath)
    output_file = "datapunk_env_site_packages_structure.txt"
    
    if not os.path.exists(startpath):
        print(f"Error: The directory {startpath} does not exist.")
        return
    
    with open(output_file, "w") as f:
        f.write("Datapunk-env Site-Packages:\n")
        for root, dirs, _ in os.walk(startpath):
            rel_dir = os.path.relpath(root, startpath).replace('\\', '/')
            level = rel_dir.count('/')

            # Limit depth to just the top level
            if level == 0:
                f.write(f'{os.path.basename(root)}/\n')  # Write directory name to file

# Call the function
list_site_packages('datapunk-env/Lib/site-packages')