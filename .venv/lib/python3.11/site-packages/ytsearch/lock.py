#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import time


def create(lockfile):
    """
    Create the lockfile. This will also attempt to aquire it to make
    sure it has the rights.

    :lockfile: str: The path of the lockfile to use.
    :return: bool: True if this instance has ownership, False otherwise.
    """
    if not aquire(lockfile):
        return False

    with open(lockfile, 'w') as f:
        f.write('This file is protected!')
    return True


def aquire(lockfile, timeout=1, attempts=10):
    """
    Attempt to aquire ownership over the lockfile. ie: If it exists
    for too long, this instance will NOT have ownership.

    :lockfile: str: The path of the lockfile to use.
    :timeout: int: The time to sleep between each attempt.
    :attempts: int: The number of attempts to try to get ownership.
    :return: bool: True if this instance has ownership. False otherwise.
    """
    for i in range(attempts):
        if os.path.exists(lockfile):
            time.sleep(timeout)
        else:
            return True
    return False


def release(lockfile):
    """Remove the lockfile. This is assumed to have ownership.
    You should not be calling this when the instance does not have ownership.
    
    :lockfile: str: The path of the lockfile to use.
    :return: None
    """
    if not os.path.exists(lockfile):
        return None
    os.remove(lockfile)
    return None
