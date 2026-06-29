

# Spaceship DDNS

This is a single (dockerized) Python 3 script to update the main IP address of a domain registered with [Spaceship](https://www.spaceship.com/).

Please note that it will only work for domains with less than 500 DNS records. I have not bothered to handle pagination for now.


## Usage


### CLI interface

To use the CLI interface you first have to install the dependencies as follows:

```bash
pip install -r requirements.txt
```

Then, you can either run the script using command line arguments.

```bash
python3 ./spaceship_ddns.py -d domain-name -k api-key -s api-secret -i 5
# Help available with `python3 -h ./spaceship_ddns.py`
```

The `-i` (or `--interval`) flag sets the update interval in minutes. Omit it to run once and exit.

Alternatively, you can set up the `SPACESHIP_DDNS_DOMAIN`, `SPACESHIP_DDNS_API_KEY` and `SPACESHIP_DDNS_API_SECRET` environment variables and run the script without arguments.


### Docker compose

Create a new empty .env file with the following environment variables:

```
SPACESHIP_DDNS_DOMAIN=YourDomainHere
SPACESHIP_DDNS_API_KEY=YourApiKeyHere
SPACESHIP_DDNS_API_SECRET=YourApiSecretHere
SPACESHIP_DDNS_INTERVAL=5
```

The `SPACESHIP_DDNS_INTERVAL` is optional. If set, the script will run in a loop, updating every N minutes. Omit it to run once and exit.

Then you can run the container with a single command.

```bash
docker compose up
```


## References

  - [API docs](https://docs.spaceship.dev/#tag/DNS-records/operation/saveRecords)
