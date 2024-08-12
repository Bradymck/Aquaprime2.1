import subprocess
import os
import openai
import datetime

# Initialize OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_git_diff():
    result = subprocess.run(['git', 'diff', '--cached'], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()

def generate_commit_message(diff):
    prompt = f"Generate a commit message based on the following changes:\n{diff}\n\nCommit Message:"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

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

    # Commit the changes
    subprocess.run(['git', 'commit', '-m', commit_message])

    # Sync with the remote repository
    subprocess.run(['git', 'push'])

if __name__ == "__main__":
    main()