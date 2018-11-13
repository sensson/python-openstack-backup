# OpenStack CLI backup tools

This repository contains a few useful tools to manage your instances on
OpenStack. It was written to support our backup needs in an environment
created to run volatile services.

WARNING: we use snapshots as a way to create crash consistent backups. These
backups may not include all data. Any data not `sync`'d to disk may be lost.

Read more about [crash consistent vs. application consistent](https://searchdatabackup.techtarget.com/answer/Crash-consistent-vs-application-consistent-backups-of-virtual-machines).

# Installation

Configure your OpenStack cloud(s). The example and default is based on [Fuga](https://fuga.cloud/).

- Copy `clouds.yaml.example` to `clouds.yaml` and fill in your details.
- Copy `secure.yaml.example` to `secure.yaml` and fill in your password.

We suggest you run this from a virtualenv.

```
virtualenv -p python3 env
. env/bin/activate
pip install -r requirements.txt
```

# Backup

```
./snapshot.py
```

This takes two optional arguments:

- `--include` can be used to specify servers that you want to include. Specify
  multiple times to include more servers.
- `--exclude` can be used to exclude servers from making snapshots. Specify
  multiple times to exclude more servers.

It will create a snapshot of all servers by default.

# Restore

```
openstack volume snapshot list
./restore.py --snapshot <id> --volume <name>
```

# Limitations

These scripts were written using Python 3.6. Other versions may work but are
untested.

# Tests

Sorry, this code doesn't come with tests yet.
