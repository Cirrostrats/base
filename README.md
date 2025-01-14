
# Project README

### .env contents:
1. **Frontend .env file contents** - Paste the following inside of frontend's `.env` file.

    ```bash
        # .env (for local environment)
        VITE_API_URL=http://127.0.0.1:8000
        
        # .env (for production/AWS environment) Use this for production. Comment it out on local machine
        # VITE_API_URL=/api
        
        # Set it to true for returning test data on search - Good for efficient frontend dev. Set to false if requesting actual data.
        VITE_APP_TEST_FLIGHT_DATA=false
    ```

2. **Backend .env file contents** - Paste the following inside of the backend's `.env` file - replace connection string. 

    ```bash
    connection_string='***'
    env='development'         # Use this locally. Otherwise comment it out
    # env='production'          # Use this in production. Otherwise comment it out locally.
    ```

    ***Please reach out to me for access to mongodb connection string.***


## Docker container(spools up frontend, backend and nginx using docker)
***Initial Setup Only***
1. **Clone the base repo:f** [https://github.com/Cirrostrats/base](https://github.com/Cirrostrats/base)
2. **Navigate into this base repo folder**
3. **Ensure Docker Desktop is running in the background, esure python is installed on your system**
6. **Run the setup.py file from the base directory - `python3 setup.py`**
7. **follow instructions on terminal.**

***Subsequent Runs***
**You don't need to run `python setup.py` for subsequent runs. Just run docker compose up on the base directory and it should spool up the containers accordingly.**
