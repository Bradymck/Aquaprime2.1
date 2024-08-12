import subprocess
import os
import openai
import threading
from flask import Flask, render_template_string, redirect, url_for

# Initialize OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

def get_git_diff():
    """Get the diff of the staged changes."""
    result = subprocess.run(['git', 'diff', '--cached'], stdout=subprocess.PIPE, text=True, encoding='utf-8')
    return result.stdout.strip()

def generate_commit_message(diff):
    """Generate a commit message based on the provided git diff."""
    prompt = f"Generate a clear and concise git commit message based on the following changes:\n{diff}\n\nCommit Message:"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant skilled in generating commit messages."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    
    except openai.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return "Failed to generate commit message."

def sync_code():
    # Stage all changes
    subprocess.run(['git', 'add', '.'])

    # Get the diff of the staged changes
    diff = get_git_diff()

    if not diff:
        print("No changes to commit.")
        return "No changes to commit."

    commit_message = generate_commit_message(diff)

    if commit_message:
        print("Generated commit message:")
        print(commit_message)
        subprocess.run(['git', 'commit', '-m', commit_message])
        subprocess.run(['git', 'push'])
        return f"Commit Successful: {commit_message}"
    else:
        return "Failed to generate commit message."

@app.route('/')
def index():
    return render_template_string('''
        <h1>Sync Code to Git</h1>
        <form action="/sync" method="post">
            <button type="submit">Sync Now</button>
        </form>
    ''')

@app.route('/sync', methods=['POST'])
def sync():
    message = sync_code()
    return redirect(url_for('index', message=message))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
