ninetofiver
===========

[![Build Status](https://travis-ci.org/kalmanolah/925r.svg?branch=master)](https://travis-ci.org/kalmanolah/925r)
[![Coverage Status](https://coveralls.io/repos/github/kalmanolah/925r/badge.svg?branch=master)](https://coveralls.io/github/kalmanolah/925r?branch=master)
[![GitHub issues](https://img.shields.io/github/issues/kalmanolah/925r.svg)](https://shields.io)
[![License](https://img.shields.io/github/license/kalmanolah/925r.svg)](https://shields.io)

ninetofiver (or 925r) is a free and open source time and leave tracking application.

## Installation

Install build dependencies:

```bash
apt-get install -y python-dev libldap2-dev libsasl2-dev libssl-dev
```

You'll need [pipenv](https://docs.pipenv.org/). Installing it is super simple:

```bash
pip install pipenv
```

After that, installing the application is smooth sailing:

```bash
pipenv install
```

Once your pipenv is set up, you can use `pipenv shell` to get a shell, or
just prefix additional commands with `pipenv run`.

## Usage

1. Run `python manage.py migrate` to create the models.

2. Run `python manage.py createsuperuser` to create an admin user

### Running (development)

Running the command below starts a development server at
`http://127.0.0.1:8000`.

```bash
python manage.py runserver
```

## Running (production)

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
tox
```

## License

See [LICENSE](LICENSE)

```
ninetofiver (925r): a free and open source time and leave tracking application.
Copyright (C) 2016-2019 Kalman Olah

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
