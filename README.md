# loxprox

*Experimental*: Proxies Loxone UDP data frames containing "Lumitech DMX" information to Philips Hue. Expect at least some changes in the config file format. Software is provided as is, no warranty.

More input types will be added in the future to include additional data like readings from the Energy Meter.

## Docker

### Server configuration
The sample configuration can be found in the directory 'config.in'. Make a local copy and adjust accordingly to be safe from future upstream changes.

```sh
cp -r config.in config
```

### Docker Compose

Rename docker-compose.yml.in to docker-compose.yml and edit the files to your liking. Especially the ports and volumes need to be adjusted to your needs.

```sh
cp docker-compose.yml.in docker-compose.yml
```

Edit the `docker-compose.yml` file to your liking and run:

```sh
docker compose up -d
```

## Logs
The server process is started with supervisord. Logs can be found in the directory 'config/log/'. Supervisor is also providing a webinterface on port 52080 in my default config. Username and password are 'loxprox:loxone'. The logs have unfurtunately a delay for some reason.

