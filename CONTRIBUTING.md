# Contributors

## Special thanks for all the people who have helped this project so far:

* [Simon Mathis](https://github.com/Croydon-Brixton)
* [Martin Buttenschön](https://github.com/maabuu)

## I would like to join this list. How can I help the project?

We always welcome contributions to improve the project. Please have a look at the current github issues for information on where help could be needed.

### Getting set up:
The development environment for pymol-remote is detailed in the [`environment.yml` file](environment.yml).

For simplicity, you can set up the development environment using the `contribute.sh` script:

```bash
# NOTE: If you wish to use a different package manager than conda/etc. you can manually install the dependencies and set the .env file
./contribute.sh
```

You can then set the environment variables such as your localhosts's IP address in the `.env` file. Do not commit this file to github.

### Running the tests

To run the tests, you can use

```bash
# Run all tests
pytest tests/

# Run only the tests that do not require a running server
pytest tests/ -m "not requires_server"

# Run only the tests that do not require biotite on the client side
pytest tests/ -m "not client_requires_biotite"

```

### Test Categories

The test suite uses pytest markers to organize tests:

- `requires_server`: Tests that need a running PyMOL server
- `client_requires_biotite`: Tests that need biotite installed on the client side
