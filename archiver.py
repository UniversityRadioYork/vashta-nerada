import argparse
import datetime
import fnmatch
import logging
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


def archive_unit(directory: str, archive_location: str, ttl: int, weaponised: bool, parent_archive: str, library_loc: str, ignore_format: str) -> None:
    """Archive directories as a whole, where everything in the directory is last modified more than the ttl (days)
    Files shouldn't be stored in the locations of the directories (except .archiveignore), so they'll be archived immediately

    :param directory: - The parent directory
    :param archive_location: - The path within the main archive location for these files to be archived
    :param ttl: - Time to live (days) - Last Modified Time
    :param weaponised: - Whether the original files will be deleted afterwards
    :param parent_archive: - The main archive location
    :param library_loc: - The main location for fofn (file of file names) files
    :param ignore_format: - The format files will be in if they are to be processed as ignore files
    """

    logging.info(f"analysing {directory}")

    all_files = os.walk(directory)
    _, subdirectories, files = next(all_files)

    ignore_files: T.List[str] = [
        os.path.join(directory, f) for f in files if os.path.join(directory, f).endswith(ignore_format)]
    paths_to_ignore: T.List[str] = []
    for ignorefile in ignore_files:
        logging.debug(f"found ignorefile {ignorefile}")
        with open(ignorefile) as f:
            for entry in f:
                paths_to_ignore.append(os.path.join(
                    os.path.dirname(ignorefile), entry.strip("\n")))
    logging.debug(f"all ignore paths: {paths_to_ignore}")

    for subdirectory in subdirectories:
        _mtime = datetime.datetime.fromtimestamp(
            os.stat(os.path.join(directory, subdirectory)).st_mtime)

        if (datetime.datetime.now() - _mtime).days < ttl \
                or any([fnmatch.fnmatch(os.path.join(directory, subdirectory), pattern) for pattern in paths_to_ignore]):
            continue

        fn = f"{archive_location}/{subdirectory.replace(' ', '')}.{datetime.datetime.now().strftime('%Y%m%d')}"

        with tarfile.open(f"{parent_archive}/{fn}.tar.gz", "w:gz") as tar:
            logging.debug(f"creating tarball {parent_archive}/{fn}.tar.gz")
            tar.add(os.path.join(directory, subdirectory),
                    arcname=subdirectory)

        with open(f"{library_loc}/{fn}.fofn", "w") as fofn:
            logging.info(f"writing {library_loc}/{fn}.fofn")
            fofn.write("\n".join(all_entries(
                os.path.join(directory, subdirectory))))

        if weaponised:
            logging.warning("deleting directory that was archived")
            shutil.rmtree(os.path.join(directory, subdirectory))

    if len(files) != 0:
        logging.info(f"found files where they shouldn't be: {directory}")
        fn = f"{archive_location}/{datetime.datetime.now().strftime('%Y%m%d')}"
        with tarfile.open(f"{parent_archive}/{fn}.tar.gz", "w:gz") as tar:
            for f in files:
                if not os.path.join(directory, f).endswith(ignore_format):
                    logging.debug(f"adding {f} to tarball")
                    tar.add(os.path.join(directory, f))

        with open(f"{library_loc}/{fn}.fofn", "w") as fofn:
            logging.info(f"writing {library_loc}/{fn}.fofn")
            fofn.write(
                "\n".join([os.path.join(directory, f) for f in files if not os.path.join(directory, f).endswith(ignore_format)]))

        if weaponised:
            logging.warning("deleting files that were archived")
            for f in files:
                if not os.path.join(directory, f).endswith(ignore_format):
                    os.remove(os.path.join(directory, f))


def archive_full(directory: str, archive_location: str, ttl: int, weaponised: bool, parent_archive: str, library_loc: str, ignore_format: str) -> None:
    """Archive all files in a directory and its subdirectories when it's last accessed more than the ttl (days)

    :param directory: - The parent directory
    :param archive_location: - The path within the main archive location for these files to be archived
    :param ttl: - Time to live (days) - Last Modified Time
    :param weaponised: - Whether the original files will be deleted afterwards
    :param parent_archive: - The main archive location
    :param library_loc: - The main location for fofn (file of file names) files
    :param ignore_format: - The format files will be in if they are to be processed as ignore files
    """

    logging.info(f"analysing {directory}")

    all_items = all_entries(directory)
    to_archive: T.List[str] = []

    ignore_files: T.List[str] = [
        f for f in all_items if f.endswith(ignore_format)]
    paths_to_ignore: T.List[str] = []
    for ignorefile in ignore_files:
        logging.debug(f"found ignorefile {ignorefile}")
        with open(ignorefile) as f:
            for entry in f:
                paths_to_ignore.append(os.path.join(
                    os.path.dirname(ignorefile), entry.strip("\n")))
                paths_to_ignore.append(os.path.join(
                    os.path.dirname(ignorefile), entry.strip("\n"), "*"
                ))
    logging.debug(f"all ignore paths: {paths_to_ignore}")

    for item in all_items:
        _mtime = datetime.datetime.fromtimestamp(os.stat(item).st_mtime)
        if (datetime.datetime.now() - _mtime).days >= ttl \
                and not any([fnmatch.fnmatch(item, pattern) for pattern in paths_to_ignore]) \
                and not item.endswith(ignore_format):
            logging.debug(f"planning to archive {item}")
            to_archive.append(item)

    if len(to_archive) != 0:
        fn = f"{archive_location}/{datetime.datetime.now().strftime('%Y%m%d')}"
        with tarfile.open(f"{parent_archive}/{fn}.tar.gz", "w:gz") as tar:
            for f in to_archive:
                logging.debug(f"adding {f} to tarball")
                tar.add(f)

        with open(f"{library_loc}/{fn}.fofn", "w") as fofn:
            logging.info(f"writing {library_loc}/{fn}.fofn")
            fofn.write("\n".join(to_archive))

        if weaponised:
            logging.warning("deleting files that were archived")
            for f in to_archive:
                try:
                    try:
                        os.remove(f)
                    except IsADirectoryError:
                        shutil.rmtree(f)
                except FileNotFoundError:
                    pass


def main(weaponised: bool = False) -> None:
    logging.info("starting the archive process")

    for directory, (archive_location, ttl) in config.ARCHIVE_DIRS.items():
        archive_full(directory, archive_location, ttl, weaponised,
                     config.ARCHIVE_LOC, config.LIBRARY_LOC, config.ARCHIVE_IGNORE_FORMAT)

    for directory, (archive_location, ttl) in config.ARCHIVE_UNITS.items():
        archive_unit(directory, archive_location, ttl, weaponised,
                     config.ARCHIVE_LOC, config.LIBRARY_LOC, config.ARCHIVE_IGNORE_FORMAT)

    logging.info("finished the archive process")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--weaponised", help="run archiver deleting files once archived", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=config.LOGGING_LEVEL,
                        format="%(asctime)s - %(levelname)s - %(message)s")

    if not args.weaponised:
        logging.info(
            "Running the archiver without deleting fils once archived.")
        time.sleep(5)
        main()

    else:
        logging.info("Running the archiver.")
        logging.warning("THIS WILL DELETE THE FILES ONCE ARCHIVED!")
        time.sleep(5)
        main(weaponised=True)
