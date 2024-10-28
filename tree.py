#!/usr/bin/env python3

import os
import sys
from datetime import datetime

def get_first_line(file_path):
    """Get first line of file if it's readable text"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            
            # Handle common comment styles
            for marker in ['#', '//', '--', '/*']:
                if first_line.startswith(marker):
                    return first_line.lstrip(marker).strip()
            
            # For md/txt files, return first line
            if file_path.lower().endswith(('.md', '.txt')):
                return first_line
                
        return None
    except:
        return None

def should_skip(name):
    """Check if file/directory should be skipped"""
    skip_list = {
        'node_modules', 'venv', 'env', '.git', '__pycache__',
        '.env', '.vscode', 'build', 'dist', '.next'
    }
    return any(pattern in name for pattern in skip_list)

def get_file_info(path):
    """Get file size and description"""
    size = os.path.getsize(path)
    size_str = "empty" if size == 0 else (
        f"{size} bytes" if size < 1024 else
        f"{size/1024:.1f} KB" if size < 1024 * 1024 else
        f"{size/(1024*1024):.1f} MB"
    )
    
    description = get_first_line(path)
    return f"{size_str} - {description}" if description else size_str

def generate_tree(directory, output_lines=None, prefix="", level=0):
    """Generate directory tree lines"""
    if output_lines is None:
        output_lines = []
    
    if level == 0:
        output_lines.append(f"📁 {os.path.basename(directory)}")
    
    try:
        entries = sorted(os.scandir(directory), key=lambda e: (not e.is_dir(), e.name))
        
        for i, entry in enumerate(entries):
            if should_skip(entry.name):
                continue
                
            is_last = i == len(entries) - 1
            connector = "└──" if is_last else "├──"
            
            if entry.is_dir():
                output_lines.append(f"{prefix}{connector} 📁 {entry.name}/")
                next_prefix = prefix + ("    " if is_last else "│   ")
                generate_tree(entry.path, output_lines, next_prefix, level + 1)
            else:
                file_info = get_file_info(entry.path)
                output_lines.append(f"{prefix}{connector} 📄 {entry.name} ({file_info})")
                
    except PermissionError:
        output_lines.append(f"{prefix}└── ⚠️  Permission denied")
    
    return output_lines

if __name__ == "__main__":
    path = "." if len(sys.argv) < 2 else sys.argv[1]
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"directory_tree_{timestamp}.txt"
    
    # Generate tree content
    header = [
        "Directory Tree",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Root: {os.path.abspath(path)}",
        "=" * 50,
        ""
    ]
    
    tree_content = generate_tree(path)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(header + tree_content))
    
    print(f"\nDirectory tree has been saved to: {output_file}")
