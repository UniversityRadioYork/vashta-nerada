import typing as T

ARCHIVE_LOC: str = "/filestore/Archive"
LIBRARY_LOC: str = "/filestore/Archive/Library"

ARCHIVE_DIRS: T.Dict[str, T.Tuple[str, int]] = {
    "/filestore/Profiles/ury": ("Documents", 120),
    "/filestore/Teams/Audio Resources": ("Teams/Audio Resources", 365),
    "/filestore/Teams/Computing": ("Teams/Computing", 365),
    "/filestore/Teams/Engineering": ("Teams/Engineering", 365),
    "/filestore/Teams/Management": ("Teams/Management", 365),
    "/filestore/Teams/Marketing": ("Teams/Marketing", 365),
    "/filestore/Teams/Music": ("Teams/Music", 365),
    "/filestore/Teams/News": ("Teams/News", 365),
    "/filestore/Teams/Production": ("Teams/Production", 365),
    "/filestore/Teams/Speech": ("Teams/Speech", 365)
}

ARCHIVE_UNITS: T.Dict[str, T.Tuple[str, int]] = {
    "/filestore/People": ("People", 365),
    "/filestore/Shows": ("Shows", 365)
}