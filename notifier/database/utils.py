import logging
from abc import ABC
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, List, Literal, Optional, Tuple, Type, Union

from notifier.database.drivers.base import BaseDatabaseDriver

logger = logging.getLogger(__name__)


def resolve_driver_from_config(driver_path: str) -> Type[BaseDatabaseDriver]:
    """For a given Python path pointing to a database driver class (e.g.
    module.package.file.DriverClass), import the module and return the
    class.
    """
    logger.debug("Resolving database driver %s", {"path": driver_path})
    module_path, class_name = driver_path.rsplit(".", 1)
    try:
        driver_module = import_module(module_path)
    except ImportError as error:
        raise ImportError(
            f"Could not resolve driver module path {module_path} to a module"
        ) from error
    try:
        driver_class = getattr(driver_module, class_name)
    except AttributeError as error:
        raise AttributeError(
            f"Could not find driver class {class_name} in {module_path}"
        ) from error
    logger.debug(
        "Found database driver class %s", {"class": repr(driver_class)}
    )
    return driver_class


def try_cache(
    *,
    get: Callable,
    store: Callable,
    do_not_store: Optional[Any] = None,
    catch: Optional[Tuple[Type[Exception], ...]] = None,
) -> None:
    """Attempts to retrieve data from somewhere. If it succeeds, caches the
    data. If it fails, does nothing.

    Intended usage is for the data to be subsequently retrieved from the
    cache. This ensure that valid data is always received, even if the
    original call failed - in this case, old cached data is used instead.

    If it is necessary for the getter to succeed (e.g. for permanent
    storage of new posts), this function should not be used. It should only
    be used when failure is possible and acceptable (e.g. for temporary
    storage of user config).

    :param get: Callable that takes no argument that retrieves data, and
    may fail.

    :param store: Callable that takes the result of `get` as its only
    argument and caches the data.

    :param do_not_store: If the result of `get` is equal to this,
    it will not be stored. Defaults to None. If `get` returning None is
    desirable, set to a sentinel value.

    :param catch: Tuple of exceptions to catch. If `get` emits any other
    kind of error, it will not be caught. Defaults to catching no
    exceptions which obviously is not recommended. If an exception is
    caught, the store is not called.

    Functions intended to be used with this function typically either raise
    an error or return a no-op value, so `do_not_store` and `catch` should
    rarely be used together.
    """
    if catch is None:
        catch = tuple()
    value = do_not_store
    try:
        value = get()
    except catch as error:
        logger.error(
            "try_cache failed; using value from cache %s",
            {"get": get.__name__},
            exc_info=error,
        )
    if value != do_not_store:
        store(value)


class BaseDatabaseWithSqlFileCache(ABC):
    """Utilities for a database to read its SQL commands directly from the
    filesystem, caching those commands between batches of queries.

    This is so that the SQL commands can be safely edited between queries
    with no downtime.

    Execute clear_query_file_cache to clear the cache and force the next
    call to each query to re-read from the filesystem.
    """

    queries_dir = Path(__file__).parent / "queries"
    migrations_dir = Path(__file__).parent / "migrations"

    def __init__(self):
        self.clear_query_file_cache()

    def clear_query_file_cache(self):
        """Clears the cache of query files, causing subsequent calls to
        them to re-read the query from the filesystem."""
        self.query_cache = {}

    def read_query_file(self, query_name: str) -> None:
        """Reads the contents of a query file from the filesystem and
        caches it."""
        try:
            query_path = next(
                path
                for path in self.queries_dir.iterdir()
                if path.name.split(".")[0] == query_name
            )
        except StopIteration as stop:
            raise ValueError(f"Query {query_name} does not exist") from stop
        with query_path.open() as file:
            query = file.read()
        self.query_cache[query_name] = {
            "script": query_path.name.endswith(".script.sql"),
            "query": query,
        }

    def cache_named_query(self, query_name: str) -> None:
        """Reads an SQL query from the source and puts it to the cache,
        unless it is already present.

        :param query_name: The name of the query to execute, which must
        have a corresponding SQL file.
        """
        if query_name not in self.query_cache:
            self.read_query_file(query_name)

    def get_migrations(
        self, direction: Union[Literal["up"], Literal["down"]]
    ) -> List[str]:
        """Reads all migrations of the given direction from the migrations
        dir and arranges them into a list.

        The index to the list corresponds to the effective migration
        version after applying the migration for up migrations, and the
        version required to perform the migration for down migrations.
        """
        migrations: List[Tuple[int, str]] = []
        for path in self.migrations_dir.iterdir():
            if not path.name.endswith(f".{direction}.sql"):
                continue
            try:
                version = int(path.name.split("-")[0])
            except ValueError:
                continue
            with path.open() as file:
                migrations.append((version, file.read()))
        migrations.sort()
        for wanted, (version, _) in enumerate(migrations):
            if version != wanted:
                raise AttributeError(f"Migration version {version} missing")
        return [migration for _, migration in migrations]
