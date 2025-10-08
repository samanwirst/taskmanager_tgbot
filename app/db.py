import asyncpg
from typing import List, Dict, Optional

class Database:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[asyncpg.pool.Pool] = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(dsn=self.dsn, min_size=1, max_size=5)
        await self._create_tables()

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def _create_tables(self):
        assert self.pool
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    fullname TEXT
                );
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    task_text TEXT NOT NULL,
                    "user" BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    urgency INT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                );
                """
            )
            await conn.execute(
                """
                ALTER TABLE tasks
                ADD COLUMN IF NOT EXISTS done BOOLEAN DEFAULT false;
                """
            )
            await conn.execute(
                """
                ALTER TABLE tasks
                ADD COLUMN IF NOT EXISTS done_at TIMESTAMP WITH TIME ZONE;
                """
            )

    async def upsert_user(self, user_id: int, username: Optional[str], fullname: Optional[str]):
        assert self.pool
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (user_id, username, fullname)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE
                SET username = EXCLUDED.username,
                    fullname = EXCLUDED.fullname;
                """,
                user_id, username, fullname
            )

    async def add_task(self, user_id: int, task_text: str, urgency: int) -> int:
        assert self.pool
        async with self.pool.acquire() as conn:
            rec = await conn.fetchrow(
                """
                INSERT INTO tasks (task_text, "user", urgency)
                VALUES ($1, $2, $3)
                RETURNING id;
                """,
                task_text, user_id, urgency
            )
            return rec["id"]

    async def get_tasks(self, user_id: int) -> List[Dict]:
        assert self.pool
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, task_text, urgency, created_at
                FROM tasks
                WHERE "user" = $1 AND done = false
                ORDER BY urgency ASC, created_at ASC;
                """,
                user_id
            )
            return [
                {
                    "id": r["id"],
                    "task_text": r["task_text"],
                    "urgency": r["urgency"],
                    "created_at": r["created_at"]
                }
                for r in rows
            ]

    async def get_history(self, user_id: int) -> List[Dict]:
        assert self.pool
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, task_text, urgency, created_at, done, done_at
                FROM tasks
                WHERE "user" = $1
                ORDER BY created_at ASC;
                """,
                user_id
            )
            return [
                {
                    "id": r["id"],
                    "task_text": r["task_text"],
                    "urgency": r["urgency"],
                    "created_at": r["created_at"],
                    "done": bool(r["done"]),
                    "done_at": r["done_at"]
                }
                for r in rows
            ]

    async def delete_task(self, task_id: int, user_id: int) -> bool:
        assert self.pool
        async with self.pool.acquire() as conn:
            res = await conn.execute(
                """
                UPDATE tasks
                SET done = true, done_at = now()
                WHERE id = $1 AND "user" = $2;
                """,
                task_id, user_id
            )
            return res.endswith("1")