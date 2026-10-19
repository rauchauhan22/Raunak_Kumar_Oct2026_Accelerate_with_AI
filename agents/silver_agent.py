import pandas as pd

def inspect_task_tool(csv_path, sttm_path):
    bronze_pq=pd.read_parquet(csv_path)
    sttm_df_silver=pd.read_csv(sttm_path)
    return {"Shape":bronze_pq.shape,"Columns": bronze_pq.columns.to_list(), "Sample":bronze_pq.head(5).to_dict(orient="records"),"Transformations":sttm_df_silver['transformation_logic'].to_list()}

def silver_ingestion_tool(bronze_pq_path, sttm_path, object_name):
    try:
        df=pd.read_parquet(bronze_pq_path)
        sttm_df=pd.read_csv(sttm_path)
        for _,row in sttm_df.iterrows():
            if pd.isna(row['transformation_logic']):
                continue
            source_col=row['source_col']
            if source_col not in df.columns:
                continue
            logic=row['transformation_logic'].lower()
            if 'drop_null' in logic:
                df = df.dropna(subset=[source_col])
            elif 'fill_unknown' in logic:
                df[source_col]=df[source_col].fillna('Unknown')
            elif 'fill_mean' in logic and pd.api.types.is_numeric_dtype(df[source_col]):
                df[source_col]=df[source_col].fillna(df[source_col].mean())
            elif 'drop_duplicates' in logic:
                df = df.drop_duplicates()

        df.insert(0,f'pk_{object_name}_silver_id',range(1,len(df)+1))
        df.to_parquet(f"data/silver/{object_name}_silver.parquet", index=False)
        return f"data/silver/{object_name}_silver.parquet"
    except Exception as e:
        print(f"Error in silver_ingestion_tool: {e}")
        return False

def main():
    results=inspect_task_tool("data/bronze/sales_bronze.parquet","data/silver/sttm_silver_884abfc3-73af-45ec-a72e-7233fee1316c.csv")
    print(results)
    silver_ingestion_tool("data/bronze/sales_bronze.parquet","data/silver/sttm_silver_884abfc3-73af-45ec-a72e-7233fee1316c.csv","sales")

if __name__=="__main__":
    main()