import os

# Define the directories you want to include in the output (relative to the startpath)
include_dirs = [
    './',
    'datapunk/',
    'datapunk/datapunk/',
    'datapunk/data_importer/',
    'datapunk/data_importer/data_dump/',
    'datapunk/data_importer/data_logs/',
    'datapunk/mongodb/',
    'datapunk/mongodb/migrations/',
    'datapunk/visualizations/',
    'datapunk/visualizations/migrations/',
    'docs/'
]

def list_files(startpath):
    startpath = os.path.abspath(startpath)  # Get absolute path of the start directory
    with open("project_structure.txt", "w") as f:
        for root, dirs, files in os.walk(startpath):
            # Get relative path for comparison
            rel_dir = os.path.relpath(root, startpath).replace('\\', '/') + '/'

            # Only include directories in the list of include_dirs
            if any(rel_dir.startswith(d) for d in include_dirs):
                # Exclude specific directories
                dirs[:] = [d for d in dirs if d not in ['__pycache__', 'venv', 'node_modules', '.git', 'datapunk-env']]
                
                level = rel_dir.count('/')
                indent = ' ' * 4 * level
                f.write(f'{indent}{os.path.basename(root)}/\n')

                subindent = ' ' * 4 * (level + 1)
                for file in files:
                    f.write(f'{subindent}{file}\n')

# Call the function
list_files('.')
