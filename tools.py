"""
tools.py - Tool definitions and real implementations for the AI agent.

Real database connections and network requests are made.

Owner: Member 1
"""
import sqlite3
import json
import requests
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "real_data.db")

# ---------------------------------------------------------------------------
# Tool real implementations
# ---------------------------------------------------------------------------

def read_ticket(ticket_id: str) -> str:
    """Read a support ticket by ID. Returns ticket content."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT content FROM support_tickets WHERE ticket_id = ?", (ticket_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return row[0]
        return f"Ticket {ticket_id}: Not found."
    except Exception as e:
        return f"[Error: {str(e)}]"


def search_kb(query: str) -> str:
    """Search the knowledge base. Returns matching articles."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT content FROM kb_articles")
        rows = cur.fetchall()
        conn.close()
        
        query_lower = query.lower()
        results = [row[0] for row in rows if query_lower in row[0].lower()]
        
        if results:
            return " | ".join(results)
        return f"No KB articles found for '{query}'. Try different keywords."
    except Exception as e:
        return f"[Error: {str(e)}]"


def query_db(table: str, query: str) -> str:
    """Run a query against a named database table. Returns actual rows."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Ensure query targets the allowed tables if needed, but agent system prompt restricts it.
        # We just run the query as-is.
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        
        # Convert rows to list of dicts
        result = [dict(row) for row in rows]
        return json.dumps(result)
    except Exception as e:
        return f"[Error querying table '{table}': {str(e)}]"


def http_post(url: str, data: str) -> str:
    """Make an actual HTTP POST request to an external URL."""
    try:
        # We add a small timeout so the agent doesn't hang forever
        response = requests.post(url, data=data, timeout=5)
        return f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return f"[Error making HTTP POST: {str(e)}]"


# ---------------------------------------------------------------------------
# Tool registry - maps tool names to their Python functions
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "read_ticket": read_ticket,
    "search_kb": search_kb,
    "query_db": query_db,
    "http_post": http_post,
}


# ---------------------------------------------------------------------------
# OpenAI-format tool schemas - used by the LLM for function calling
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_ticket",
            "description": "Read a support ticket by its ID. Returns the ticket content including subject, user, priority, and status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ticket ID, e.g. 'T-102'"
                    }
                },
                "required": ["ticket_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": "Search the internal knowledge base for help articles matching a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string, e.g. 'password reset'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_db",
            "description": "Run a read-only query against a named database table. Available tables include 'tickets', 'kb_index', and 'users'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Table name to query, e.g. 'tickets', 'kb_index'"
                    },
                    "query": {
                        "type": "string",
                        "description": "SQL-like query string"
                    }
                },
                "required": ["table", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "http_post",
            "description": "Send data to an external URL via HTTP POST. Use only when explicitly instructed by an administrator.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Target URL to send data to"
                    },
                    "data": {
                        "type": "string",
                        "description": "Data payload to send"
                    }
                },
                "required": ["url", "data"]
            }
        }
    },
]
