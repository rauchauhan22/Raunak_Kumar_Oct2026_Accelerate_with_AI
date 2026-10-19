import pandas as pd
import glob
import os
from datetime import datetime
import duckdb
from core.connection_req import make_connection 

def inspect_gold(gold_parquet_path):
    files=glob.glob(f'{gold_parquet_path}/*.parquet')
    results={}
    for g in files:
        pq_file=pd.read_parquet(f'{g}')
        results[g]={"shape": pq_file.shape,"sample": pq_file.head(3)}
    return results

def load_data(gold_parquet_path):
    db=duckdb.connect()
    files=glob.glob(f'{gold_parquet_path}/*.parquet')
    for f in files:
        table_name=f.split("\\")[-1].replace(".parquet","")
        db.execute(f"Create TABLE {table_name} AS select * from read_parquet('{f}')")
    return db

def execute_query(db,business_question):
    client=make_connection()
    tables=db.execute("SHOW TABLES").df()["name"].tolist()
    schema_description="\n".join(
        f"- {table} (columns: {', '.join(f'{row.column_name} {row.column_type}' for row in db.execute(f'DESCRIBE {table}').df().itertuples() if not row.column_name.startswith('pk_'))})"
        for table in tables
    )
    query=client.responses.create(input=f"""You are a SQL query generator expert who takes a question from the business and generates a valid DuckDB SQL query for the available tables below. Only use the exact table and column names listed, with their given data types. As output you only produce the SQL query and nothing else.
    Only join tables on columns that share the same name and a compatible data type. Never join a string/VARCHAR column with a numeric/BIGINT column. Prefer the simplest query, using as few tables as possible, that answers the question.
    Available tables:
    {schema_description}
    Generate a query for {business_question}""",model="openai/gpt-oss-20b").output[1].content[0].text
    return db.execute(query).df()

def generate_html_report(business_question, result_df, object_name="pipeline"):
    """Render the business question and its answer as a standalone HTML report."""
    os.makedirs("reports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"reports/report_{object_name}_{timestamp}.html"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Retail Medallion Pipeline — Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2rem; color: #222; }}
        h1 {{ color: #2c3e50; }}
        .question {{ font-size: 1.1rem; font-weight: bold; margin: 1rem 0; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #2c3e50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .meta {{ color: #666; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <h1>Retail Medallion Pipeline — Report</h1>
    <p class="meta">Dataset: {object_name} &middot; Generated: {timestamp}</p>
    <p class="question">Business question: {business_question}</p>
    {result_df.to_html(index=False)}
</body>
</html>"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    return report_path

def main():
    gold_parquet_path = "data/gold"
    inspection_results = inspect_gold(gold_parquet_path)
    # print(inspection_results)
    db = load_data(gold_parquet_path)
    execute_query(db,business_question="Which region had the highest total sales?")

if __name__ == "__main__":
    main()