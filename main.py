import argparse
import os
import hashlib
import shutil
import time
import difflib

def initialize_project(project_dir):
    try:
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        svcs_dir = os.path.join(project_dir, '.svcs')
        if not os.path.exists(svcs_dir):
            os.makedirs(svcs_dir)
            
            with open(os.path.join(svcs_dir, 'config.txt'), 'w') as config_file:
                config_file.write("username: user\nignored_files: []")
            
            with open(os.path.join(svcs_dir, 'index.txt'), 'w') as index_file:
                index_file.write("")  

            os.makedirs(os.path.join(svcs_dir, 'versions'))
            
            print(f"Project initialized in {project_dir}")
        else:
            print(f"Project already initialized in {project_dir}")
    except OSError as e:
        print(f"Error intializing project: {e}")


def sha256(file_path): 
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192): #This reads up to 8192 bytes (8 KB) of the file at a time.
            sha256.update(chunk)
    return sha256.hexdigest()

def add_item(project_dir, item_path):
    svcs_dir = os.path.join(project_dir, '.svcs')
    index_file = os.path.join(svcs_dir, 'index.txt')

    # TODO: check if the item_path is a sub part of project_dir

    if not os.path.exists(item_path):
        print(f"Error: {item_path} does not exist.")
        return
    
    if os.path.isfile(item_path):
        file_hash = sha256(item_path)
        with open(index_file, 'a') as f:
            f.write(f"{item_path} {file_hash}\n")
        print(f"Added {item_path} to version control.")
    else:
        print("Error: Only files can be added.")

def create_version(project_dir, commit_message):
    # Get the .svcs directory
    svcs_dir = os.path.join(project_dir, '.svcs')
    
    # List all version directories (v1, v2, etc.)
    versions_dir = os.path.join(svcs_dir, 'versions')
    version_dirs = sorted([d for d in os.listdir(versions_dir) if d.startswith('v')], key=lambda x: int(x[1:]))
    
    # Calculate the new version number (next available)
    new_version_number = len(version_dirs) + 1
    new_version_dir = os.path.join(versions_dir, f'v{new_version_number}')
    
    # Create the new version directory
    os.makedirs(new_version_dir)
    
    # Copy files from the index.txt to the new version directory using hard links or copies
    index_file = os.path.join(svcs_dir, 'index.txt')
    
    with open(index_file, 'r') as f:
        files_to_add = f.readlines()
    
    file_hashes = []
    
    for file_path in files_to_add:
        file_path = file_path.strip()
        full_file_path = os.path.join(project_dir, file_path)
        
        if os.path.isfile(full_file_path):
            # Use hard link or copy file (depending on OS and requirements)
            new_file_path = os.path.join(new_version_dir, file_path)
            os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
            shutil.copy2(full_file_path, new_file_path)
            
            # Store file hash
            file_hash = sha256(full_file_path)
            file_hashes.append(file_hash)
    
    # Store the version metadata
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    version_history_file = os.path.join(new_version_dir, 'history.txt')
    
    with open(version_history_file, 'w') as history_file:
        history_file.write(f"Version: v{new_version_number}\n")
        history_file.write(f"Commit Message: {commit_message}\n")
        history_file.write(f"Timestamp: {timestamp}\n")
        history_file.write(f"Files: {', '.join(file_hashes)}\n")
    
    print(f"New version created: v{new_version_number}")


def list_versions(project_dir):
    svcs_dir = os.path.join(project_dir, '.svcs')
    versions_dir = os.path.join(svcs_dir, 'versions')
    
    version_dirs = sorted([d for d in os.listdir(versions_dir) if d.startswith('v')], key=lambda x: int(x[1:]))
    
    print("Available versions:")
    
    for version_dir in version_dirs:
        history_file_path = os.path.join(versions_dir, version_dir, 'history.txt')
        
        with open(history_file_path, 'r') as history_file:
            lines = history_file.readlines()
            version_info = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in lines}
            
            print(f"Version {version_info['Version']}: {version_info['Commit Message']} ({version_info['Timestamp']})")


def restore_version(project_dir, version):
    svcs_dir = os.path.join(project_dir, '.svcs')
    versions_dir = os.path.join(svcs_dir, 'versions')
    
    # Find the version directory to restore
    version_dir = os.path.join(versions_dir, version)
    if not os.path.exists(version_dir):
        print(f"Version {version} not found!")
        return
    
    # Get the history file for the version
    history_file_path = os.path.join(version_dir, 'history.txt')
    
    # Delete all files in the project directory, except .svcs
    for root, dirs, files in os.walk(project_dir):
        if root == svcs_dir:
            continue  # Skip .svcs directory
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            shutil.rmtree(os.path.join(root, dir))
    
    # Copy the files from the selected version back to the project directory
    with open(history_file_path, 'r') as history_file:
        lines = history_file.readlines()
        file_hashes = lines[3].strip().split(": ")[1].split(", ")
        
        for file_hash in file_hashes:
            # Find and copy the file from the version directory
            for file in os.listdir(version_dir):
                if sha256(file) == file_hash:
                    src_file = os.path.join(version_dir, file)
                    dest_file = os.path.join(project_dir, file)
                    shutil.copy2(src_file, dest_file)
    
    print(f"Project restored to version {version}")


def show_diff(project_dir, version1, version2):
    svcs_dir = os.path.join(project_dir, '.svcs')
    versions_dir = os.path.join(svcs_dir, 'versions')
    
    # Find the version directories to compare
    version_dir_1 = os.path.join(versions_dir, version1)
    version_dir_2 = os.path.join(versions_dir, version2)
    
    if not os.path.exists(version_dir_1) or not os.path.exists(version_dir_2):
        print(f"One or both versions not found!")
        return
    
    # Compare all files in both versions
    version_1_files = os.listdir(version_dir_1)
    version_2_files = os.listdir(version_dir_2)
    
    for file in set(version_1_files + version_2_files):
        file1_path = os.path.join(version_dir_1, file)
        file2_path = os.path.join(version_dir_2, file)
        
        if os.path.exists(file1_path) and os.path.exists(file2_path):
            # Perform a line-by-line diff between the two versions of the file
            with open(file1_path, 'r') as f1, open(file2_path, 'r') as f2:
                diff = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile=file1_path, tofile=file2_path)
                for line in diff:
                    print(line)
        elif os.path.exists(file1_path):
            print(f"File {file} exists only in version {version1}")
        elif os.path.exists(file2_path):
            print(f"File {file} exists only in version {version2}")


def display_menu():
    while True:
        print("\n--- Simplified Version Control System (SVCS) ---")
        print("1. Initialize Project")
        print("2. Add Item")
        print("3. Create Version")
        print("4. List Versions")
        print("5. Restore Version")
        print("6. Show Diff Between Versions")
        print("7. Exit")

        choice = input("Enter your choice (1-7): ")

        if choice == '1':
            project_dir = input("Enter the project directory path: ")
            initialize_project(project_dir)
        
        elif choice == '2':
            project_dir = input("Enter the project directory path: ")
            item_path = input("Enter the file or directory path to add: ")
            add_item(project_dir, item_path)
        
        elif choice == '3':
            project_dir = input("Enter the project directory path: ")
            commit_message = input("Enter commit message: ")
            create_version(project_dir, commit_message)
        
        elif choice == '4':
            project_dir = input("Enter the project directory path: ")
            list_versions(project_dir)
        
        elif choice == '5':
            project_dir = input("Enter the project directory path: ")
            version = input("Enter version number to restore: ")
            restore_version(project_dir, version)
        
        elif choice == '6':
            project_dir = input("Enter the project directory path: ")
            version1 = input("Enter the first version number: ")
            version2 = input("Enter the second version number: ")
            show_diff(project_dir, version1, version2)
        
        elif choice == '7':
            print("Exiting the program.")
            break
        
        else:
            print("Invalid choice. Please enter a number between 1 and 7.")

if __name__ == "__main__":
    display_menu()