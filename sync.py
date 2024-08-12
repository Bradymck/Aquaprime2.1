import subprocess
import os
import webbrowser
import threading
from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)

def get_git_diff():
    """Get the diff of the staged changes."""
    result = subprocess.run(['git', 'diff', '--cached'], stdout=subprocess.PIPE, text=True, encoding='utf-8')
    return result.stdout.strip()


def generate_commit_message(diff):
    """Generate a commit message based on the provided git diff."""
    # Your OpenAI logic here or any other commit message generation logic
    return "Your AI-generated commit message"

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

def open_cursor_browser():
    # Open the URL in Cursor's Simple Browser (if it supports VSCode URI scheme)
    cursor_url = "vscode://vscode-webview/open?url=http://localhost:5000"
    webbrowser.open(cursor_url)

if __name__ == "__main__":
    # Start the Flask server and open it in Cursor's internal browser
    threading.Timer(1, open_cursor_browser).start()
    app.run(host='0.0.0.0', port=5000)
