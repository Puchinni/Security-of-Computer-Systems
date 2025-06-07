import psutil

class UsbDrive:
    def __init__(self, device: str, mountpoint: str):
        self.device = device
        self.mountpoint = mountpoint
        self.keys = []

    def __str__(self):
        return f"device: {self.device}, mountpoint: {self.mountpoint}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.device == other.device and self.mountpoint == other.mountpoint


def get_usb_mounts() -> list[UsbDrive]:
    partitions = psutil.disk_partitions(all=False)
    partitions = [part for part in partitions if
                  'removable' in part.opts or
                  'media' in part.mountpoint.lower()]
    return [UsbDrive(part.device, part.mountpoint) for part in partitions]

# This function checks for USB drives that have been added or removed since the last check.
def get_usb_update(known: list[UsbDrive]):
    current = get_usb_mounts()

    added = [drive for drive in current if
             drive not in known]
    removed = [drive for drive in known if
               drive not in current]
    if added:
        print("USB plugged in:", added)
    if removed:
        print("USB unplugged:", removed)

    return current, (added or removed), added