## Docker container(spools up frontend, backend and nginx using docker)

***If you need to install docker on linux use the shell file install-docker.. in the root directory (Mind the aws/ubu trails)***
  ```bash
   # To make file executable
   chmod +x install-docker-aws.sh

   # To run the shell file
   ./install-docker-aws.sh
   ```

***Initial Setup Only***
1. **Clone the base repo:f** [https://github.com/Cirrostrats/base](https://github.com/Cirrostrats/base)
2. **Navigate into this base repo folder**
3. **Ensure Docker Desktop is running in the background, esure python is installed on your system**
6. **Run the setup.py file from the base directory - `python3 setup.py`**
7. **follow instructions on terminal.**

***Subsequent Runs***
**You don't need to run `python setup.py` for subsequent runs. Just run docker compose up on the base directory and it should spool up the containers accordingly.**
