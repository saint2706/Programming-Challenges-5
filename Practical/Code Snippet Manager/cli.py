import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from pygments import highlight
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexers import TextLexer, get_lexer_by_name, guess_lexer


class SnippetStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                language TEXT NOT NULL,
                code TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snippet_tags (
                snippet_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (snippet_id, tag_id),
                FOREIGN KEY (snippet_id) REFERENCES snippets(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );
            """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snippets_title ON snippets(title);
            """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snippets_code ON snippets(code);
            """)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def _get_or_create_tag_ids(self, tags: Iterable[str]) -> List[int]:
        tag_ids: List[int] = []
        cursor = self.conn.cursor()
        for tag in tags:
            tag = tag.strip()
            if not tag:
                continue
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
            row = cursor.fetchone()
            if row:
                tag_ids.append(row[0])
                continue
            cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag,))
            tag_ids.append(cursor.lastrowid)
        return tag_ids

    def add_snippet(
        self,
        title: str,
        language: str,
        code: str,
        tags: Optional[Iterable[str]] = None,
        created_at: Optional[str] = None,
    ) -> int:
        created_value = created_at or datetime.utcnow().isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO snippets (title, language, code, created_at) VALUES (?, ?, ?, ?)",
            (title, language, code, created_value),
        )
        snippet_id = cursor.lastrowid
        if tags:
            tag_ids = self._get_or_create_tag_ids(tags)
            cursor.executemany(
                "INSERT OR IGNORE INTO snippet_tags (snippet_id, tag_id) VALUES (?, ?)",
                [(snippet_id, tag_id) for tag_id in tag_ids],
            )
        self.conn.commit()
        return snippet_id

    def list_snippets(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.id, s.title, s.language, s.created_at, GROUP_CONCAT(t.name, ',') AS tags
            FROM snippets s
            LEFT JOIN snippet_tags st ON s.id = st.snippet_id
            LEFT JOIN tags t ON t.id = st.tag_id
            GROUP BY s.id
            ORDER BY s.created_at DESC;
            """)
        return cursor.fetchall()

    def search_snippets(
        self, keywords: Optional[List[str]] = None, tags: Optional[List[str]] = None
    ):
        keywords = keywords or []
        tags = [tag.strip() for tag in tags or [] if tag.strip()]
        params: List[str] = []
        where_clauses = []

        for keyword in keywords:
            where_clauses.append("(s.title LIKE ? OR s.code LIKE ?)")
            pattern = f"%{keyword}%"
            params.extend([pattern, pattern])

        base_query = """
            SELECT s.id, s.title, s.language, s.code, s.created_at, GROUP_CONCAT(t.name, ',') AS tags
            FROM snippets s
            LEFT JOIN snippet_tags st ON s.id = st.snippet_id
            LEFT JOIN tags t ON t.id = st.tag_id
            {where_clause}
            GROUP BY s.id
            {having_clause}
            ORDER BY s.created_at DESC;
            """

        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)

        having_clause = ""
        if tags:
            placeholders = ",".join("?" for _ in tags)
            having_clause = (
                "HAVING COUNT(DISTINCT CASE WHEN t.name IN ("
                + placeholders
                + ") THEN t.name END) = ?"
            )
            params.extend(tags)
            params.append(len(tags))

        query = base_query.format(
            where_clause=where_clause, having_clause=having_clause
        )
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_snippet(self, snippet_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT s.id, s.title, s.language, s.code, s.created_at, GROUP_CONCAT(t.name, ',') AS tags
            FROM snippets s
            LEFT JOIN snippet_tags st ON s.id = st.snippet_id
            LEFT JOIN tags t ON t.id = st.tag_id
            WHERE s.id = ?
            GROUP BY s.id;
            """,
            (snippet_id,),
        )
        return cursor.fetchone()

    def export_json(self, output_path: Path) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.id, s.title, s.language, s.code, s.created_at,
                   COALESCE(GROUP_CONCAT(t.name, ','), '') AS tags
            FROM snippets s
            LEFT JOIN snippet_tags st ON s.id = st.snippet_id
            LEFT JOIN tags t ON t.id = st.tag_id
            GROUP BY s.id
            ORDER BY s.id;
            """)
        data = []
        for row in cursor.fetchall():
            snippet_id, title, language, code, created_at, tags = row
            tag_list = [tag for tag in (tags or "").split(",") if tag]
            data.append(
                {
                    "id": snippet_id,
                    "title": title,
                    "language": language,
                    "code": code,
                    "created_at": created_at,
                    "tags": tag_list,
                }
            )

        output_path.write_text(json.dumps(data, indent=2))

    def import_json(self, input_path: Path) -> int:
        payload = json.loads(input_path.read_text())
        added = 0
        for entry in payload:
            self.add_snippet(
                title=entry["title"],
                language=entry.get("language", "text"),
                code=entry["code"],
                tags=entry.get("tags", []),
                created_at=entry.get("created_at"),
            )
            added += 1
        return added


def highlight_code(code: str, language: str) -> str:
    lexer = None
    try:
        lexer = get_lexer_by_name(language)
    except Exception:
        try:
            lexer = guess_lexer(code)
        except Exception:
            lexer = TextLexer()
    formatter = TerminalFormatter()
    return highlight(code, lexer, formatter)


def read_code(args: argparse.Namespace) -> str:
    if args.code:
        return args.code
    if args.file:
        if args.file == "-":
            return sys.stdin.read()
        return Path(args.file).read_text()
    raise SystemExit("Provide --code or --file (use '-' to read from stdin)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage code snippets with tagging and search."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).with_name("snippets.db"),
        help="Path to the SQLite database file (default: snippets.db next to the CLI).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new snippet")
    add_parser.add_argument("title", help="Title for the snippet")
    add_parser.add_argument(
        "language", help="Programming language for syntax highlighting"
    )
    add_parser.add_argument("--code", help="Code content as a string")
    add_parser.add_argument(
        "--file", help="Path to a file containing the code or '-' for stdin"
    )
    add_parser.add_argument(
        "--tag", action="append", help="Tags to associate with the snippet", default=[]
    )

    list_parser = subparsers.add_parser("list", help="List all snippets")
    list_parser.add_argument("--limit", type=int, help="Limit the number of results")

    search_parser = subparsers.add_parser(
        "search", help="Search snippets by keywords and tags"
    )
    search_parser.add_argument(
        "--keyword", action="append", help="Keyword to search in title or code"
    )
    search_parser.add_argument(
        "--tag", action="append", help="Tag that must be present on the snippet"
    )

    show_parser = subparsers.add_parser("show", help="Show a snippet in detail")
    show_parser.add_argument(
        "snippet_id", type=int, help="ID of the snippet to display"
    )

    export_parser = subparsers.add_parser("export", help="Export all snippets to JSON")
    export_parser.add_argument(
        "output", type=Path, help="Destination path for the JSON export"
    )

    import_parser = subparsers.add_parser(
        "import", help="Import snippets from a JSON file"
    )
    import_parser.add_argument("input", type=Path, help="JSON file to import")

    return parser.parse_args()


def main():
    args = parse_args()
    store = SnippetStore(args.db)
    try:
        if args.command == "add":
            code = read_code(args)
            snippet_id = store.add_snippet(
                args.title, args.language, code, tags=args.tag
            )
            print(f"Added snippet #{snippet_id}: {args.title}")
        elif args.command == "list":
            for row in store.list_snippets()[: args.limit if args.limit else None]:
                snippet_id, title, language, created_at, tags = row
                tag_display = f" [tags: {tags}]" if tags else ""
                print(
                    f"#{snippet_id} | {title} ({language}) | {created_at}{tag_display}"
                )
        elif args.command == "search":
            results = store.search_snippets(keywords=args.keyword, tags=args.tag)
            if not results:
                print("No snippets found.")
            for snippet_id, title, language, code, created_at, tags in results:
                tag_display = f" [tags: {tags}]" if tags else ""
                print(
                    f"\n#{snippet_id} | {title} ({language}) | {created_at}{tag_display}"
                )
                print(highlight_code(code, language))
        elif args.command == "show":
            record = store.get_snippet(args.snippet_id)
            if not record:
                print(f"Snippet #{args.snippet_id} not found.")
            else:
                snippet_id, title, language, code, created_at, tags = record
                tag_display = f" [tags: {tags}]" if tags else ""
                print(
                    f"#{snippet_id} | {title} ({language}) | {created_at}{tag_display}"
                )
                print(highlight_code(code, language))
        elif args.command == "export":
            store.export_json(args.output)
            print(f"Exported snippets to {args.output}")
        elif args.command == "import":
            added = store.import_json(args.input)
            print(f"Imported {added} snippets from {args.input}")
    finally:
        store.close()


if __name__ == "__main__":
    main()
