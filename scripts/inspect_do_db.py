# -*- coding: utf-8 -*-
import os
import sys

import psycopg2

url = os.environ.get("DATABASE_URL")
if not url:
    print("ERRO: DATABASE_URL")
    sys.exit(1)

conn = psycopg2.connect(url)
conn.autocommit = True
cur = conn.cursor()
cur.execute("select current_user, session_user, current_database()")
print("user", cur.fetchone())
cur.execute(
    "SELECT nspname, pg_catalog.pg_get_userbyid(nspowner) "
    "FROM pg_namespace WHERE nspname='public'"
)
print("public owner", cur.fetchone())
cur.execute(
    "SELECT has_schema_privilege(current_user, 'public', 'CREATE'), "
    "has_schema_privilege(current_user, 'public', 'USAGE')"
)
print("create,usage", cur.fetchone())
cur.execute(
    "SELECT rolname, rolsuper, rolcreaterole, rolcreatedb "
    "FROM pg_roles WHERE rolname = current_user"
)
print("role", cur.fetchone())
cur.execute(
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema='public' ORDER BY 1"
)
print("tables", [r[0] for r in cur.fetchall()])
# try grant to self (may fail)
for stmt in [
    "GRANT USAGE, CREATE ON SCHEMA public TO CURRENT_USER",
    'GRANT ALL ON SCHEMA public TO "whatsapp-meta-db"',
    "CREATE SCHEMA IF NOT EXISTS whatsapp AUTHORIZATION CURRENT_USER",
]:
    try:
        cur.execute(stmt)
        print("OK", stmt)
    except Exception as e:
        print("FAIL", stmt, "->", e)
cur.close()
conn.close()
