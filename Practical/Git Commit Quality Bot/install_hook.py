import os
import sys
import stat

def install_hook():
    git_dir = os.path.join(os.getcwd(), '.git')
    if not os.path.exists(git_dir):
        # Try to find .git in parent directories
        current_dir = os.getcwd()
        while current_dir != os.path.dirname(current_dir):
            if os.path.exists(os.path.join(current_dir, '.git')):
                git_dir = os.path.join(current_dir, '.git')
                break
            current_dir = os.path.dirname(current_dir)
        
        if not os.path.exists(git_dir):
            print("Error: Not a git repository (or any of the parent directories).")
            sys.exit(1)

    hooks_dir = os.path.join(git_dir, 'hooks')
    hook_path = os.path.join(hooks_dir, 'commit-msg')
    
    # Path to the validator script
    # Assuming the validator script is in the same directory as this installer
    validator_script = os.path.abspath(os.path.join(os.path.dirname(__file__), 'commit_check.py'))
    
    # Create the hook script
    # On Windows, we might need a slightly different approach if using Git Bash vs PowerShell,
    # but a python call usually works if python is in PATH.
    hook_content = f"""#!/bin/sh
python "{validator_script}" "$1"
"""

    try:
        with open(hook_path, 'w') as f:
            f.write(hook_content)
        
        # Make it executable
        st = os.stat(hook_path)
        os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
        
        print(f"Hook installed successfully at {hook_path}")
        print(f"It will run: python \"{validator_script}\"")
    except Exception as e:
        print(f"Error installing hook: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_hook()
