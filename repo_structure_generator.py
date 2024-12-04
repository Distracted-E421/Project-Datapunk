#!/usr/bin/env python3

import os
from pathlib import Path
import datetime

# Directories and files to ignore
IGNORE_PATTERNS = {
    '__pycache__',
    'node_modules',
    '.git',
    '.pytest_cache',
    '.coverage',
    '.env',
    '.venv',
    'venv',
    'dist',
    'build',
    '.DS_Store',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.Python',
    '*.so'
}

def should_ignore(path):
    """Check if the path should be ignored."""
    return any(pattern in str(path) for pattern in IGNORE_PATTERNS)

def get_file_info(file_path):
    """Get file information including size and line count."""
    try:
        size = os.path.getsize(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        return size, line_count
    except (IOError, UnicodeDecodeError):
        return os.path.getsize(file_path), 0

def format_size(size):
    """Format size in bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

def generate_tree(start_path='.'):
    """Generate tree structure of the repository."""
    bash_tree = []
    human_tree = []
    
    for root, dirs, files in os.walk(start_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]
        
        if should_ignore(root):
            continue
            
        level = root.replace(start_path, '').count(os.sep)
        indent = '  ' * level
        bash_indent = '│   ' * level
        
        # Add directory
        rel_path = os.path.relpath(root, start_path)
        if rel_path != '.':
            bash_tree.append(f"{bash_indent}├── {os.path.basename(root)}/")
            human_tree.append(f"{indent}- **{os.path.basename(root)}/**")
        
        # Add files
        for file in sorted(files):
            if should_ignore(os.path.join(root, file)):
                continue
                
            file_path = os.path.join(root, file)
            size, line_count = get_file_info(file_path)
            
            bash_tree.append(f"{bash_indent}│   ├── {file} ({format_size(size)}, {line_count} lines)")
            human_tree.append(f"{indent}  - {file} ({format_size(size)}, {line_count} lines)")
    
    return bash_tree, human_tree

def generate_markdown():
    """Generate markdown file with repository structure."""
    bash_tree, human_tree = generate_tree()
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    bash_view = '\n'.join(['.']+bash_tree)
    human_view = '\n'.join(human_tree)
    ignored_patterns = ', '.join(sorted(IGNORE_PATTERNS))
    
    markdown_content = f"""# Repository Structure Overview
Generated on: {timestamp}

## Bash-style Tree View
```bash
{bash_view}
```

## Human Readable Structure
{human_view}

## Notes
- Sizes are shown in bytes (B), kilobytes (KB), megabytes (MB), or gigabytes (GB)
- Line counts are shown for text files only
- The following patterns were ignored: {ignored_patterns}
"""
    
    # Write to file
    with open('REPOSITORY_STRUCTURE.md', 'w', encoding='utf-8') as f:
        f.write(markdown_content)

if __name__ == '__main__':
    generate_markdown()
    print("Repository structure has been generated in REPOSITORY_STRUCTURE.md") 