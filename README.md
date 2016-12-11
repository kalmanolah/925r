ninetofiver
===========

ninetofiver (or 925r) is a free and open source time and leave tracking application.

## Installation

Create and activate a virtual environment:

```
python3 -m virtualenv -p python3 ../ninetofiver_venv
source ../ninetofiver_venv/bin/activate
```

Install build dependencies:

```
apt-get install -y python-dev libldap2-dev libsasl2-dev libssl-dev
```

Install the application:

```
python setup.py install
pip install -r requirements.txt
```

## Usage

1. Run `python manage.py migrate` to create the models.

2. Run `python manage.py createsuperuser` to create an admin user

### Running (Docker)

Running the command below starts linked docker containers
running OpenLDAP and ninetofiver at `http://127.0.0.1:8888`.
You may need to install docker and docker-compose first.

```
docker-compose -f ./scripts/docker/docker-compose.yml up
```

### Running (development)

Running the command below starts a development server at
`http://127.0.0.1:8000`.

```
python manage.py runserver
```

## Running in production

Running the command below starts a server using the production configuration
at `http://127.0.0.1:8000`.

Note: The `insecure` flag is used to allow the server to serve static files.

```
python manage.py runserver --configuration=Prod --insecure
```

## License

See [LICENSE](LICENSE)
