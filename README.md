## Spool up using docker compose:
Read through the DOCKER_COMPOSE_GUIDE markdown file for detailed instruction on how to compose for dev vs prod using different compose files

## Docker installation
***If you need to install docker on linux use the shell file install-docker.. in the root directory (Mind the aws/ubu trails)***
  ```bash
   # To make file executable
   chmod +x install-docker-aws.sh

   # To run the shell file
   ./install-docker-aws.sh
   ```

### Initial setup (one-time)

1. **Clone the base repo:** [https://github.com/Cirrostrats/base](https://github.com/Cirrostrats/base)
2. **Go into the base repo:** `cd base`
3. **Prerequisites:** Docker Desktop running, Python 3 and Git installed.
4. **Run setup from the base directory:**
   ```bash
   python3 setup.py
   ```
   - You’ll be asked which **branch** to use (default: `dev`). Press Enter for `dev` or type e.g. `main`.
   - Or pass the branch up front: `python3 setup.py -b dev`
   - The script clones **cirrostrats-frontend** and **cirrostrats-backend** (if missing), checks out the chosen branch, then creates **.env** from **.env.example** in each repo (if present).
   - It will open each **.env** in your editor so you can add secrets (API keys, MongoDB, etc.). You can choose **nano** or **vim** when prompted.
5. **Follow the prompts** in the terminal until setup finishes.

### Subsequent runs

You don’t need to run `python3 setup.py` again. From the base directory, bring up the stack with Docker Compose (see DOCKER_COMPOSE_GUIDE for dev vs prod):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```
