import os
import json
import csv
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger

# Try to use a POSIX file lock for cross-process safety (macOS/Linux)
try:
    import fcntl  # type: ignore
    HAS_FCNTL = True
except Exception:
    HAS_FCNTL = False


class TicketManager:
    """
    Simple ticket numbering and registry with daily counter reset.

    - Generates sequential ticket IDs of the form: TKT-YYYYMMDD-0001
    - Persists a daily counter to disk
    - Logs created tickets to CSV and JSONL for auditing/search
    - Uses file locking (fcntl) when available to handle concurrent writers
    """

    def __init__(self, data_dir: str = "ai-agent/data", prefix: str = "TKT"):
        self.data_dir = data_dir
        self.prefix = prefix
        self.counter_path = os.path.join(self.data_dir, "ticket_counter.json")
        self.csv_path = os.path.join(self.data_dir, "tickets.csv")
        self.jsonl_path = os.path.join(self.data_dir, "tickets.jsonl")
        self.lock_path = os.path.join(self.data_dir, "tickets.lock")

        os.makedirs(self.data_dir, exist_ok=True)
        # Ensure files exist
        if not os.path.exists(self.counter_path):
            self._write_counter({"date": self._today_str(), "seq": 0})

        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "ticket_id",
                        "date",
                        "seq",
                        "created_at",
                        "user_id",
                        "subject",
                        "channel",
                        "metadata_json",
                    ],
                )
                writer.writeheader()

        if not os.path.exists(self.jsonl_path):
            with open(self.jsonl_path, "w", encoding="utf-8") as _:
                pass  # just create the file

    # -----------------------
    # Public API
    # -----------------------

    def create_ticket(
        self,
        user_id: Optional[str] = None,
        subject: Optional[str] = None,
        channel: Optional[str] = "whatsapp",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new ticket, incrementing the daily counter and persisting the record.
        """
        with self._locked_section():
            counter = self._read_counter()
            today = self._today_str()

            if counter.get("date") != today:
                # Reset counter for a new day
                logger.info(f"Resetting ticket counter for new day: {today}")
                counter = {"date": today, "seq": 0}

            counter["seq"] += 1
            self._write_counter(counter)

            ticket_id = f"{self.prefix}-{today}-{counter['seq']:04d}"
            created_at = datetime.now().isoformat()

            record: Dict[str, Any] = {
                "ticket_id": ticket_id,
                "date": today,
                "seq": counter["seq"],
                "created_at": created_at,
                "user_id": user_id,
                "subject": subject,
                "channel": channel,
                "metadata": metadata or {},
            }

            # Persist to CSV
            self._append_csv(record)
            # Persist to JSONL
            self._append_jsonl(record)

            logger.info(f"Created ticket {ticket_id}")
            return record

    def get_counter(self) -> Dict[str, Any]:
        """
        Return the current counter state and the last ticket id for today (if any).
        """
        counter = self._read_counter()
        date = counter.get("date", self._today_str())
        seq = int(counter.get("seq", 0))
        last_ticket_id = f"{self.prefix}-{date}-{seq:04d}" if seq > 0 else None
        return {
            "date": date,
            "seq": seq,
            "last_ticket_id": last_ticket_id,
            "prefix": self.prefix,
        }

    def list_tickets(self, date: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List tickets for a given date (YYYYMMDD). Defaults to today if not provided.
        Returns up to `limit` most recent tickets for that date.
        """
        date_str = date or self._today_str()
        results: List[Dict[str, Any]] = []
        try:
            # Read JSONL and filter by date
            with open(self.jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        if obj.get("date") == date_str:
                            results.append(obj)
                    except Exception:
                        continue
            # Return most recent first
            results.sort(key=lambda x: (x.get("date", ""), int(x.get("seq", 0))), reverse=True)
            return results[:limit]
        except FileNotFoundError:
            return []

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single ticket by ID by scanning JSONL (sufficient for modest volumes).
        """
        try:
            with open(self.jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        if obj.get("ticket_id") == ticket_id:
                            return obj
                    except Exception:
                        continue
        except FileNotFoundError:
            return None
        return None

    # -----------------------
    # Internal helpers
    # -----------------------

    def _append_csv(self, record: Dict[str, Any]) -> None:
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "ticket_id",
                    "date",
                    "seq",
                    "created_at",
                    "user_id",
                    "subject",
                    "channel",
                    "metadata_json",
                ],
            )
            row = {
                "ticket_id": record["ticket_id"],
                "date": record["date"],
                "seq": record["seq"],
                "created_at": record["created_at"],
                "user_id": record.get("user_id"),
                "subject": record.get("subject"),
                "channel": record.get("channel"),
                "metadata_json": json.dumps(record.get("metadata") or {}, ensure_ascii=False),
            }
            writer.writerow(row)

    def _append_jsonl(self, record: Dict[str, Any]) -> None:
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _today_str(self) -> str:
        return datetime.now().strftime("%Y%m%d")

    def _read_counter(self) -> Dict[str, Any]:
        try:
            with open(self.counter_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"date": self._today_str(), "seq": 0}
        except Exception as e:
            logger.error(f"Error reading counter file: {e}")
            return {"date": self._today_str(), "seq": 0}

    def _write_counter(self, counter: Dict[str, Any]) -> None:
        tmp_path = self.counter_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(counter, f, ensure_ascii=False)
        # Atomic replace
        os.replace(tmp_path, self.counter_path)

    # -----------------------
    # Locking helpers
    # -----------------------

    def _locked_section(self):
        """
        Context manager for file-based locking across processes (when fcntl is available).
        Falls back to a dummy context manager if not supported.
        """
        class _Dummy:
            def __enter__(self_nonlocal):
                return None

            def __exit__(self_nonlocal, exc_type, exc, tb):
                return False

        if not HAS_FCNTL:
            return _Dummy()

        class _FlockContext:
            def __init__(self_outer, lock_file_path: str):
                self_outer.lock_file_path = lock_file_path
                self_outer._fh = None

            def __enter__(self_outer):
                # Open lock file and acquire exclusive lock
                self_outer._fh = open(self_outer.lock_file_path, "a+")
                fcntl.flock(self_outer._fh, fcntl.LOCK_EX)
                return self_outer

            def __exit__(self_outer, exc_type, exc, tb):
                try:
                    if self_outer._fh:
                        fcntl.flock(self_outer._fh, fcntl.LOCK_UN)
                        self_outer._fh.close()
                except Exception:
                    pass
                return False

        return _FlockContext(self.lock_path)
