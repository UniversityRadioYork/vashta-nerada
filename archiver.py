import argparse
import datetime
import os
import shutil
import tarfile
import time

import typing as T

import config


def all_entries(directory: str) -> T.List[str]:
    all_items = os.walk(directory)
    all_paths: T.List[str] = []

    for directory, subdirs, files in all_items:
        all_paths.extend([os.path.join(directory, p) for p in subdirs])
        all_paths.extend([os.path.join(directory, p) for p in files])

    return all_paths


def archive_unit(directory: str, archive_location: str, ttl: int, dry_run: bool) -> None:
    all_files = os.walk(directory)
    _, subdirectories, files = next(all_files)
    for subdirectory in subdirectories:
        _mtime = datetime.datetime.fromtimestamp(
            os.stat(os.path.join(directory, subdirectory)).st_mtime)

        if (datetime.datetime.now() - _mtime).days < ttl:
            continue

        fn = f"{archive_location}/{subdirectory.replace(' ', '')}.{datetime.datetime.now().strftime('%Y%m%d')}"

        with tarfile.open(f"{config.ARCHIVE_LOC}/{fn}.tar.gz", "w:gz") as tar:
            tar.add(os.path.join(directory, subdirectory),
                    arcname=subdirectory)

        with open(f"{config.LIBRARY_LOC}/{fn}.fofn", "w") as fofn:
            fofn.write("\n".join(all_entries(
                os.path.join(directory, subdirectory))))

        if not dry_run:
            shutil.rmtree(os.path.join(directory, subdirectory))

    if len(files) != 0:
        fn = f"{archive_location}/{datetime.datetime.now().strftime('%Y%m%d')}"
        with tarfile.open(f"{config.ARCHIVE_LOC}/{fn}.tar.gz", "w:gz") as tar:
            for f in files:
                tar.add(os.path.join(directory, f))

        with open(f"{config.LIBRARY_LOC}/{fn}.fofn", "w") as fofn:
            fofn.write(
                "\n".join([os.path.join(directory, f) for f in files]))

        if not dry_run:
            for f in files:
                os.remove(os.path.join(directory, f))


def archive_full(directory: str, archive_location: str, ttl: int, dry_run: bool) -> None:
    all_items = all_entries(directory)
    to_archive: T.List[str] = []
    for item in all_items:
        _atime = datetime.datetime.fromtimestamp(os.stat(item).st_atime)
        if (datetime.datetime.now() - _atime).days >= ttl:
            to_archive.append(item)

    if len(to_archive) != 0:
        fn = f"{archive_location}/{datetime.datetime.now().strftime('%Y%m%d')}"
        with tarfile.open(f"{config.ARCHIVE_LOC}/{fn}.tar.gz", "w:gz") as tar:
            for f in to_archive:
                tar.add(f)

        with open(f"{config.LIBRARY_LOC}/{fn}.fofn", "w") as fofn:
            fofn.write("\n".join(to_archive))

        if not dry_run:
            for f in to_archive:
                try:
                    try:
                        os.remove(f)
                    except IsADirectoryError:
                        shutil.rmtree(f)
                except FileNotFoundError:
                    pass


def main(dry_run: bool = False) -> None:
    for directory, (archive_location, ttl) in config.ARCHIVE_DIRS.items():
        archive_full(directory, archive_location, ttl, dry_run)

    for directory, (archive_location, ttl) in config.ARCHIVE_UNITS.items():
        archive_unit(directory, archive_location, ttl, dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry", help="run archiver without deleting files once archived", action="store_true")
    args = parser.parse_args()

    if args.dry:
        print("Running the archiver without deleting fils once archived.")
        for i in range(5, 0, -1):
            print(i, end="\r")
            time.sleep(1)
        main(dry_run=True)

    else:
        print("Running the archiver.")
        print("THIS WILL DELETE THE FILES ONCE ARCHIVED!")
        for i in range(5, 0, -1):
            print(i, end="\r")
            time.sleep(1)
        main()
