import subprocess

def get_git_diff():
    """Get the diff of the staged changes."""
    result = subprocess.run(['git', 'diff', '--cached'], stdout=subprocess.PIPE, text=True, encoding='utf-8')
    return result.stdout.strip()

def generate_commit_message():
    """Generate a basic commit message."""
    return "Version update: code changes committed."

def sync_code():
    # Stage all changes
    subprocess.run(['git', 'add', '.'])

    # Get the diff of the staged changes (optional)
    diff = get_git_diff()

    if not diff:
        print("No changes to commit.")
        return "No changes to commit."

    # Generate a simple commit message
    commit_message = generate_commit_message()

    if commit_message:
        print("Generated commit message:")
        print(commit_message)
        subprocess.run(['git', 'commit', '-m', commit_message])
        subprocess.run(['git', 'push'])
        return f"Commit Successful: {commit_message}"
    else:
        return "Failed to generate commit message."

if __name__ == "__main__":
    result = sync_code()
    print(result)
