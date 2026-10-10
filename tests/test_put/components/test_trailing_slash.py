import os

from trashcli.put.context import without_trailing_slashes
from trashcli.put.core.trashee import should_skipped_by_specs


class TestWithoutTrailingSlashes:
    def test_trailing_slashes_are_removed(self):
        assert [without_trailing_slashes("dir/"),
                without_trailing_slashes("dir//"),
                without_trailing_slashes("dir")] == ["dir", "dir", "dir"]

    def test_the_root_is_kept(self):
        assert without_trailing_slashes("/") == "/"

    def test_the_rest_of_the_path_is_left_unchanged(self):
        assert without_trailing_slashes("a/../b/") == "a/../b"


class TestBasename:
    def test_the_plain_basename_and_the_normalized_one_disagree(self):
        assert [(os.path.basename(p), os.path.basename(os.path.normpath(p)))
                for p in ["./", "a/b/.."]] == [("", "."), ("..", "a")]

    def test_dot_entries_are_refused_after_the_slash_is_removed(self):
        paths = ["./", "../", "dir/./", "dir/../", "dir/"]
        assert [should_skipped_by_specs(without_trailing_slashes(p))
                for p in paths] == [True, True, True, True, False]
