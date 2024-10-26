import os  

def print_directory_tree(start_path, output_file="current_directory_structure.txt"):
    with open(output_file, "w") as f:
        for root, dirs, files in os.walk(start_path):
            level = root.replace(start_path, '').count(os.sep)
            indent = ' ' * 4 * level
            f.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                f.write(f"{sub_indent}{file}\n")

if __name__ == "__main__":
    current_directory = os.getcwd()
    print_directory_tree(current_directory)
    print("Directory structure saved to directory_structure.txt")