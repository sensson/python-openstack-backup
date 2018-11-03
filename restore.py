#!/usr/bin/env python
#
# This will take a snapshot and convert it into a volume. To create a volume
# without any links to the old snapshot you need to convert it to a temporary
# volume first, convert that into an image and convert the image back into
# your final volume. Once this is all done, the temporary volume and image
# will be removed.
#

import argparse
import openstack
import time
import sys
from sdk import Snapshot


def main(args):
    # Set up the connection to OpenStack -- this is read from clouds.yaml
    openstack.enable_logging(debug=False)
    api = openstack.connect(cloud='fuga')

    snapshot_id = args.snapshot
    server = args.volume

    # Create a snapshot object
    try:
        snapshot = Snapshot(
            api=api,
            snapshot=api.volume.get_snapshot(snapshot_id),
        )
    except openstack.exceptions.ResourceNotFound:
        print('Snapshot id {} not found.'.format(snapshot_id))
        sys.exit(1)

    today = time.strftime("%d-%m-%Y")

    # Convert the snapshot to a volume
    print('')

    print('Converting snapshot to volume..')
    volume = snapshot.to_volume('{}-restore-{}'.format(server, today))

    print('Converting volume to image..')
    image = volume.to_image('{}-restore-{}'.format(server, today))

    print('Converting image to volume..')
    image.to_volume(server, size=volume.volume.size)

    image.delete()
    volume.delete()
    print('')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Restore snapshots')
    parser.add_argument(
        '--snapshot',
        required=True,
        help='',
        metavar=('<snapshot_id>'),
    )
    parser.add_argument(
        '--volume',
        required=True,
        help='',
        metavar=('<volume name>'),
    )

    args = parser.parse_args()
    main(args)
