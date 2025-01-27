from pathlib import Path
import os,sys
import subprocess

# repositories
frontend_repo = "https://github.com/ujazishere/cirrostrats-frontend.git"
backend_repo = "https://github.com/ujazishere/cirrostrats-backend.git"

def branch_work(repo_link, folder):

    """Clone repo and change to dev branch"""

    folder_path = os.path.join(os.getcwd(), folder)
    print("Currently attempting to work in folder_path path:", folder_path)

    folder_path_exists = os.path.exists(folder_path)

    # Clone repo if it does not exist
    if not folder_path_exists:      # if the folder is not there then clone it
        print(f"Cloning {folder} repo on your this machine...")
        subprocess.run(["git", "clone", repo_link, folder])          # if the folder is not there then clone it
    
    # Change to dev branch and fetch latest
    elif folder_path_exists:
        print(f"{folder} repo already exists on this machine")
        base_path = os.getcwd()
        print('Current working directory: ', os.getcwd())
        os.chdir(folder_path)
        print('updated cwd', os.getcwd())

        print('Attempting to change and track to dev branch...')
        dev_branch_check = subprocess.run(["git", "checkout", "-b", "dev", "origin/dev"],capture_output=True,text=True)
        if "fatal: a branch named 'dev' already exists" in dev_branch_check.stderr:
            subprocess.run(["git", "checkout", "dev"])
            subprocess.run(["git", "pull", "origin", "dev"])       # Pull the latest remote dev
        
        # Return back to base
        os.chdir(base_path)
        print("Finally updated cwd to: ", os.getcwd())


branch_work(repo_link=frontend_repo, folder="cirrostrats-frontend")
branch_work(repo_link=backend_repo, folder="cirrostrats-backend")

input("***Attention: You will have to create .env files as follows:(press enter to continue...)\n")

input("create .env file for frontend ./cirrostrats-frontend/.env for React and include appropriate variables(press enter once done...)\n")
check_for_env_frontend = Path("./cirrostrats-frontend/.env").exists()
if not check_for_env_frontend:
    input("***Caution the file ./cirrostrats-frontend/.env does not exist - code may break. Press enter to continue without it...")

input("create .env file for backend ./cirrostrats-backend/.env for MongoDB and local work(press enter once done...)\n")
check_for_env_backend = Path("./cirrostrats-backend/.env").exists()
if not check_for_env_backend:
    input("***Caution** the file ./cirrostrats-backend/.env does not exist - code may break. Press enter to continue without it...")

# Start Docker Compose
type_of_env = input("Starting Docker Compose. Is this for developement? (y/n) ")

# For production
if type_of_env == "n":
    subprocess.run(["docker", "compose", "--profile", "production", "up", "--build"])

# For development
else:
    print('Starting Docker Compose for development...')
    subprocess.run(["docker", "compose", "up"])