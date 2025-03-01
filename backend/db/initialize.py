"""Initialize database

1. Initialize the database if it doesn't exist
2. Download CSV files from the enclave
3. Load the data from the CSV files into the database
"""
import os
import sys
from argparse import ArgumentParser
from pathlib import Path

from sqlalchemy.engine.base import Connection

THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = Path(THIS_DIR).parent.parent
# todo: why is this necessary in this case and almost never otherwise?
# https://stackoverflow.com/questions/33862963/python-cant-find-my-module
sys.path.insert(0, str(PROJECT_ROOT))
from backend.db.config import CONFIG
from backend.db.load import download_artefacts, indexes_and_derived_tables, initialize_test_schema, seed
from backend.db.utils import database_exists, run_sql, show_tables, get_db_connection, DB

SCHEMA = CONFIG['schema']


def create_database(con: Connection, schema: str):
    """Create the database"""
    show_tables(con)
    if not database_exists(con, DB):
        # noinspection PyUnresolvedReferences
        con.connection.connection.set_isolation_level(0)
        run_sql(con, 'CREATE DATABASE ' + DB)
        # noinspection PyUnresolvedReferences
        con.connection.connection.set_isolation_level(1)
    with get_db_connection(schema='') as con2:
        run_sql(con2, "CREATE TABLE IF NOT EXISTS public.manage ("
                      "key text not null, "
                      "value text);")
        run_sql(con2, "CREATE TABLE IF NOT EXISTS public.counts ("
                      "timestamp text not null, "
                      "date text, "
                      "schema text not null, "
                      '"table" text not null, '
                      "count integer not null, "
                      "delta integer not null);")
        run_sql(con2, "CREATE TABLE IF NOT EXISTS public.counts_runs ("
                      "timestamp text not null, "
                      "date text, "
                      "schema text not null, "
                      "note text);")
        run_sql(con, f'CREATE SCHEMA IF NOT EXISTS {schema};')


def initialize(
    clobber=False, schema: str = SCHEMA, local=False, create_db=False, download=True,
    download_force_if_exists=False, hours_threshold_for_updates=24
):
    """Initialize set up of DB

    :param local: If True, does this on local instead of production database.

    Resources
    - https://docs.sqlalchemy.org/en/20/core/engines.html
    - https://docs.sqlalchemy.org/en/20/dialects/mysql.html
    """
    with get_db_connection(local=local) as con:
        if create_db:
            create_database(con, schema)  # causing error. don't need it at the moment anyway
        if download:
            download_artefacts(force_download_if_exists=download_force_if_exists)
        seed(con, schema, clobber, hours_threshold_for_updates)
        indexes_and_derived_tables(con, schema)  # , start_step=30)
        initialize_test_schema(con, schema, local=local)


def cli():
    """Command line interface"""
    parser = ArgumentParser(description='Initializes DB.')
    parser.add_argument(
        '-D', '--clobber', action='store_true', default=False, help='If table exists, delete rows before seeding?')
    parser.add_argument(
        '-s', '--schema', default=SCHEMA, help='Name of the PostgreSQL scheam to create to store tables.')
    parser.add_argument(
        '-l', '--local', action='store_true', default=False,
        help='Use local database? If this is set, will use DB related environmental variables that end with _LOCAL.')
    parser.add_argument(
        '-c', '--create-db', action='store_true', default=False,
        help='Create the database "termhub", the "manage" table, and schema?')
    parser.add_argument(
        '-d', '--download', action='store_true', default=False,
        help='Download datasets necessary for seeding DB? Not needed if they\'ve already been downloaded.')
    parser.add_argument(
        '-f', '--download-force-if-exists', action='store_true', default=False,
        help='Force overwrite of existing dataset files?')
    parser.add_argument(
        '-t', '--hours-threshold-for-updates', default=24,
        help='Threshold for how many hours since last update before we require refreshes. If last update time was less '
             'than this, nothing will happen. Will evaluate this separately for downloads of local artefacts as well '
             'as uploading data to the DB.\n'
             'This is useful if expecting errors to happen during table creation / seeding process, and you don\'t want'
             ' to start over from the beginning.')
    initialize(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
