"""Verify every expected capture and stale seat using SQL on the source rows."""
import csv
import json
from math import isclose
from pathlib import Path
import sqlite3
import sys

data = json.loads((Path(__file__).resolve().parent/"result.json").read_text())
db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE events (user INTEGER, time REAL, flag INTEGER)")
with open(sys.argv[1], newline="") as f:
    rows = csv.reader(f)
    next(rows)
    db.executemany("INSERT INTO events VALUES (?,?,?)", ((r[0],r[2],r[3]) for r in rows))
db.execute("CREATE INDEX user_time ON events(user,time)")
directions = {"inactivity":"-last_seen", "few_actions":"-actions", "recent_activity":"last_seen",
              "many_actions":"actions","uniform":"0.0"}
for item in data["landmarks"].values():
    t, k = item["time"], item["seats"]
    db.execute("""CREATE TEMP TABLE roster AS SELECT user,MAX(CASE WHEN time<=? THEN time END) AS last_seen,
               SUM(time<=?) AS actions,MIN(CASE WHEN flag=1 THEN time END) AS exit_time
               FROM events GROUP BY user HAVING actions>0""",(t,t))
    for row in item["queues"]:
        lag = None if row["lag"]=="all" else t-int(row["lag"])*86400
        sql = f"""WITH blocks AS (
          SELECT {directions[row['method']]} AS score, COUNT(*) AS n, SUM(COALESCE(exit_time>?,0)) AS cases,
          SUM(COALESCE(exit_time<=?,0)) AS stale FROM roster
          WHERE ? IS NULL OR exit_time IS NULL OR exit_time>? GROUP BY score
        ), ranked AS (SELECT *,SUM(n) OVER(ORDER BY score DESC)-n AS above FROM blocks)
        SELECT SUM(n), SUM(cases*1.0*min(n,max(0,?-above))/n),
               SUM(stale*1.0*min(n,max(0,?-above))/n) FROM ranked"""
        n, captures, stale = db.execute(sql,(t,t,lag,lag,k,k)).fetchone()
        assert n==row["roster"] and isclose(captures,row["capture"],abs_tol=1e-9)
        assert isclose(stale,row["stale"],abs_tol=1e-9)
    db.execute("DROP TABLE roster")
print("Verified all 75 published queues.")
