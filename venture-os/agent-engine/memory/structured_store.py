# Relational data (PostgreSQL)
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    from sqlalchemy import create_engine, text, inspect as sa_inspect
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False


@dataclass
class QueryResult:
    """Result of a database query."""

    rows: List[Dict[str, Any]]
    row_count: int
    columns: List[str]
    execution_time_ms: float


class StructuredStore:
    """PostgreSQL-based relational data storage."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._engine = None
        self._session_factory = None
        self._connection = None
        self._connected = False
        self._pool = None
        # In-memory fallback: table -> list of row dicts
        self._mem: Dict[str, List[Dict[str, Any]]] = {}

    # ==================== Connection Management ====================

    def connect(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "agent_engine",
        user: str = "postgres",
        password: str = "",
    ) -> bool:
        """Connect to PostgreSQL database."""
        if _HAS_SQLALCHEMY:
            try:
                url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
                self._engine = create_engine(url, pool_pre_ping=True)
                self._session_factory = sessionmaker(bind=self._engine)
                # test connection
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self._connected = True
                return True
            except Exception:
                self._engine = None
        # SQLite in-memory fallback
        if _HAS_SQLALCHEMY:
            try:
                self._engine = create_engine(
                    "sqlite:///:memory:",
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
                self._session_factory = sessionmaker(bind=self._engine)
                self._connected = True
                return True
            except Exception:
                pass
        # Pure in-memory dict fallback
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect from database."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
        self._connected = False

    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected

    def create_pool(self, min_size: int = 1, max_size: int = 10) -> None:
        """Create connection pool."""
        # SQLAlchemy manages pooling internally; nothing to do here.
        pass

    def get_connection(self) -> Any:
        """Get connection from pool."""
        if self._engine:
            return self._engine.connect()
        return None

    def release_connection(self, conn: Any) -> None:
        """Release connection back to pool."""
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    def ping(self) -> bool:
        """Ping database."""
        if self._engine:
            try:
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return True
            except Exception:
                return False
        return self._connected

    # ==================== Query Operations ====================

    def _exec(
        self, query: str, params: Optional[Tuple] = None, fetch: bool = False
    ) -> Any:
        """Internal: execute raw query via SQLAlchemy or no-op."""
        if not self._engine:
            return None
        start = time.monotonic()
        with self._engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            if fetch:
                rows = result.fetchall()
                cols = list(result.keys()) if hasattr(result, "keys") else []
                return rows, cols, (time.monotonic() - start) * 1000
            return result.rowcount, [], (time.monotonic() - start) * 1000

    def execute(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute a query. Returns affected rows."""
        if self._engine:
            result = self._exec(query, params)
            return result[0] if result else 0
        return 0

    def query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        """Execute query and return results."""
        if self._engine:
            try:
                rows_raw, cols, ms = self._exec(query, params, fetch=True)
                rows = [dict(zip(cols, r)) for r in rows_raw]
                return QueryResult(
                    rows=rows, row_count=len(rows), columns=cols, execution_time_ms=ms
                )
            except Exception:
                pass
        return QueryResult(rows=[], row_count=0, columns=[], execution_time_ms=0.0)

    def query_one(
        self, query: str, params: Optional[Tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute query and return single row."""
        result = self.query(query, params)
        return result.rows[0] if result.rows else None

    def query_scalar(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute query and return single value."""
        row = self.query_one(query, params)
        if row:
            return next(iter(row.values()), None)
        return None

    # ==================== CRUD Operations ====================

    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """Insert a row. Returns inserted ID."""
        if self._engine:
            cols = ", ".join(data.keys())
            placeholders = ", ".join(f":{k}" for k in data.keys())
            q = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
            try:
                with self._engine.connect() as conn:
                    result = conn.execute(text(q), data)
                    conn.commit()
                    return result.lastrowid
            except Exception:
                pass
        # In-memory fallback
        self._mem.setdefault(table, [])
        row = dict(data)
        row.setdefault("_id", len(self._mem[table]) + 1)
        self._mem[table].append(row)
        return row["_id"]

    def insert_many(self, table: str, rows: List[Dict[str, Any]]) -> int:
        """Insert multiple rows. Returns count inserted."""
        count = 0
        for row in rows:
            if self.insert(table, row) is not None:
                count += 1
        return count

    def update(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> int:
        """Update rows. Returns count updated."""
        if self._engine:
            set_clause = ", ".join(f"{k} = :set_{k}" for k in data.keys())
            where_clause = " AND ".join(f"{k} = :where_{k}" for k in where.keys())
            params = {f"set_{k}": v for k, v in data.items()}
            params.update({f"where_{k}": v for k, v in where.items()})
            q = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            try:
                with self._engine.connect() as conn:
                    result = conn.execute(text(q), params)
                    conn.commit()
                    return result.rowcount
            except Exception:
                pass
        count = 0
        for row in self._mem.get(table, []):
            if all(row.get(k) == v for k, v in where.items()):
                row.update(data)
                count += 1
        return count

    def delete(self, table: str, where: Dict[str, Any]) -> int:
        """Delete rows. Returns count deleted."""
        if self._engine:
            where_clause = " AND ".join(f"{k} = :{k}" for k in where.keys())
            q = f"DELETE FROM {table} WHERE {where_clause}"
            try:
                with self._engine.connect() as conn:
                    result = conn.execute(text(q), where)
                    conn.commit()
                    return result.rowcount
            except Exception:
                pass
        before = len(self._mem.get(table, []))
        self._mem[table] = [
            r
            for r in self._mem.get(table, [])
            if not all(r.get(k) == v for k, v in where.items())
        ]
        return before - len(self._mem.get(table, []))

    def upsert(
        self, table: str, data: Dict[str, Any], conflict_columns: List[str]
    ) -> bool:
        """Insert or update on conflict."""
        where = {c: data[c] for c in conflict_columns if c in data}
        if self.exists(table, where):
            self.update(table, data, where)
        else:
            self.insert(table, data)
        return True

    def select(
        self,
        table: str,
        columns: List[str] = None,
        where: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None,
    ) -> List[Dict[str, Any]]:
        """Select rows from table."""

        if self._engine:
            cols = ", ".join(columns) if columns else "*"
            q = f"SELECT {cols} FROM {table}"
            params: Dict[str, Any] = {}
            if where:
                q += " WHERE " + " AND ".join(f"{k} = :{k}" for k in where.keys())
                params.update(where)
            if order_by:
                q += f" ORDER BY {order_by}"
            if limit is not None:
                q += f" LIMIT {limit}"
            if offset is not None:
                q += f" OFFSET {offset}"
            result = self.query(q, params or None)
            return result.rows
        rows = list(self._mem.get(table, []))
        if where:
            rows = [r for r in rows if all(r.get(k) == v for k, v in where.items())]
        if columns:
            rows = [{c: r.get(c) for c in columns} for r in rows]
        if offset:
            rows = rows[offset:]
        if limit is not None:
            rows = rows[:limit]
        return rows

    def select_one(self, table: str, where: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Select single row."""
        rows = self.select(table, where=where, limit=1)
        return rows[0] if rows else None

    def count(self, table: str, where: Optional[Dict[str, Any]] = None) -> int:
        """Count rows in table."""
        return len(self.select(table, where=where))

    def exists(self, table: str, where: Dict[str, Any]) -> bool:
        """Check if row exists."""
        return self.select_one(table, where) is not None

    # ==================== Transaction Management ====================

    def begin_transaction(self) -> None:
        """Begin a transaction."""
        if self._engine:
            self._connection = self._engine.connect()
            self._connection.begin()

    def commit(self) -> None:
        """Commit current transaction."""
        if self._connection:
            self._connection.commit()
            self._connection.close()
            self._connection = None

    def rollback(self) -> None:
        """Rollback current transaction."""
        if self._connection:
            self._connection.rollback()
            self._connection.close()
            self._connection = None

    @contextmanager
    def transaction(self) -> Any:
        """Context manager for transactions."""
        self.begin_transaction()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise

    # ==================== Schema Management ====================

    def create_table(
        self,
        table: str,
        columns: Dict[str, str],
        primary_key: Optional[str] = None,
        if_not_exists: bool = True,
    ) -> bool:
        """Create a table."""
        exists_clause = "IF NOT EXISTS " if if_not_exists else ""
        col_defs = []
        for col, dtype in columns.items():
            if col == primary_key:
                col_defs.append(f"{col} {dtype} PRIMARY KEY")
            else:
                col_defs.append(f"{col} {dtype}")
        q = f"CREATE TABLE {exists_clause}{table} ({', '.join(col_defs)})"
        if self._engine:
            try:
                with self._engine.connect() as conn:
                    conn.execute(text(q))
                    conn.commit()
                return True
            except Exception:
                return False
        self._mem.setdefault(table, [])
        return True

    def drop_table(self, table: str, if_exists: bool = True) -> bool:
        """Drop a table."""
        exists_clause = "IF EXISTS " if if_exists else ""
        q = f"DROP TABLE {exists_clause}{table}"
        if self._engine:
            try:
                with self._engine.connect() as conn:
                    conn.execute(text(q))
                    conn.commit()
                return True
            except Exception:
                return False
        self._mem.pop(table, None)
        return True

    def table_exists(self, table: str) -> bool:
        """Check if table exists."""
        if self._engine:
            try:
                insp = sa_inspect(self._engine)
                return insp.has_table(table)
            except Exception:
                pass
        return table in self._mem

    def list_tables(self) -> List[str]:
        """List all tables."""
        if self._engine:
            try:
                insp = sa_inspect(self._engine)
                return insp.get_table_names()
            except Exception:
                pass
        return list(self._mem.keys())

    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        """Get column information for table."""
        if self._engine:
            try:
                insp = sa_inspect(self._engine)
                return insp.get_columns(table)
            except Exception:
                pass
        rows = self._mem.get(table, [])
        if not rows:
            return []
        return [{"name": k, "type": type(v).__name__} for k, v in rows[0].items()]

    def add_column(self, table: str, column: str, data_type: str) -> bool:
        """Add column to table."""
        if self._engine:
            try:
                with self._engine.connect() as conn:
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {column} {data_type}")
                    )
                    conn.commit()
                return True
            except Exception:
                return False
        return True

    def drop_column(self, table: str, column: str) -> bool:
        """Drop column from table."""
        if self._engine:
            try:
                with self._engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {column}"))
                    conn.commit()
                return True
            except Exception:
                return False
        for row in self._mem.get(table, []):
            row.pop(column, None)
        return True

    # ==================== Index Management ====================

    def create_index(
        self,
        table: str,
        columns: List[str],
        index_name: Optional[str] = None,
        unique: bool = False,
    ) -> bool:
        """Create an index."""
        if not self._engine:
            return True
        name = index_name or f"idx_{table}_{'_'.join(columns)}"
        unique_kw = "UNIQUE " if unique else ""
        cols = ", ".join(columns)
        q = f"CREATE {unique_kw}INDEX IF NOT EXISTS {name} ON {table} ({cols})"
        try:
            with self._engine.connect() as conn:
                conn.execute(text(q))
                conn.commit()
            return True
        except Exception:
            return False

    def drop_index(self, index_name: str) -> bool:
        """Drop an index."""
        if not self._engine:
            return True
        try:
            with self._engine.connect() as conn:
                conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                conn.commit()
            return True
        except Exception:
            return False

    def list_indexes(self, table: str) -> List[Dict[str, Any]]:
        """List indexes on table."""
        if self._engine:
            try:
                insp = sa_inspect(self._engine)
                return insp.get_indexes(table)
            except Exception:
                pass
        return []

    # ==================== Utility ====================

    def truncate(self, table: str) -> bool:
        """Truncate table."""
        if self._engine:
            try:
                with self._engine.connect() as conn:
                    conn.execute(text(f"DELETE FROM {table}"))
                    conn.commit()
                return True
            except Exception:
                return False
        self._mem[table] = []
        return True

    def vacuum(self, table: Optional[str] = None) -> None:
        """Vacuum database or table."""
        if self._engine:
            try:
                with self._engine.connect().execution_options(
                    isolation_level="AUTOCOMMIT"
                ) as conn:
                    conn.execute(text("VACUUM"))
            except Exception:
                pass

    def analyze(self, table: Optional[str] = None) -> None:
        """Analyze database or table."""
        if self._engine:
            try:
                q = f"ANALYZE {table}" if table else "ANALYZE"
                with self._engine.connect() as conn:
                    conn.execute(text(q))
                    conn.commit()
            except Exception:
                pass

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return {
            "connected": self._connected,
            "backend": "sqlalchemy" if self._engine else "in-memory",
            "tables": self.list_tables(),
        }

    def get_table_size(self, table: str) -> int:
        """Get table size in bytes."""
        if self._engine:
            try:
                result = self.query_scalar(f"SELECT pg_total_relation_size('{table}')")
                return int(result) if result else 0
            except Exception:
                pass
        return len(str(self._mem.get(table, [])))

    def explain(self, query: str, params: Optional[Tuple] = None) -> str:
        """Explain query plan."""
        if self._engine:
            try:
                result = self.query(f"EXPLAIN {query}", params)
                return "\n".join(str(r) for r in result.rows)
            except Exception:
                pass
        return f"EXPLAIN not available (in-memory backend): {query}"
