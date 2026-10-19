import json,io
from core.connection_req import make_connection 
import pandas as pd

def inspect_context_tool(file_path):
    with open(file_path) as f:
        profile_data=json.load(f)
    return profile_data

def generate_bronze_sttm_tool(result, run_id):
    try:
        client=make_connection()
        response=client.responses.create(input=f"""You are a data engineer. Given this data profile: {result}. Generate a source-to-target mapping for the Bronze layer. Return ONLY a CSV with exactly 3 columns: source_col, target_col, transformation_logic. Also, Value of transformation logic should follow the below mapping 
        parse_date: Standardize date to YYYY-MM-DD 
        remove_currency_cast_float: Strip $ and cast to float
        trim: Strip whitespace               
        cast_integer: Cast to integer               
        No explanation, no markdown, just the CSV rows.""", model="openai/gpt-oss-20b")
        response=response.output[1].content[0].text
        
        response=io.StringIO(response)
        df=pd.read_csv(response)
        df.to_csv(f"data/bronze/sttm_bronze_{run_id}.csv", index=False)
        return f"data/bronze/sttm_bronze_{run_id}.csv"
    except Exception as e:
        print(f"Error in generate_bronze_sttm_tool: {e}")
        return False


def generate_silver_sttm_tool(parquet_path, run_id):
    try:
        client=make_connection()
        parquet_file=pd.read_parquet(parquet_path)
        silver_prompt=f"""You are a data engineer. Given bronze data: {parquet_file.to_dict(orient="records")}. Apply silver layer transformations, STTM rules  "Use ONLY these transformation_logic values:
         - 'fill_unknown' — for column store_region where nulls should be filled with 'UNKNOWN'
         - 'drop_null' — for rows where this column('transaction_id','customer_id','product_id','date') is null and must exist
         - 'fill_mean' — for ('quantity','unit_price','total_amount') columns where nulls should be filled with mean
         - 'drop_duplicates' — for deduplication on column 'transaction_id'
            Return ONLY a CSV with exactly 3 columns: source_col, target_col, transformation_logic. No explanation, no markdown, just the CSV rows."""
        response=client.responses.create(input=f'{silver_prompt}', model="openai/gpt-oss-20b")
        response=response.output[1].content[0].text
        response=io.StringIO(response)
        df=pd.read_csv(response)
        df.to_csv(f"data/silver/sttm_silver_{run_id}.csv", index=False)
        return f"data/silver/sttm_silver_{run_id}.csv"
    except Exception as e:
        print(f"Error in generate_silver_sttm_tool: {e}")
        return False

def generate_gold_sttm_tool(parquet_path, run_id):
    try:
        client=make_connection()
        silver_parquet_file=pd.read_parquet(parquet_path)
        response=client.responses.create(input=f"""You are a data engineer. Given this data profile: {silver_parquet_file}. Generate a source-to-target mapping for the Gold layer. Return ONLY a CSV with exactly 3 columns: source_col, target_col, transformation_logic. Also, for the value of transformation logic, follow the below mapping logic: 
        group_by_region: Group by store_region, sum total_amount 
        group_by_product: Group by product_id, sum quantity       
        group_by_date: Group by date, sum total_amount                                 
        No explanation, no markdown, just the CSV rows.""", model="openai/gpt-oss-20b")
        response=response.output[1].content[0].text
        response=io.StringIO(response)
        df=pd.read_csv(response)
        df.to_csv(f"data/gold/sttm_gold_{run_id}.csv", index=False)
        return f"data/gold/sttm_gold_{run_id}.csv"
    except Exception as e:
        print(f"Error in generate_gold_sttm_tool: {e}")
        return False
    
def main():
    # profile=inspect_context_tool("data/raw/profile_combined_20261017.json")
    # generate_bronze_sttm_tool(result=profile, run_id=run_id)
    # generate_silver_sttm_tool(parquet_path="data/bronze/sales_bronze.parquet", run_id=run_id)
    generate_gold_sttm_tool(parquet_path="data/silver/sales_silver.parquet", run_id=run_id)

if __name__=="__main__":
    main()