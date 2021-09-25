import logging
import typing as T

ARCHIVE_LOC: str = "/filestore/Archive"
LIBRARY_LOC: str = "/filestore/Archive/Library"
ARCHIVE_IGNORE_FORMAT: str = "/.archiveignore"

ARCHIVE_DIRS: T.Dict[str, T.Tuple[str, int]] = {
    "/filestore/Profiles/ury": ("Documents", 5),
    "/filestore/Teams/Audio Resources": ("Teams/Audio Resources", 365),
    "/filestore/Teams/Computing": ("Teams/Computing", -1),
    "/filestore/Teams/Engineering": ("Teams/Engineering", 365),
    "/filestore/Teams/Management": ("Teams/Management", 365),
    "/filestore/Teams/Marketing": ("Teams/Marketing", 365),
    "/filestore/Teams/Music": ("Teams/Music", 365),
    "/filestore/Teams/News": ("Teams/News", 365),
    "/filestore/Teams/Production": ("Teams/Production", -1),
    "/filestore/Teams/Speech": ("Teams/Speech", 365)
}

ARCHIVE_UNITS: T.Dict[str, T.Tuple[str, int]] = {
    "/filestore/People": ("People", -1),
    "/filestore/Shows": ("Shows", -1)
}

LOGGING_LEVEL: int = logging.INFO
