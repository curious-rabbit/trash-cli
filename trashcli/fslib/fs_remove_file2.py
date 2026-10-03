import errno

from trashcli.fslib.protocols.fs import Fs
from trashcli.fslib.protocols.remove_file2 import RemoveFile2


class FsRemoveFile2(RemoveFile2):
    def __init__(self, fs):  # type: (Fs) -> None
        self.fs = fs

    def remove_file2(self, path):
        try:
            self.fs.remove(path)
        except OSError:
            try:
                self.fs.shutil_rmtree(path)
            except OSError as e:
                # a missing write or search bit fails with EACCES
                if e.errno != errno.EACCES:
                    raise
                old_modes = self.fs.add_write_permission(path)
                # retry only if some directory got the missing bits
                if not old_modes:
                    raise
                try:
                    self.fs.shutil_rmtree(path)
                except OSError:
                    self.fs.restore_modes(path, old_modes)
                    raise
