import time
import openstack
from halo import Halo


class OpenStack(object):
    def setup_spinner(self, text='Loading'):
        spinner = Halo(
            text=text,
            spinner='simpleDots',
            color='white',
        ).start()

        return spinner

    def handle_spinner_error_state(self, spinner, succeed_on_error=False):
        if succeed_on_error:
            spinner.stop_and_persist(symbol='[x]', text='Finished')
            return True

        spinner.fail()
        return False

    def wait_for_state(self, state='available', attempts=10, succeed_on_error=False): # noqa
        '''Waits until the volume has a certain state'''
        tries = 0

        # Start the spinner
        spinner = self.setup_spinner()

        # Wait 1 second to give the API some space to breathe
        time.sleep(1)

        # Get the current state and check if it's valid
        try:
            previous_state = self.state
        except openstack.exceptions.ResourceNotFound:
            return self.handle_spinner_error_state(
                spinner=spinner,
                succeed_on_error=succeed_on_error
            )

        spinner.text = previous_state.title()

        while tries < attempts:
            time.sleep(1)
            try:
                current_state = self.state
            except openstack.exceptions.ResourceNotFound:
                return self.handle_spinner_error_state(
                    spinner=spinner,
                    succeed_on_error=succeed_on_error
                )

            if current_state == state:
                spinner.stop_and_persist(
                    symbol='[x]',
                    text=current_state.title()
                )

                return True

        spinner.fail()
        return False

    def delete(self):
        '''Dummy method that should delete the object'''
        return True

    @property
    def state(self):
        '''Return the current state of the object'''
        return 'unknown'


class Image(OpenStack):
    def __init__(self, api, image, debug=True):
        self.api = api
        self.image = image
        self.debug = debug

    def to_volume(self, name, size, wait=True, attempts=600):
        '''Convert the image to a volume'''
        volume = self.api.volume.create_volume(
            name=name,
            image_id=self.image.id,
            size=size,
        )

        volume = Volume(api=self.api, volume=volume)

        if wait:
            if volume.wait_for_state(state='available', attempts=attempts):
                return volume

            return False

        return volume

    def delete(self):
        '''Delete the image from OpenStack'''
        self.api.delete_image(self.image.id)

    @property
    def state(self):
        '''Get the current state of the image'''
        return self.api.get_image(self.image.id).status


class Volume(OpenStack):
    def __init__(self, api, volume, debug=True):
        self.api = api
        self.volume = volume
        self.debug = debug

    def to_image(self, name, wait=True, attempts=600):
        '''Convert an existing volume to an image'''
        image = self.api.create_image(
            name=name,
            volume=self.volume,
        )

        image = Image(api=self.api, image=image)

        if wait:
            if image.wait_for_state(state='active', attempts=attempts):
                return image

            return False

        return image

    def to_snapshot(self, name, description, wait=True, attempts=600):
        '''Create a snapshot of a volume'''
        snapshot = self.api.volume.create_snapshot(
            name=name,
            description=description,
            volume_id=self.volume.id,
            force=True,
        )

        snapshot = Snapshot(api=self.api, snapshot=snapshot)

        if wait:
            if snapshot.wait_for_state(state='available', attempts=attempts):
                return snapshot

            return False

        return snapshot

    def snapshots(self):
        '''Return all snapshots for this volume'''
        return self.api.volume.snapshots(volume_id=self.volume.id)

    def delete(self):
        '''Delete the volume from OpenStack'''
        self.api.volume.delete_volume(self.volume)

    @property
    def state(self):
        '''Get the current state of the volume'''
        return self.api.volume.get_volume(self.volume).status


class Snapshot(OpenStack):
    def __init__(self, api, snapshot, debug=True):
        self.api = api
        self.snapshot = snapshot
        self.debug = debug

    def to_volume(self, name, wait=True, attempts=10):
        '''Create a volume from a snapshot'''
        volume = self.api.volume.create_volume(
            name=name,
            snapshot_id=self.snapshot.id,
        )

        volume = Volume(api=self.api, volume=volume)

        if wait:
            if volume.wait_for_state(state='available', attempts=attempts):
                return volume

            return False

        return volume

    def delete(self):
        '''Delete the snapshot from OpenStack'''
        self.api.volume.delete_snapshot(self.snapshot)

        return self.wait_for_state(
            state='error',
            attempts=10,
            succeed_on_error=True
        )

    @property
    def state(self):
        '''Return the current state of the snapshot'''
        return self.api.volume.get_snapshot(self.snapshot).status
