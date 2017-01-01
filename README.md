ninetofiver
===========

[![Build Status](https://travis-ci.org/kalmanolah/925r.svg?branch=master)](https://travis-ci.org/kalmanolah/925r)
[![Coverage Status](https://coveralls.io/repos/github/kalmanolah/925r/badge.svg?branch=master)](https://coveralls.io/github/kalmanolah/925r?branch=master)
[![Documentation Status](https://readthedocs.org/projects/925r/badge/?version=latest)](http://925r.readthedocs.io/en/latest/?badge=latest)
[![GitHub issues](https://img.shields.io/github/issues/kalmanolah/925r.svg)](https://shields.io)
[![license](https://img.shields.io/github/license/kalmanolah/925r.svg)](https://shields.io)

ninetofiver (or 925r) is a free and open source time and leave tracking application.

## Installation

Create and activate a virtual environment:

```bash
python3 -m virtualenv -p python3 ninetofiver_venv
source ninetofiver_venv/bin/activate
```

Install build dependencies:

```bash
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

```bash
docker-compose -f ./scripts/docker/docker-compose.yml up
```

### Running (development)

Running the command below starts a development server at
`http://127.0.0.1:8000`.

```bash
python manage.py runserver
```

## Running in production

Running the command below starts a server using the production configuration
at `http://127.0.0.1:8000`.

Note: The `insecure` flag is used to allow the server to serve static files.

```bash
python manage.py runserver --configuration=Prod --insecure
```

## Configuration

Since this application is built using Django, you can configure the settings
which will be loaded using the environment variables `DJANGO_SETTINGS_MODULE`
(defaulting to `ninetofiver.settings`) and `DJANGO_CONFIGURATION` (defaulting
to `Dev`).

The application will also attempt to load a YAML configuration file from a
location specified using the environment variable `CFG_FILE_PATH` (defaulting
to `/etc/925r/config.yml`) and use the resulting data to override existing
settings.

For example, if you wanted to override the secret key used for production you
could use the following configuration:

```yaml
# Use your own secret key!
SECRET_KEY: mae3fo4dooJaiteth2emeaNga1biey9ia8FaiQuooYoac8phohee7r
```

## Testing

Run the test suite:

```bash
python manage.py testninetofiver
```

## Documentation

Generate the docs:

```bash
pip install sphinx
sphinx-apidoc -e -f -a -d 2 -o docs ninetofiver ninetofiver/migrations
cd docs && make html && cd ../
```

## License

See [LICENSE](LICENSE)

```
ninetofiver (925r): a free and open source time and leave tracking application.
Copyright (C) 2016 Kalman Olah

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
