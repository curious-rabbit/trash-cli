import errno
import os
import shutil
import stat
import tempfile

from trashcli.fslib.protocols.move import Move


class RealMove(Move):
    def move(self, path, dest):
        dest = str(dest)
        if not os.path.isdir(path) or os.path.islink(path) or not os.listdir(path):
            return shutil.move(path, dest)
        try:
            os.rename(path, dest)
            return dest
        except OSError as e:
            # on one file system copy and delete of a full directory never works
            if e.errno != errno.EXDEV:
                raise
        try:
            shutil.copytree(path, dest, symlinks=True)
            _remove_or_undo(path)
        except EnvironmentError:
            _remove_copy(dest)
            raise
        return dest


def _remove_or_undo(path):
    # remove by renaming into a folder on the same file system so every step can be undone
    holder = tempfile.mkdtemp(prefix='.trash-put-', dir=os.path.dirname(os.path.abspath(path)))
    done = []
    try:
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files + dirs:
                entry = os.path.join(root, name)
                if os.path.isdir(entry) and not os.path.islink(entry):
                    mode = os.lstat(entry).st_mode
                    os.rmdir(entry)
                    done.append((entry, mode))
                else:
                    os.rename(entry, os.path.join(holder, str(len(done))))
                    done.append((entry, None))
        mode = os.lstat(path).st_mode
        os.rmdir(path)
        done.append((path, mode))
    except OSError:
        for index in reversed(range(len(done))):
            entry, mode = done[index]
            if mode is None:
                os.rename(os.path.join(holder, str(index)), entry)
            else:
                os.mkdir(entry)
                os.chmod(entry, stat.S_IMODE(mode))
        os.rmdir(holder)
        raise
    shutil.rmtree(holder)


def _remove_copy(copy):
    # the copy keeps the original modes and must be made writable first
    for root, dirs, files in os.walk(copy):
        os.chmod(root, stat.S_IRWXU)
    if os.path.lexists(copy):
        shutil.rmtree(copy)
