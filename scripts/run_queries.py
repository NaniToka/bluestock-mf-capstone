"""
run_queries.py
--------------
Executes each of the 10 business SQL queries from sql/queries.sql
against data/db/bluestock_mf.db and prints results to stdout.
"""

import sqlite3
import re
from pathlib import Path

DB_PATH    = Path("data/db/bluestock_mf.db")
QUERY_FILE = Path("sql/queries.sql")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row


def run_query(sql: str, label: str) -> None:
    cur = conn.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    col_w = [max(len(c), max((len(str(r[c])) for r in rows), default=0)) for c in cols]
    header = " | ".join(c.ljust(w) for c, w in zip(cols, col_w))
    sep    = "-+-".join("-" * w for w in col_w)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(header)
    print(sep)
    for row in rows:
        print(" | ".join(str(row[c]).ljust(w) for c, w in zip(cols, col_w)))
    print(f"  ({len(rows)} rows)")


if __name__ == "__main__":
    full_sql = QUERY_FILE.read_text(encoding="utf-8")

    # Split on "-- Q1:", "-- Q2:", etc.
    # Each block: first line = description, rest = SQL
    blocks = re.split(r"--\s+Q(\d+):\s+", full_sql)
    # blocks[0] = file header preamble
    # then alternating: number, body
    queries = []
    for i in range(1, len(blocks), 2):
        q_num  = blocks[i].strip()
        q_body = blocks[i + 1]
        # First non-empty line is the description (a comment like "Top 5 …")
        lines = q_body.splitlines()
        desc_line = lines[0].strip() if lines else f"Query {q_num}"
        # Remove dash-separator comment lines and blank leading lines
        sql_lines = []
        for line in lines[1:]:
            if re.match(r"^\s*--\s*─+", line):
                break  # stop at next separator
            sql_lines.append(line)
        sql_block = "\n".join(sql_lines).strip()
        # Take first complete SQL statement (up to ;)
        q_sql = sql_block.split(";")[0].strip()
        queries.append((f"Q{q_num}: {desc_line}", q_sql))

    for label, sql in queries:
        try:
            run_query(sql, label)
        except Exception as e:
            print(f"\n[ERROR] {label}: {e}")

    conn.close()
    print("\n✅ All 10 queries executed.")
