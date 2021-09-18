import unittest
import archiver
import os
import shutil
import typing as T
import datetime
import tarfile


class TestArchiver(unittest.TestCase):
    def setUp(self) -> None:
        # Create the file structure
        try:
            shutil.rmtree("/tmp/directory")
        except FileNotFoundError:
            pass

        try:
            shutil.rmtree("/tmp/archive")
        except FileNotFoundError:
            pass

        try:
            shutil.rmtree("/tmp/extract")
        except FileNotFoundError:
            pass

        os.mkdir("/tmp/directory")
        os.mkdir("/tmp/archive")
        os.mkdir("/tmp/extract")

    def tearDown(self) -> None:
        shutil.rmtree("/tmp/directory")
        shutil.rmtree("/tmp/archive")
        shutil.rmtree("/tmp/extract")


class TestFullArchiver(TestArchiver):

    to_archive = [
        "/tmp/directory/subdir_some_files/old_archive",
        "/tmp/directory/subdir_archive/old_file_1",
        "/tmp/directory/subdir_archive/old_file_2",
        "/tmp/directory/subdir_archive",
        "/tmp/directory/subdir_ignore/archive",
        "/tmp/directory/old_file"
    ]

    to_keep = [
        "/tmp/directory/subdir_dont_touch/file_a",
        "/tmp/directory/subdir_dont_touch/file_b",
        "/tmp/directory/subdir_some_files/new_keep",
        "/tmp/directory/new_file"
    ]

    to_keep_directories = [
        "/tmp/directory",
        "/tmp/directory/subdir_dont_touch",
        "/tmp/directory/subdir_some_files"
    ]

    to_ignore = [
        "/tmp/directory/subdir_ignore/parent_ignore",
        "/tmp/directory/subdir_ignore/subdir_ignore",
        "/tmp/directory/subdir_ignore/subdir/file",
        "/tmp/directory/subdir_ignore/.archiveignore",
        "/tmp/directory/ignore",
        "/tmp/directory/.archiveignore"
    ]

    to_ignore_directories = [
        "/tmp/directory/subdir_ignore",
        "/tmp/directory/subdir_ignore/subdir"
    ]

    def setUp(self) -> None:
        super().setUp()

        # Nothing in this folder should be touched as its all new
        os.mkdir("/tmp/directory/subdir_dont_touch")
        with open("/tmp/directory/subdir_dont_touch/file_a", "w"):
            pass
        with open("/tmp/directory/subdir_dont_touch/file_b", "w"):
            pass

        # Some files in this folder will be out of date, some won't
        os.mkdir("/tmp/directory/subdir_some_files")
        with open("/tmp/directory/subdir_some_files/old_archive", "w"):
            pass
        os.utime("/tmp/directory/subdir_some_files/old_archive", times=(0, 0))
        with open("/tmp/directory/subdir_some_files/new_keep", "w"):
            pass

        # Everything in this folder is old, so it should all be archived
        os.mkdir("/tmp/directory/subdir_archive")
        with open("/tmp/directory/subdir_archive/old_file_1", "w"):
            pass
        os.utime("/tmp/directory/subdir_archive/old_file_1", times=(0, 0))
        with open("/tmp/directory/subdir_archive/old_file_2", "w"):
            pass
        os.utime("/tmp/directory/subdir_archive/old_file_2", times=(0, 0))
        os.utime("/tmp/directory/subdir_archive", times=(0, 0))

        # This directory has .archiveignore files associated
        os.mkdir("/tmp/directory/subdir_ignore")
        with open("/tmp/directory/subdir_ignore/parent_ignore", "w"):
            pass
        os.utime("/tmp/directory/subdir_ignore/parent_ignore", times=(0, 0))
        with open("/tmp/directory/subdir_ignore/subdir_ignore", "w"):
            pass
        os.utime("/tmp/directory/subdir_ignore/subdir_ignore", times=(0, 0))
        with open("/tmp/directory/subdir_ignore/archive", "w"):
            pass
        os.utime("/tmp/directory/subdir_ignore/archive", times=(0, 0))
        os.mkdir("/tmp/directory/subdir_ignore/subdir")
        with open("/tmp/directory/subdir_ignore/subdir/file", "w"):
            pass
        os.utime("/tmp/directory/subdir_ignore/subdir/file", times=(0, 0))
        os.utime("/tmp/directory/subdir_ignore/subdir", times=(0, 0))
        with open("/tmp/directory/subdir_ignore/.archiveignore", "w") as f:
            f.write("subdir_ignore\n")
            f.write("subdir")

        # These are files in the parent directory
        with open("/tmp/directory/new_file", "w"):
            pass
        with open("/tmp/directory/old_file", "w"):
            pass
        os.utime("/tmp/directory/old_file", times=(0, 0))
        with open("/tmp/directory/ignore", "w"):
            pass
        os.utime("/tmp/directory/ignore", times=(0, 0))
        with open("/tmp/directory/.archiveignore", "w") as f:
            f.write("ignore\n")
            f.write("subdir_ignore/parent_ignore")

        os.mkdir("/tmp/archive/documents")


class TestFullArchiverNotWeaponised(TestFullArchiver):

    def setUp(self) -> None:
        # Create the file structure
        super().setUp()

        # Run the archiver
        archiver.archive_full("/tmp/directory", "documents",
                              5, False, "/tmp/archive", "/tmp/archive", "/.archiveignore")

        # Bring the fofn file into memory
        self.fofn: T.Set[str] = set()
        with open(f"/tmp/archive/documents/{datetime.datetime.now().strftime('%Y%m%d')}.fofn") as f:
            for entry in f:
                self.fofn.add(entry.strip("\n"))

        # Extract the archive
        tarfile.open(
            f"/tmp/archive/documents/{datetime.datetime.now().strftime('%Y%m%d')}.tar.gz").extractall("/tmp/extract")

    def test_archived_files_in_fofn(self):
        self.assertTrue(
            all([item in self.fofn for item in super().to_archive]))

    def test_young_files_not_in_fofn(self):
        self.assertTrue(
            all([item not in self.fofn for item in [*super().to_keep, *super().to_keep_directories]]))

    def test_ignored_files_not_in_fofn(self):
        self.assertTrue(
            all([item not in self.fofn for item in [*super().to_ignore, *super().to_ignore_directories]]))

    def test_archived_files_still_exist(self):
        self.assertTrue(all([os.path.exists(item)
                        for item in super().to_archive]))

    def test_kept_files_still_exist(self):
        self.assertTrue(all([os.path.exists(item)
                        for item in super().to_keep]))

    def test_ignored_files_still_exist(self):
        self.assertTrue(all([os.path.exists(item)
                        for item in super().to_ignore]))

    def test_archived_files_in_archive(self):
        self.assertTrue(all([os.path.exists(os.path.join(
            "/tmp/extract", item.strip("/"))) for item in super().to_archive]))

    def test_kept_files_not_in_archive(self):
        self.assertTrue(all([not os.path.exists(os.path.join(
            "/tmp/extract", item.strip("/"))) for item in super().to_keep]))

    def test_ignored_files_not_in_archive(self):
        self.assertTrue(all([not os.path.exists(os.path.join(
            "/tmp/extract", item.strip("/"))) for item in super().to_ignore]))


class TestFullArchiverWeaponised(TestFullArchiver):

    def setUp(self) -> None:
        # Create the file structure
        super().setUp()

        # Run the archiver
        archiver.archive_full("/tmp/directory", "documents",
                              5, True, "/tmp/archive", "/tmp/archive", "/.archiveignore")

        # Bring the fofn file into memory
        self.fofn: T.Set[str] = set()
        with open(f"/tmp/archive/documents/{datetime.datetime.now().strftime('%Y%m%d')}.fofn") as f:
            for entry in f:
                self.fofn.add(entry.strip("\n"))

        # Extract the archive
        tarfile.open(
            f"/tmp/archive/documents/{datetime.datetime.now().strftime('%Y%m%d')}.tar.gz").extractall("/tmp/extract")

    def test_archived_files_in_fofn(self):
        self.assertTrue(
            all([item in self.fofn for item in super().to_archive]))

    def test_young_files_not_in_fofn(self):
        self.assertTrue(
            all([item not in self.fofn for item in [*super().to_keep, *super().to_keep_directories]]))

    def test_ignored_files_not_in_fofn(self):
        self.assertTrue(
            all([item not in self.fofn for item in [*super().to_ignore, *super().to_ignore_directories]]))

    def test_archived_files_dont_exist(self):
        self.assertTrue(all([not os.path.exists(item)
                        for item in super().to_archive]))

    def test_kept_files_still_exist(self):
        self.assertTrue(all([os.path.exists(item)
                        for item in super().to_keep]))

    def test_ignored_files_still_exist(self):
        self.assertTrue(all([os.path.exists(item)
                        for item in super().to_ignore]))

    def test_archived_files_in_archive(self):
        self.assertTrue(all([os.path.exists(os.path.join(
            "/tmp/extract", item.strip("/"))) for item in super().to_archive]))

    def test_kept_files_not_in_archive(self):
        self.assertTrue(all([not os.path.exists(os.path.join(
            "/tmp/extract", item.strip("/"))) for item in super().to_keep]))

    def test_ignored_files_not_in_archive(self):
        self.assertTrue(all([not os.path.exists(os.path.join(
            "/tmp/extract", item.strip("/"))) for item in super().to_ignore]))


class TestUnitArchiver(TestArchiver):
    def setUp(self) -> None:
        super().setUp()

        os.mkdir("/tmp/directory/new")
        with open("/tmp/directory/new/file_a", "w"):
            pass
        with open("/tmp/directory/new/file_b", "w"):
            pass

        os.mkdir("/tmp/directory/mixed")
        with open("/tmp/directory/mixed/file_a", "w"):
            pass
        with open("/tmp/directory/mixed/file_b", "w"):
            pass
        os.utime("/tmp/directory/mixed/file_a", times=(0, 0))

        os.mkdir("/tmp/directory/old")
        with open("/tmp/directory/old/file_a", "w"):
            pass
        with open("/tmp/directory/old/file_b", "w"):
            pass
        os.utime("/tmp/directory/old/file_a", times=(0, 0))
        os.utime("/tmp/directory/old/file_a", times=(0, 0))
        os.utime("/tmp/directory/old", times=(0, 0))

        os.mkdir("/tmp/directory/ignore")
        with open("/tmp/directory/ignore/file_a", "w"):
            pass
        with open("/tmp/directory/ignore/file_b", "w"):
            pass
        os.utime("/tmp/directory/ignore/file_a", times=(0, 0))
        os.utime("/tmp/directory/ignore/file_a", times=(0, 0))
        os.utime("/tmp/directory/ignore", times=(0, 0))

        with open("/tmp/directory/file_a", "w"):
            pass
        with open("/tmp/directory/file_b", "w"):
            pass
        with open("/tmp/directory/.archiveignore", "w") as f:
            f.write("ignore\n")

        os.mkdir("/tmp/archive/units")


class TestUnitArchiverNotWeaponised(TestUnitArchiver):
    def setUp(self) -> None:
        super().setUp()

        archiver.archive_unit("/tmp/directory", "units", 5, False,
                              "/tmp/archive", "/tmp/archive", "/.archiveignore")

        # Get general file fofn
        self.main_fofn: T.Set[str] = set()
        with open(f"/tmp/archive/units/{datetime.datetime.now().strftime('%Y%m%d')}.fofn") as f:
            for entry in f:
                self.main_fofn.add(entry.strip("\n"))

        # Get Old fofn
        self.old_fofn: T.Set[str] = set()
        with open(f"/tmp/archive/units/old.{datetime.datetime.now().strftime('%Y%m%d')}.fofn") as f:
            for entry in f:
                self.old_fofn.add(entry.strip("\n"))

        # Extract the archives
        os.mkdir("/tmp/extract/main")
        os.mkdir("/tmp/extract/old")
        tarfile.open(
            f"/tmp/archive/units/{datetime.datetime.now().strftime('%Y%m%d')}.tar.gz").extractall("/tmp/extract/main")
        tarfile.open(
            f"/tmp/archive/units/old.{datetime.datetime.now().strftime('%Y%m%d')}.tar.gz").extractall("/tmp/extract/old")

    def test_files_in_main_fofn(self):
        self.assertTrue(all([item in self.main_fofn for item in [
            "/tmp/directory/file_a",
            "/tmp/directory/file_b"
        ]]))

    def test_all_other_files_not_in_main_fofn(self):
        self.assertTrue(all([item not in self.main_fofn for item in [
            "/tmp/directory/new",
            "/tmp/directory/new/file_a",
            "/tmp/directory/new/file_b",
            "/tmp/directory/old",
            "/tmp/directory/old/file_a",
            "/tmp/directory/old/file_b",
            "/tmp/directory/mixed"
            "/tmp/directory/mixed/file_a",
            "/tmp/directory/mixed/file_b",
            "/tmp/directory/ignore",
            "/tmp/directory/ignore/file_a",
            "/tmp/directory/ignore/file_b",
            "/tmp/directory/.archiveignore"
        ]]))

    def test_files_in_old_fofn(self):
        self.assertTrue(all([item in self.old_fofn for item in [
            "/tmp/directory/old/file_a",
            "/tmp/directory/old/file_b"
        ]]))

    def test_all_other_files_not_in_old_fofn(self):
        self.assertTrue(all([item not in self.old_fofn for item in [
            "/tmp/directory/new",
            "/tmp/directory/new/file_a",
            "/tmp/directory/new/file_b",
            "/tmp/directory/mixed"
            "/tmp/directory/mixed/file_a",
            "/tmp/directory/mixed/file_b",
            "/tmp/directory/ignore",
            "/tmp/directory/ignore/file_a",
            "/tmp/directory/ignore/file_b",
            "/tmp/directory/file_a",
            "/tmp/directory/file_b",
            "/tmp/directory/.archiveignore"
        ]]))

    def test_kept_files_still_exist(self):
        self.assertTrue(all([os.path.exists(item) for item in [
            "/tmp/directory/new",
            "/tmp/directory/new/file_a",
            "/tmp/directory/new/file_b",
            "/tmp/directory/mixed",
            "/tmp/directory/mixed/file_a",
            "/tmp/directory/mixed/file_b",
            "/tmp/directory"
        ]]))

    def test_archive_files_still_exist(self):
        self.assertTrue(all([os.path.exists(item) for item in [
            "/tmp/directory/old",
            "/tmp/directory/old/file_a",
            "/tmp/directory/old/file_b",
            "/tmp/directory/file_a",
            "/tmp/directory/file_b"
        ]]))

    def test_ignore_files_still_exist(self):
        self.assertTrue(all([os.path.exists(item) for item in [
            "/tmp/directory/ignore",
            "/tmp/directory/ignore/file_a",
            "/tmp/directory/ignore/file_b",
            "/tmp/directory/.archiveignore"
        ]]))

    def test_archived_files_in_main_archive(self):
        self.assertTrue(all([os.path.exists(os.path.join("/tmp/extract/main", item.strip("/"))) for item in [
            "/tmp/directory/file_a",
            "/tmp/directory/file_b"
        ]]))

    def test_all_other_files_not_in_main_archive(self):
        self.assertTrue(all([not os.path.exists(os.path.join("/tmp/extract/main", item.strip("/"))) for item in [
            "/tmp/directory/new",
            "/tmp/directory/new/file_a",
            "/tmp/directory/new/file_b",
            "/tmp/directory/old",
            "/tmp/directory/old/file_a",
            "/tmp/directory/old/file_b",
            "/tmp/directory/mixed",
            "/tmp/directory/mixed/file_a",
            "/tmp/directory/mixed/file_b",
            "/tmp/directory/ignore",
            "/tmp/directory/ignore/file_a",
            "/tmp/directory/ignore/file_b",
            "/tmp/directory/.archiveignore"
        ]]))

    def test_old_files_in_old_archive(self):
        self.assertTrue(all([os.path.exists(os.path.join("/tmp/extract/old", item)) for item in [
            "old/file_a",
            "old/file_b"
        ]]))

    def test_all_other_files_not_in_old_archive(self):
        self.assertTrue(all([not os.path.exists(os.path.join("/tmp/extract/old", item)) for item in [
            "new",
            "new/file_a",
            "new/file_b",
            "mixed"
            "mixed/file_a",
            "mixed/file_b",
            "ignore",
            "ignore/file_a",
            "ignore/file_b",
            "file_a",
            "file_b",
            ".archiveignore"
        ]]))

    def test_no_other_fofns_exist(self):
        self.assertTrue(all([not os.path.exists(
            f"/tmp/archive/{item}.{datetime.datetime.now().strftime('%Y%m%d')}.fofn") for item in ["new", "mixed", "ignore"]]))

    def test_no_other_archives_exist(self):
        self.assertTrue(all([not os.path.exists(
            f"/tmp/archive/{item}.{datetime.datetime.now().strftime('%Y%m%d')}.tar.gz") for item in ["new", "mixed", "ignore"]]))


class TestUnitArchiverWeaponised(TestUnitArchiver):
    def setUp(self) -> None:
        super().setUp()

        archiver.archive_unit("/tmp/directory", "units", 5, True,
                              "/tmp/archive", "/tmp/archive", "/.archiveignore")

        # Get general file fofn
        self.main_fofn: T.Set[str] = set()
        with open(f"/tmp/archive/units/{datetime.datetime.now().strftime('%Y%m%d')}.fofn") as f:
            for entry in f:
                self.main_fofn.add(entry.strip("\n"))

        # Get Old fofn
        self.old_fofn: T.Set[str] = set()
        with open(f"/tmp/archive/units/old.{datetime.datetime.now().strftime('%Y%m%d')}.fofn") as f:
            for entry in f:
                self.old_fofn.add(entry.strip("\n"))

        # Extract the archives
        os.mkdir("/tmp/extract/main")
        os.mkdir("/tmp/extract/old")
        tarfile.open(
            f"/tmp/archive/units/{datetime.datetime.now().strftime('%Y%m%d')}.tar.gz").extractall("/tmp/extract/main")
        tarfile.open(
            f"/tmp/archive/units/old.{datetime.datetime.now().strftime('%Y%m%d')}.tar.gz").extractall("/tmp/extract/old")

    def test_files_in_main_fofn(self):
        self.assertTrue(all([item in self.main_fofn for item in [
            "/tmp/directory/file_a",
            "/tmp/directory/file_b"
        ]]))

    def test_all_other_files_not_in_main_fofn(self):
        self.assertTrue(all([item not in self.main_fofn for item in [
            "/tmp/directory/new",
            "/tmp/directory/new/file_a",
            "/tmp/directory/new/file_b",
            "/tmp/directory/old",
            "/tmp/directory/old/file_a",
            "/tmp/directory/old/file_b",
            "/tmp/directory/mixed"
            "/tmp/directory/mixed/file_a",
            "/tmp/directory/mixed/file_b",
            "/tmp/directory/ignore",
            "/tmp/directory/ignore/file_a",
            "/tmp/directory/ignore/file_b",
            "/tmp/directory/.archiveignore"
        ]]))

    def test_files_in_old_fofn(self):
        self.assertTrue(all([item in self.old_fofn for item in [
            "/tmp/directory/old/file_a",
            "/tmp/directory/old/file_b"
        ]]))

    def test_all_other_files_not_in_old_fofn(self):
        self.assertTrue(all([item not in self.old_fofn for item in [
            "/tmp/directory/new",
            "/tmp/directory/new/file_a",
            "/tmp/directory/new/file_b",
            "/tmp/directory/mixed"
            "/tmp/directory/mixed/file_a",
            "/tmp/directory/mixed/file_b",
            "/tmp/directory/ignore",
            "/tmp/directory/ignore/file_a",
            "/tmp/directory/ignore/file_b",
            "/tmp/directory/file_a",
            "/tmp/directory/file_b",
            "/tmp/directory/.archiveignore"
        ]]))

    def test_kept_files_still_exist(self):
        self.assertTrue(all([os.path.exists(item) for item in [
            "/tmp/directory/new",
            "/tmp/directory/new/file_a",
            "/tmp/directory/new/file_b",
            "/tmp/directory/mixed",
            "/tmp/directory/mixed/file_a",
            "/tmp/directory/mixed/file_b",
            "/tmp/directory"
        ]]))

    def test_archive_files_dont_exist(self):
        self.assertTrue(all([not os.path.exists(item) for item in [
            "/tmp/directory/old",
            "/tmp/directory/old/file_a",
            "/tmp/directory/old/file_b",
            "/tmp/directory/file_a",
            "/tmp/directory/file_b"
        ]]))

    def test_ignore_files_still_exist(self):
        self.assertTrue(all([os.path.exists(item) for item in [
            "/tmp/directory/ignore",
            "/tmp/directory/ignore/file_a",
            "/tmp/directory/ignore/file_b",
            "/tmp/directory/.archiveignore"
        ]]))

    def test_archived_files_in_main_archive(self):
        self.assertTrue(all([os.path.exists(os.path.join("/tmp/extract/main", item.strip("/"))) for item in [
            "/tmp/directory/file_a",
            "/tmp/directory/file_b"
        ]]))

    def test_all_other_files_not_in_main_archive(self):
        self.assertTrue(all([not os.path.exists(os.path.join("/tmp/extract/main", item.strip("/"))) for item in [
            "/tmp/directory/new",
            "/tmp/directory/new/file_a",
            "/tmp/directory/new/file_b",
            "/tmp/directory/old",
            "/tmp/directory/old/file_a",
            "/tmp/directory/old/file_b",
            "/tmp/directory/mixed",
            "/tmp/directory/mixed/file_a",
            "/tmp/directory/mixed/file_b",
            "/tmp/directory/ignore",
            "/tmp/directory/ignore/file_a",
            "/tmp/directory/ignore/file_b",
            "/tmp/directory/.archiveignore"
        ]]))

    def test_old_files_in_old_archive(self):
        self.assertTrue(all([os.path.exists(os.path.join("/tmp/extract/old", item)) for item in [
            "old/file_a",
            "old/file_b"
        ]]))

    def test_all_other_files_not_in_old_archive(self):
        self.assertTrue(all([not os.path.exists(os.path.join("/tmp/extract/old", item)) for item in [
            "new",
            "new/file_a",
            "new/file_b",
            "mixed"
            "mixed/file_a",
            "mixed/file_b",
            "ignore",
            "ignore/file_a",
            "ignore/file_b",
            "file_a",
            "file_b",
            ".archiveignore"
        ]]))

    def test_no_other_fofns_exist(self):
        self.assertTrue(all([not os.path.exists(
            f"/tmp/archive/{item}.{datetime.datetime.now().strftime('%Y%m%d')}.fofn") for item in ["new", "mixed", "ignore"]]))

    def test_no_other_archives_exist(self):
        self.assertTrue(all([not os.path.exists(
            f"/tmp/archive/{item}.{datetime.datetime.now().strftime('%Y%m%d')}.tar.gz") for item in ["new", "mixed", "ignore"]]))


if __name__ == "__main__":
    unittest.main()
