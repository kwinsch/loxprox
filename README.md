# loxprox

*Experimental*: Proxies Loxone UDP data frames containing "Lumitech DMX" information to Philips Hue. Expect at least some changes in the config file format. Software is provided as is, no warranty.

More input types will be added in the future to include additional data like readings from the Energy Meter.

## Docker

### Server configuration
The sample configuration can be found in the directory 'config.in'. Make a local copy and adjust accordingly to be safe from future upstream changes.

'''sh
cp -r config.in config
'''

### Docker Compose

Rename docker-compose.yml.in to docker-compose.yml and edit the files to your liking. Especially the ports and volumes need to be adjusted to your needs.

'''sh
cp docker-compose.yml.in docker-compose.yml
'''

Edit the `docker-compose.yml` file to your liking and run:

'''
docker compose up -d
'''

