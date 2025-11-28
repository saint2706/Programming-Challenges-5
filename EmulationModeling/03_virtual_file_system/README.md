# Virtual File System

An in-memory file system implementation with Unix-like shell interface supporting standard file operations and persistence.

## 📋 Table of Contents

- [Theory](#theory)
- [Installation](#installation)
- [Usage](#usage)
- [Commands](#commands)

## 🧠 Theory

### File System Structure

A hierarchical file system with:

- **Nodes**: Abstract base for files and directories
- **Files**: Store text content
- **Directories**: Container for files and subdirectories
- **Tree Structure**: Root node with parent/child relationships

### Path Resolution

- **Absolute paths**: Start with `/` from root
- **Relative paths**: Start from current working directory
- **Path traversal**: Support for `.` (current) and `..` (parent)

## 💻 Installation

Requires Python 3.8+ (no external dependencies):

```bash
cd EmulationModeling/03_virtual_file_system
python shell.py
```

## 🚀 Usage

### Starting the Shell

```bash
python shell.py
```

You'll see an interactive prompt:

```
Virtual File System initialized. Type 'help' for commands.
[/] $
```

## 📝 Commands

### File Operations

```bash
# Create an empty file or update with content (custom implementation)
# Note: Unlike Unix touch, this supports inline content as second argument
touch myfile.txt "Hello, World!"

# Read file contents
cat myfile.txt

# Remove file or directory
rm myfile.txt
```

### Directory Operations

```bash
# List directory contents
ls
ls /path/to/dir

# Create directory
mkdir projects

# Change directory
cd projects
cd ..
cd /

# Show current directory
pwd
```

### Persistence

```bash
# Save file system to disk
save fs_snapshot.json

# Load file system from disk
load fs_snapshot.json

# Exit shell
exit
```

## ✨ Features

- Complete in-memory file system
- Unix-like command interface
- Serialization/deserialization to JSON
- Support for nested directories
- Relative and absolute path navigation
