import pandas as pd

def inspect_task_tool(csv_path, sttm_path):
    silver_pq=pd.read_parquet(csv_path)
    sttm_df_gold=pd.read_csv(sttm_path)
    return {"Shape":silver_pq.shape,"Columns": silver_pq.columns.to_list(), "Sample":silver_pq.head(5).to_dict(orient="records"),"Transformations":sttm_df_gold['transformation_logic'].to_list()}

def _is_identifier_like(col_name):
    name = col_name.lower()
    return name.endswith('_id') or name.startswith('pk_') or name.endswith('_key')

def gold_ingestion_tool(silver_pq_path, sttm_path, object_name):
    try:
        df=pd.read_parquet(silver_pq_path)
        sttm_df=pd.read_csv(sttm_path)
        sttm_df=sttm_df[sttm_df['transformation_logic'].notna()]
        sttm_df=sttm_df[sttm_df['source_col'].isin(df.columns)]

        output_written=False
        for tag, group in sttm_df.groupby(sttm_df['transformation_logic'].str.lower()):
            if not tag.startswith('group_by'):
                continue
            cols = group['source_col'].tolist()
            key_cols = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c]) or _is_identifier_like(c)]
            if not key_cols:
                key_cols = [cols[0]]
            value_cols = [c for c in cols if c not in key_cols and pd.api.types.is_numeric_dtype(df[c])]

            if value_cols:
                grouped_df = df.groupby(key_cols)[value_cols].sum().reset_index()
            else:
                grouped_df = df.groupby(key_cols).size().reset_index(name='count')

            output_suffix=tag.replace('group_by_', '')
            grouped_df.to_parquet(f"data/gold/{object_name}_by_{output_suffix}.parquet", index=False)
            output_written=True

        if not output_written:
            return False
        return "data/gold"
    except Exception as e:
        print(f"Error in gold_ingestion_tool: {e}")
        return False
    
def main():
    results=inspect_task_tool("data/silver/sales_silver.parquet","data/gold/sttm_gold_b2aea847-40ed-4851-be1b-974245e09730.csv")
    print(results)
    gold_ingestion_tool("data/silver/sales_silver.parquet","data/gold/sttm_gold_b2aea847-40ed-4851-be1b-974245e09730.csv")

if __name__=="__main__":
    main()