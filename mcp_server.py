import psycopg2
import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

app = Server("asx-stock-server")

def run_query(sql: str):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(sql)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return columns, rows

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="query_asx_stocks",
            description="Run a SQL query against the ASX stocks database. The table is called asx_stocks with columns: ticker, date, open, high, low, close, volume.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to run"
                    }
                },
                "required": ["sql"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_asx_stocks":
        sql = arguments["sql"]
        try:
            columns, rows = run_query(sql)
            result = {"columns": columns, "rows": [list(r) for r in rows]}
            return [TextContent(type="text", text=json.dumps(result, default=str))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())