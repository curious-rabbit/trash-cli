import os
import stat


def add_write_permission(path):
    # add owner write and search bits to own directories, return old modes
    old_modes = {}
    for fd in _dir_fds(path, topdown=True):
        try:
            st = os.fstat(fd)
            old = stat.S_IMODE(st.st_mode)
            new = old | stat.S_IWUSR | stat.S_IXUSR
            if new != old and st.st_uid == os.geteuid():
                os.fchmod(fd, new)
                old_modes[(st.st_dev, st.st_ino)] = old
        except OSError:
            pass
    return old_modes


def restore_modes(path, old_modes):
    # set back the old mode of each changed directory that is left
    for fd in _dir_fds(path, topdown=False):
        try:
            st = os.fstat(fd)
            if (st.st_dev, st.st_ino) in old_modes:
                os.fchmod(fd, old_modes[(st.st_dev, st.st_ino)])
        except OSError:
            pass


def _dir_fds(path, topdown):
    # yield a handle for each directory under path, never follow symlinks
    if hasattr(os, 'fwalk'):
        try:
            for _, _, _, fd in os.fwalk(path, topdown=topdown,
                                        follow_symlinks=False):
                yield fd
        except OSError:
            pass
        return
    for fd in _proc_fds(path, topdown):
        yield fd


def _proc_fds(path, topdown):
    # without fwalk, open each entry through /proc/self/fd of its directory
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return
    try:
        if topdown:
            yield fd
        try:
            names = os.listdir('/proc/self/fd/%d' % fd)
        except OSError:
            names = []
        for name in names:
            for child_fd in _proc_fds('/proc/self/fd/%d/%s' % (fd, name),
                                      topdown):
                yield child_fd
        if not topdown:
            yield fd
    finally:
        os.close(fd)
