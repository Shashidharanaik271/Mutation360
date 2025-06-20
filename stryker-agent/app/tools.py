import os
import subprocess
import requests
from langchain_core.tools import tool

@tool
def read_file(file_path: str) -> str:
    """Reads the entire content of a file."""
    with open(os.path.join("/repo", file_path), "r") as f:
        return f.read()

@tool
def write_file(file_path: str, content: str):
    """Writes content to a file, overwriting it."""
    with open(os.path.join("/repo", file_path), "w") as f:
        f.write(content)
    return f"Successfully wrote to {file_path}"

@tool
def find_test_file(source_file_path: str) -> str | None:
    """
    Finds the corresponding test file for a given C# source file.
    It checks for both [FileName]Tests.cs and [FileName]Test.cs conventions.
    """
    filename = os.path.basename(source_file_path).replace(".cs", "")
    
    # Create a list of possible test filenames
    possible_test_filenames = [
        f"{filename}Tests.cs",
        f"{filename}Test.cs"
    ]

    for root, _, files in os.walk("/repo/"):
        for test_filename in possible_test_filenames:
            if test_filename in files:
                # Found a match, return its path
                return os.path.relpath(os.path.join(root, test_filename), "/repo")
                
    # If we searched for all possibilities and found nothing, return None
    return None

class GitTool:
    @staticmethod
    @tool
    def create_and_checkout_branch(branch_name: str):
        """Creates and checks out a new git branch. If the branch already exists, it just checks it out."""
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd="/repo", check=True, capture_output=True, text=True
            )
            return f"Created and checked out new branch: {branch_name}"
        except subprocess.CalledProcessError as e:
            if "already exists" in e.stderr:
                print(f"INFO: Branch '{branch_name}' already exists. Checking it out.")
                subprocess.run(["git", "checkout", branch_name], cwd="/repo", check=True)
                return f"Checked out existing branch: {branch_name}"
            else:
                print(f"ERROR: An unexpected git error occurred during checkout:\n{e.stderr}")
                raise e

    @staticmethod
    @tool
    def add_commit_and_push(branch_name: str, commit_message: str):
        """Adds all changes, commits them, and pushes the branch to origin after authenticating."""
        print(f"--- GitTool: Committing and preparing to push to branch '{branch_name}' ---")
        
        # Reconfigure the remote URL to include the GITHUB_TOKEN for authentication
        print("--- GitTool: Reconfiguring remote for authentication ---")
        token = os.environ["GITHUB_TOKEN"]
        repo_slug = os.environ["GITHUB_REPOSITORY"]
        authenticated_url = f"https://oauth2:{token}@github.com/{repo_slug}.git"
        subprocess.run(["git", "remote", "set-url", "origin", authenticated_url], cwd="/repo", check=True)
        print("--- GitTool: Remote URL configured for push. ---")

        subprocess.run(["git", "add", "."], cwd="/repo", check=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd="/repo", check=True)
        
        print(f"--- GitTool: Pushing to origin/{branch_name} ---")
        subprocess.run(["git", "push", "-u", "origin", branch_name], cwd="/repo", check=True)
        
        return "Changes committed and pushed."

class GitHubApiTool:
    def __init__(self, repo_slug: str, token: str):
        self.repo_slug = repo_slug
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    @tool
    def create_pull_request(self, head_branch: str, base_branch: str, title: str, body: str) -> str:
        """Creates a pull request on GitHub."""
        url = f"https://api.github.com/repos/{self.repo_slug}/pulls"
        data = { "title": title, "head": head_branch, "base": base_branch, "body": body }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()["html_url"]
