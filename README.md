# Moment Track

Moment Track wants to let users search text into audio and video files to know
when such text has been pronounced.

## Requirements

- Python 2.7
- Django 1.11
- MySQL-compliant DBMS (MySQL, MariaDB, …)

## Getting Started

Extract the `moment-track.tar.gz` archive and move to the project folder:

```bash
$ tar -zxvf moment-track.tar.gz
$ cd moment-track
```


### Build the documentation

Move to documentation folder and prepare the environment to run Sphinx:

```bash
$ cd docs
$ virtualenv2 venv
$ source venv/bin/activate
$ (venv) pip2 install -r requirements.txt
```

Build the documentation as PDF and/or HTML:

```bash
$ (venv) make      # with no parameters will show you all the available options
$ (venv) make html # documentation files will be located at "dist/html/"
$ (venv) make pdf  # documentation file will be located at "dist/manual.pdf"
```

### Setting up Google Cloud Platform environment

> If you want to deploy Moment Track on your server, please skip this section.
> It will not break your deployment, but it is just useless.

If you haven't already created a project in the Google Cloud Platform Console,
[create one](https://console.cloud.google.com/) now giving it the name you
prefer.

[Enable billing](https://console.cloud.google.com/project/_/settings) for
your project and sign up for a free trial if you haven't already a billing
account.

Install the Google Cloud SDK following [this guide](https://cloud.google.com/sdk/docs/)

Enable the required APIs:

- [Google Cloud SQL API](https://console.cloud.google.com/flows/enableapi?apiid=sqladmin.googleapis.com&showconfirmation=true "Click to automatically enable Google CLoud API for your project")
- [Google Speech API](https://console.cloud.google.com/flows/enableapi?apiid=speech.googleapis.com&showconfirmation=true "Click to automatically enable Google Speech API for your project")

Download and install the [Cloud SQL Proxy](https://cloud.google.com/sql/docs/sql-proxy "Click to learn more on Google Cloud SQL Proxy")
to connect to your Cloud SQL instance when running locally. You can follow the
more appropriate guide based on your operating system choosing from
[this table](https://cloud.google.com/python/django/appengine#install_the_sql_proxy).

[Create a Cloud SQL for MySQL Second Generation instance](https://cloud.google.com/sql/docs/mysql/create-instance).
Name the instance `moment_track` and wait until ready.

Now use the Cloud SDK from command line to run the following command. Copy the
`connectionName` value for the next step.

```bash
gcloud beta sql instances describe moment_track
```

Start the Cloud SQL Proxy using the `connectionName` from the previous step.

If you are using Linux or Unix-like operating system use:

```bash
./cloud_sql_proxy -instances="[YOUR_INSTANCE_CONNECTION_NAME]"=tcp:3306
```

If you are using Windows operating system use:

```
cloud_sql_proxy.exe -instances="[YOUR_INSTANCE_CONNECTION_NAME]"=tcp:3306
```

> From now you can follow the next section instructions to set up local
> environment and dependencies.

### Setting up your local environment

> If you intend to use this app in a local production environment, please look
> for the Django deploy how-to guide for your web server of use.
> For project specific dependencies you can use the `Requirements` section
> above and your preferred package manager.

Move to source folder:

```bash
$ cd src/
```

Create an isolated Python environment and install dependencies:

```bash
$ virtualenv2 venv
$ source venv/bin/activate
$ (venv) pip2 install -r requirements-vendor.txt -t lib/
$ (venv) pip2 install -r requirements.txt
```

Access MySQL console with a privileged user to create project user and
database:

```sql
$ mysql --host 127.0.0.1 --user root --password
mysql > CREATE DATABASE moment_track;
mysql > CREATE USER 'moment_track' IDENTIFIED BY 'moment_track';
mysql > GRANT ALL ON moment_track.* TO 'moment_track';
mysql > FLUSH PRIVILEGES;
```

Run the Django migrations to set up ORM models:

```bash
$ cd moment_track/
$ (venv) python2 manage.py makemigrations
$ (venv) python2 manage.py makemigrations website
$ (venv) python2 manage.py migrate
```

Copy static files to static root directory to let Django serves them even if
not in debug mode:

```bash
$ (venv) python2 manage.py collectstatic
```

### Run Django on local webserver

Start a local webserver from Django project folder:

```bash
$ (venv) python2 manage.py runsslserver 127.0.0.1 9000
```

You can view running instance of Moment Track with your preferred browser at
[https://127.0.0.1:9000](https://127.0.0.1:9000) address.

### Deploy on Google App Engine

Upload the app by running the following command from within the django project
directory (`<path-to-moment-track-root-folder>/src/moment_track`) where the
`app.yaml` file is located:

```bash
gcloud app deploy
```

Wait for the message that notifies you that the update has completed, then open
your preferred browser at the address `https://<your_project_id>.appspot.com`

> The `project id` could be retrieved in the
> [Google Cloud Console Dashboard](https://console.cloud.google.com/home/dashboard)
> looking for `Project information` card.

***

Copyright © 2017 Moment Track - Released under
[Proprietary Software License](LICENSE).

