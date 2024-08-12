import subprocess
import os
import openai
import datetime

# Initialize OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_git_diff():
    """Get the diff of the staged changes."""
    result = subprocess.run(['git', 'diff', '--cached'], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()

def generate_commit_message(diff):
    """Generate a commit message based on the provided git diff."""
    prompt = f"Generate a commit message based on the following changes:\n{diff}\n\nCommit Message:"

    # Make the API call to OpenAI's ChatCompletion
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},  # Optional context
            {"role": "user", "content": prompt}
        ]
    )

    # Extract and return the message content from the response
    return response['choices'][0]['message']['content'].strip()

def main():
    # Stage all changes
    subprocess.run(['git', 'add', '.'])

    # Get the diff of the staged changes
    diff = get_git_diff()

    if not diff:
        print("No changes to commit.")
        return

    # Generate commit message using AI
    commit_message = generate_commit_message(diff)
    print("Generated commit message:")
    print(commit_message)

    # Commit the changes using the generated commit message
    subprocess.run(['git', 'commit', '-m', commit_message])

    # Sync with the remote repository
    subprocess.run(['git', 'push'])

if __name__ == "__main__":
    main()