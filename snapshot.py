#!/usr/bin/env python
#
# This is NOT intended as a backup replacement. Snapshots are crash consistent,
# not application consistent. This means in-memory data may get lost. As a
# result, it makes no sense to have a --retention flag, you should only have
# a single snapshot per instance. Data backups should be done elsewhere.
#

import argparse
import openstack
import time
from sdk import Snapshot
from sdk import Volume


def main(args):
    # Set up the connection to OpenStack -- this is read from clouds.yaml
    openstack.enable_logging(debug=False)
    api = openstack.connect(cloud=args.cloud)

    # Create a list of known snapshots -- we do this to limit the number
    # of API calls later on when detecting old snapshots
    current_snapshots = {}
    for snapshot in api.volume.snapshots():
        current_snapshots[snapshot['id']] = snapshot['volume_id']

    today = time.strftime("%d-%m-%Y")

    print('')

    exclude = args.exclude
    include = args.include

    for server in api.compute.servers():
        # Logic for include and exclude
        if len(exclude) > 0:
            if server.name in exclude:
                continue

        if len(include) > 0:
            if server.name not in include:
                continue

        print(server.name)

        if len(server.attached_volumes) >= 1:
            for volume in server.attached_volumes:
                # Detect and remove old snapshots
                for snapshot_id, volume_id in current_snapshots.items():
                    if volume_id == volume['id']:
                        print('Deleting old snapshot..')
                        snapshot = Snapshot(
                            api=api,
                            snapshot=api.volume.get_snapshot(snapshot_id),
                        )

                        snapshot.delete()

                # Create new snapshot
                print('Creating new snapshot..')
                volume = Volume(
                    api=api,
                    volume=api.volume.get_volume(volume['id']),
                )
                volume.to_snapshot(
                    name=server.name,
                    description='Automated snapshot on {}'.format(today),
                )

            print('')

    print('Snapshots created.')
    print('')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create snapshots from servers on OpenStack.',
        epilog='This is NOT intended as a backup replacement.',
    )
    parser.add_argument(
        '--include',
        action='append',
        help='',
        metavar=('<server>'),
        default=[],
    )
    parser.add_argument(
        '--exclude',
        action='append',
        help='',
        metavar=('<server>'),
        default=[],
    )
    parser.add_argument(
        '--cloud',
        help='',
        metavar=('<cloud in clouds.yaml>'),
        default='fuga',
    )

    args = parser.parse_args()
    main(args)
