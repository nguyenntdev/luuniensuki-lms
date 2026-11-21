"""Reconstruct registration joins and tie-weighted review counts independently in SQLite."""
import csv
import gzip
import hashlib
import io
import sqlite3
import sys
import zipfile
from pathlib import Path

archive_path, run = map(Path, sys.argv[1:])
with archive_path.open("rb") as source:
    assert hashlib.file_digest(source, "sha256").hexdigest() == "f2ed1902616c1fe8d2824d872c0b7d2d72be435bf0124d077044fe4be2c6d3e4"
with zipfile.ZipFile(archive_path) as archive:
    def read(member):
        return list(csv.DictReader(io.TextIOWrapper(archive.open(member+".csv"))))
    registration = {(r["code_module"], r["id_student"]):r for r in read("studentRegistration")
                    if r["code_presentation"] == "2014J" and r["date_registration"] not in ("","?")
                    and int(r["date_registration"]) <= 60}
    roster = [r for r in read("studentInfo") if r["code_presentation"] == "2014J"
              and (r["code_module"], r["id_student"]) in registration]

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE scores(module TEXT,exit INTEGER,y INTEGER,catboost_all REAL,logit_all REAL,uniform REAL)")
users = {key:i for i,key in enumerate(sorted({int(r["id_student"]) for r in roster}))}
with gzip.open(Path(__file__).resolve().parents[1]/"run/predictions.csv.gz", "rt") as f:
    for r, pred in zip(roster, csv.DictReader(f), strict=True):
        module = r["code_module"]
        date = registration[module, r["id_student"]]["date_unregistration"]
        exit_day = None if date in ("","?") else int(date)
        y = r["final_result"] == "Withdrawn"
        assert users[int(r["id_student"])] == int(pred["learner"])
        assert (pred["eligible"] == "True") == (exit_day is None or exit_day > 60)
        assert (pred["outcome"] == "True") == y
        db.execute("INSERT INTO scores VALUES(?,?,?,?,?,?)",
                   (module, exit_day, y, float(pred["catboost_all"]), float(pred["logit_all"]), 0.))
query = """
WITH pool AS (
 SELECT *, exit <= 60 AS exited, COALESCE(exit > 60,1) AS eligible
 FROM scores WHERE module=:module AND (:cut IS NULL OR exit IS NULL OR exit>:cut)
), ranked AS (
 SELECT *, RANK() OVER(ORDER BY {method} DESC)-1 AS higher,
 COUNT(*) OVER(PARTITION BY {method}) AS tied FROM pool
), weights AS (
 SELECT *, MAX(0., MIN(1., (:budget-higher)*1./tied)) AS w FROM ranked
) SELECT SUM(w), SUM(w*COALESCE(exited,0)), SUM(w*eligible*y), SUM(eligible*y) FROM weights
"""
checked = set()
with (run/"modules.csv").open() as f:
    for r in csv.DictReader(f):
        method = r["model"]
        assert method in ("catboost_all","logit_all","uniform")
        n = db.execute("SELECT COUNT(*) FROM scores WHERE module=? AND (exit IS NULL OR exit>60)",
                       [r["module"]]).fetchone()[0]
        params = dict(module=r["module"], budget=n*int(r["percent"])//100,
                      cut=None if r["lag"] == "all" else 60-int(r["lag"]))
        actual = db.execute(query.format(method=method),params).fetchone()
        expected = [float(r[k]) for k in ("seats","stale_seats","captured","eligible_cases")]
        assert max(abs(a-b) for a,b in zip(actual,expected)) < 1e-7
        checked.add((r["module"], r["percent"], method, r["lag"]))
assert len(checked) == 7*3*3*6
print(len(checked), "module-policy-budget-lag combinations verified")
