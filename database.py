import os
import logging
import asyncio
from typing import Optional, List, Dict, Any
import asyncpg
import aiosqlite
import config

logger = logging.getLogger(__name__)

db_pool: Optional[asyncpg.Pool] = None
is_sqlite: bool = False
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "hamroh_bot.db")

async def init_sqlite():
    global is_sqlite
    is_sqlite = True
    logger.info("SQLite ma'lumotlar bazasiga ulanmoqda...")
    async with aiosqlite.connect(SQLITE_PATH) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                name TEXT,
                language TEXT DEFAULT 'uz',
                gender TEXT DEFAULT 'female',
                appeal TEXT,
                user_type TEXT CHECK (user_type IN ('keksa', 'bola')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_premium BOOLEAN DEFAULT 0,
                balance INTEGER DEFAULT 0
            );
        """)
        # Mavjud jadvalga yangi ustunlarni tekshirib qo'shish
        for col_def in [
            ("name", "TEXT"),
            ("language", "TEXT DEFAULT 'uz'"),
            ("gender", "TEXT DEFAULT 'female'"),
            ("appeal", "TEXT"),
            ("doctor_phone", "TEXT")
        ]:
            try:
                await conn.execute(f"ALTER TABLE users ADD COLUMN {col_def[0]} {col_def[1]};")
            except Exception:
                pass

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                dori_nomi TEXT NOT NULL,
                vaqt VARCHAR(5) NOT NULL,
                kunlar TEXT DEFAULT 'har_kuni',
                faol BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS points (
                user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                total_points INTEGER DEFAULT 0,
                badges TEXT DEFAULT '',
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reminder_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_id INTEGER,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                dori_nomi TEXT NOT NULL,
                scheduled_time VARCHAR(5),
                status TEXT DEFAULT 'sent',
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                taken_at TIMESTAMP
            );
        """)
        await conn.commit()
    logger.info("SQLite jadvallari muvaffaqiyatli ishga tushirildi.")

async def init_db():
    global db_pool, is_sqlite
    try:
        # Avval PostgreSQL ga urinib ko'ramiz
        logger.info("PostgreSQL ga ulanishga harakat qilinmoqda...")
        db_pool = await asyncpg.create_pool(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database="postgres",
            min_size=1,
            max_size=5,
            timeout=3
        )
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    user_type TEXT CHECK (user_type IN ('keksa', 'bola')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_premium BOOLEAN DEFAULT FALSE,
                    balance INTEGER DEFAULT 0
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    dori_nomi TEXT NOT NULL,
                    vaqt VARCHAR(5) NOT NULL,
                    kunlar TEXT DEFAULT 'har_kuni',
                    faol BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS points (
                    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                    total_points INTEGER DEFAULT 0,
                    badges TEXT[] DEFAULT '{}',
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS reminder_logs (
                    id SERIAL PRIMARY KEY,
                    reminder_id INTEGER,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    dori_nomi TEXT NOT NULL,
                    scheduled_time VARCHAR(5),
                    status TEXT DEFAULT 'sent',
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    taken_at TIMESTAMP
                );
            """)
        logger.info("PostgreSQL ma'lumotlar bazasi faol.")
        return db_pool
    except Exception as e:
        logger.warning(f"PostgreSQL ulanishida xatolik ({e}). Avtomatik SQLite rejimiga o'tilmoqda...")
        await init_sqlite()
        return True

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None
    if db_pool:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            return dict(row) if row else None
    return None

async def upsert_user(user_id: int, username: Optional[str], full_name: Optional[str], user_type: str = "keksa"):
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, full_name, user_type)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name,
                    user_type = excluded.user_type;
            """, (user_id, username, full_name, user_type))
            await conn.execute("""
                INSERT INTO points (user_id, total_points)
                VALUES (?, 0)
                ON CONFLICT(user_id) DO NOTHING;
            """, (user_id,))
            await conn.commit()
        return

    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, full_name, user_type)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE 
                SET username = EXCLUDED.username,
                    full_name = EXCLUDED.full_name,
                    user_type = EXCLUDED.user_type;
            """, user_id, username, full_name, user_type)
            await conn.execute("""
                INSERT INTO points (user_id, total_points)
                VALUES ($1, 0)
                ON CONFLICT (user_id) DO NOTHING;
            """, user_id)

async def set_user_language(user_id: int, lang: str):
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            await conn.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
            await conn.commit()
        return
    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute("UPDATE users SET language = $1 WHERE user_id = $2", lang, user_id)

async def set_user_profile(user_id: int, name: str, gender: str, appeal: str):
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            await conn.execute(
                "UPDATE users SET name = ?, gender = ?, appeal = ? WHERE user_id = ?",
                (name, gender, appeal, user_id)
            )
            await conn.commit()
        return
    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET name = $1, gender = $2, appeal = $3 WHERE user_id = $4",
                name, gender, appeal, user_id
            )

async def set_user_type(user_id: int, user_type: str):
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            await conn.execute("UPDATE users SET user_type = ? WHERE user_id = ?", (user_type, user_id))
            await conn.commit()
        return

    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute("UPDATE users SET user_type = $1 WHERE user_id = $2", user_type, user_id)

async def set_user_doctor_phone(user_id: int, phone: str):
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            await conn.execute("UPDATE users SET doctor_phone = ? WHERE user_id = ?", (phone, user_id))
            await conn.commit()
        return
    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute("UPDATE users SET doctor_phone = $1 WHERE user_id = $2", phone, user_id)



async def add_reminder(user_id: int, dori_nomi: str, vaqt: str, kunlar: str = "har_kuni") -> int:
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            cur = await conn.execute("""
                INSERT INTO reminders (user_id, dori_nomi, vaqt, kunlar, faol)
                VALUES (?, ?, ?, ?, 1)
            """, (user_id, dori_nomi, vaqt, kunlar))
            await conn.commit()
            return cur.lastrowid or 0

    if db_pool:
        async with db_pool.acquire() as conn:
            return await conn.fetchval("""
                INSERT INTO reminders (user_id, dori_nomi, vaqt, kunlar, faol)
                VALUES ($1, $2, $3, $4, TRUE)
                RETURNING id;
            """, user_id, dori_nomi, vaqt, kunlar)
    return 0

async def get_user_reminders(user_id: int) -> List[Dict[str, Any]]:
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT * FROM reminders WHERE user_id = ? AND faol = 1 ORDER BY vaqt ASC", (user_id,)) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    if db_pool:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM reminders WHERE user_id = $1 AND faol = TRUE ORDER BY vaqt ASC", user_id)
            return [dict(r) for r in rows]
    return []

async def delete_reminder(reminder_id: int, user_id: int) -> bool:
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            cur = await conn.execute("DELETE FROM reminders WHERE id = ? AND user_id = ?", (reminder_id, user_id))
            await conn.commit()
            return cur.rowcount > 0

    if db_pool:
        async with db_pool.acquire() as conn:
            res = await conn.execute("DELETE FROM reminders WHERE id = $1 AND user_id = $2", reminder_id, user_id)
            return "DELETE 1" in res
    return False

async def get_all_active_reminders_by_time(current_time_str: str) -> List[Dict[str, Any]]:
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT r.*, u.full_name, u.username, u.name, u.language, u.gender, u.appeal 
                FROM reminders r
                JOIN users u ON r.user_id = u.user_id
                WHERE r.faol = 1 AND r.vaqt = ?
            """, (current_time_str,)) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    if db_pool:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT r.*, u.full_name, u.username, u.name, u.language, u.gender, u.appeal 
                FROM reminders r
                JOIN users u ON r.user_id = u.user_id
                WHERE r.faol = TRUE AND r.vaqt = $1
            """, current_time_str)
            return [dict(r) for r in rows]
    return []

async def add_user_points(user_id: int, points: int) -> int:
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            await conn.execute("""
                UPDATE points 
                SET total_points = total_points + ?, last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (points, user_id))
            await conn.commit()
            async with conn.execute("SELECT total_points FROM points WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                return row[0] if row else 0

    if db_pool:
        async with db_pool.acquire() as conn:
            return await conn.fetchval("""
                UPDATE points 
                SET total_points = total_points + $1, last_activity = CURRENT_TIMESTAMP
                WHERE user_id = $2
                RETURNING total_points;
            """, points, user_id) or 0
    return 0

async def get_user_points(user_id: int) -> int:
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            async with conn.execute("SELECT total_points FROM points WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                return row[0] if row else 0

    if db_pool:
        async with db_pool.acquire() as conn:
            val = await conn.fetchval("SELECT total_points FROM points WHERE user_id = $1", user_id)
            return val or 0
    return 0

async def save_chat_message(user_id: int, role: str, content: str):
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            await conn.execute("""
                INSERT INTO chat_history (user_id, role, content)
                VALUES (?, ?, ?)
            """, (user_id, role, content))
            await conn.commit()
        return

    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chat_history (user_id, role, content)
                VALUES ($1, $2, $3);
            """, user_id, role, content)

async def get_recent_chat_history(user_id: int, limit: int = 6) -> List[Dict[str, str]]:
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT role, content FROM chat_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (user_id, limit)) as cur:
                rows = await cur.fetchall()
                return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    if db_pool:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT role, content FROM chat_history
                WHERE user_id = $1
                ORDER BY id DESC
                LIMIT $2
            """, user_id, limit)
            return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    return []

async def get_system_stats() -> Dict[str, int]:
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            async with conn.execute("SELECT COUNT(*) FROM users") as cur:
                users = (await cur.fetchone())[0]
            async with conn.execute("SELECT COUNT(*) FROM reminders WHERE faol = 1") as cur:
                reminders = (await cur.fetchone())[0]
            async with conn.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1") as cur:
                premium = (await cur.fetchone())[0]
            return {"users": users or 0, "reminders": reminders or 0, "premium": premium or 0}

    if db_pool:
        async with db_pool.acquire() as conn:
            users = await conn.fetchval("SELECT COUNT(*) FROM users")
            reminders = await conn.fetchval("SELECT COUNT(*) FROM reminders WHERE faol = TRUE")
            premium = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_premium = TRUE")
            return {"users": users or 0, "reminders": reminders or 0, "premium": premium or 0}
    return {"users": 0, "reminders": 0, "premium": 0}

async def log_reminder(reminder_id: int, user_id: int, dori_nomi: str, scheduled_time: str) -> int:
    """Yuborilgan dori eslatmasini monitoring uchun qayd etish"""
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            cur = await conn.execute("""
                INSERT INTO reminder_logs (reminder_id, user_id, dori_nomi, scheduled_time, status)
                VALUES (?, ?, ?, ?, 'sent')
            """, (reminder_id, user_id, dori_nomi, scheduled_time))
            await conn.commit()
            return cur.lastrowid or 0
    if db_pool:
        async with db_pool.acquire() as conn:
            return await conn.fetchval("""
                INSERT INTO reminder_logs (reminder_id, user_id, dori_nomi, scheduled_time, status)
                VALUES ($1, $2, $3, $4, 'sent')
                RETURNING id;
            """, reminder_id, user_id, dori_nomi, scheduled_time) or 0
    return 0

async def mark_reminder_taken(log_id: int, user_id: int) -> bool:
    """Foydalanuvchi dori ichganini tasdiqlaganda holatni yangilash"""
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            cur = await conn.execute("""
                UPDATE reminder_logs 
                SET status = 'taken', taken_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            """, (log_id, user_id))
            await conn.commit()
            return cur.rowcount > 0
    if db_pool:
        async with db_pool.acquire() as conn:
            res = await conn.execute("""
                UPDATE reminder_logs 
                SET status = 'taken', taken_at = CURRENT_TIMESTAMP
                WHERE id = $1 AND user_id = $2
            """, log_id, user_id)
            return "UPDATE 1" in res
    return False

async def get_health_report(user_id: int, days: int = 7) -> Dict[str, Any]:
    """Haftalik yoki oylik dori qabul qilish va sog'liq hisoboti"""
    if is_sqlite:
        async with aiosqlite.connect(SQLITE_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as taken,
                    SUM(CASE WHEN status != 'taken' THEN 1 ELSE 0 END) as missed
                FROM reminder_logs
                WHERE user_id = ? AND sent_at >= datetime('now', ?)
            """, (user_id, f"-{days} days")) as cur:
                stat_row = await cur.fetchone()
                total = stat_row["total"] if stat_row and stat_row["total"] else 0
                taken = stat_row["taken"] if stat_row and stat_row["taken"] else 0
                missed = stat_row["missed"] if stat_row and stat_row["missed"] else 0

            async with conn.execute("""
                SELECT id, dori_nomi, scheduled_time, status, sent_at, taken_at
                FROM reminder_logs
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 10
            """, (user_id,)) as cur:
                recent_rows = await cur.fetchall()
                recent_logs = [dict(r) for r in recent_rows]

            rate = round((taken / total * 100), 1) if total > 0 else 100.0
            return {
                "total": total,
                "taken": taken,
                "missed": missed,
                "rate": rate,
                "recent_logs": recent_logs,
                "days": days
            }

    if db_pool:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'taken') as taken,
                    COUNT(*) FILTER (WHERE status != 'taken') as missed
                FROM reminder_logs
                WHERE user_id = $1 AND sent_at >= NOW() - ($2 || ' days')::interval
            """, user_id, str(days))
            total = row["total"] if row and row["total"] else 0
            taken = row["taken"] if row and row["taken"] else 0
            missed = row["missed"] if row and row["missed"] else 0

            recent_rows = await conn.fetch("""
                SELECT id, dori_nomi, scheduled_time, status, sent_at, taken_at
                FROM reminder_logs
                WHERE user_id = $1
                ORDER BY id DESC
                LIMIT 10
            """, user_id)
            recent_logs = [dict(r) for r in recent_rows]

            rate = round((taken / total * 100), 1) if total > 0 else 100.0
            return {
                "total": total,
                "taken": taken,
                "missed": missed,
                "rate": rate,
                "recent_logs": recent_logs,
                "days": days
            }

    return {"total": 0, "taken": 0, "missed": 0, "rate": 100.0, "recent_logs": [], "days": days}


