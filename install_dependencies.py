import subprocess
import openai
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

def run_command(command):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        handle_error(e)

def handle_error(error):
    error_message = str(error)
    print(f"Error captured: {error_message}")
    
    # Use OpenAI to process the error message
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Given the following error message, suggest the appropriate Python package to install:\n\n{error_message}\n\n",
        max_tokens=50
    )
    
    suggestion = response.choices[0].text.strip()
    print(f"Suggested package: {suggestion}")
    
    # Install the suggested package
    install_package(suggestion)

def install_package(package):
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        print(f"Successfully installed {package}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")

if __name__ == "__main__":
    # Example command that might fail due to a missing module
    run_command([sys.executable, "main.py"])