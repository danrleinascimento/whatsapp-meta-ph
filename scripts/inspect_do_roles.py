# -*- coding: utf-8 -*-
import os
import psycopg2

url = os.environ["DATABASE_URL"]
conn = psycopg2.connect(url)
conn.autocommit = True
cur = conn.cursor()

checks = [
    "SELECT pg_has_role(current_user, 'pg_database_owner', 'USAGE')",
    "SELECT pg_has_role(current_user, 'pg_database_owner', 'MEMBER')",
    "SELECT r.rolname FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid JOIN pg_roles u ON u.oid=m.member WHERE u.rolname=current_user",
    "SELECT datname, pg_catalog.pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()",
    "SELECT usename FROM pg_user ORDER BY 1",
    "SELECT rolname FROM pg_roles WHERE rolcanlogin ORDER BY 1",
]
for q in checks:
    try:
        cur.execute(q)
        print(q, "=>", cur.fetchall())
    except Exception as e:
        print(q, "ERR", e)
        conn.rollback()
        conn.autocommit = True

# try create table directly
try:
    cur.execute("CREATE TABLE IF NOT EXISTS _ph_perm_test(id int)")
    print("CREATE TABLE OK")
    cur.execute("DROP TABLE IF EXISTS _ph_perm_test")
except Exception as e:
    print("CREATE TABLE ERR", e)

cur.close()
conn.close()
