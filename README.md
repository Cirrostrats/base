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

***Initial Setup Only -- (outdated)***

1. **Clone the base repo:f** [https://github.com/Cirrostrats/base](https://github.com/Cirrostrats/base)
2. **Navigate into this base repo folder**
3. **Ensure Docker Desktop is running in the background, esure python is installed on your system**
6. **Run the setup.py file from the base directory - `python3 setup.py`**
7. **follow instructions on terminal.**

***Subsequent Runs***
**You don't need to run `python setup.py` for subsequent runs. Just run docker compose up on the base directory and it should spool up the containers accordingly.**
