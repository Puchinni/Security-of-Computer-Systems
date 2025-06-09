"""
USB Drive Detection Module

This module provides functionality to detect mounted USB drives using `psutil`
and to track changes such as USB plug-in or removal events.
"""

import psutil


class UsbDrive:
    """
    A class representing a mounted USB drive.

    :param device: The device path (e.g., /dev/sdb1).
    :type device: str
    :param mountpoint: The mount point of the device (e.g., /media/user/USB).
    :type mountpoint: str
    """

    def __init__(self, device: str, mountpoint: str):
        self.device = device
        self.mountpoint = mountpoint
        self.keys = []

    def __str__(self):
        """
        Return a human-readable string representation of the USB drive.

        :return: String in the format "device: <device>, mountpoint: <mountpoint>".
        :rtype: str
        """
        return f"device: {self.device}, mountpoint: {self.mountpoint}"

    def __repr__(self):
        """
        Return a formal string representation of the USB drive.

        :return: Same as __str__.
        :rtype: str
        """
        return self.__str__()

    def __eq__(self, other):
        """
        Check if two UsbDrive instances represent the same device.

        :param other: Another UsbDrive instance.
        :type other: UsbDrive
        :return: True if device and mountpoint match, False otherwise.
        :rtype: bool
        """
        return self.device == other.device and self.mountpoint == other.mountpoint


def get_usb_mounts() -> list[UsbDrive]:
    """
    Get a list of currently mounted USB drives.

    This filters partitions by looking for "removable" in the mount options
    or "media" in the mount point path.

    :return: List of currently mounted USB drives.
    :rtype: list[UsbDrive]
    """
    partitions = psutil.disk_partitions(all=False)
    partitions = [part for part in partitions if
                  'removable' in part.opts or
                  'media' in part.mountpoint.lower()]
    return [UsbDrive(part.device, part.mountpoint) for part in partitions]


def get_usb_update(known: list[UsbDrive]):
    """
    Compare the current list of mounted USB drives with a previously known list.

    This function detects which USB drives were added or removed.

    :param known: A previously known list of UsbDrive instances.
    :type known: list[UsbDrive]
    :return: A tuple of (current_list, has_changed, added_list)
    :rtype: tuple[list[UsbDrive], bool, list[UsbDrive]]
    """
    current = get_usb_mounts()

    added = [drive for drive in current if drive not in known]
    removed = [drive for drive in known if drive not in current]

    if added:
        print("USB plugged in:", added)
    if removed:
        print("USB unplugged:", removed)

    return current, (added or removed), added
