import pandas as pd

def inspect_task_tool(csv_path, sttm_path):
    df=pd.DataFrame(pd.read_csv(csv_path))
    sttm_df=pd.DataFrame(pd.read_csv(sttm_path))
    return {"Shape":df.shape,"Columns": df.columns.to_list(), "Sample":df.head(5).to_dict(orient="records"),"Transformations":sttm_df['transformation_logic'].to_list()}

def bronze_ingestion_tool(csv_path, sttm_path, object_name):
    try:
        df=pd.read_csv(csv_path)
        sttm_df=pd.read_csv(sttm_path)
        for _,val in sttm_df.iterrows():
            source_col=val['source_col']
            val=val['transformation_logic'].lower()
            if 'parse_date' in val:
                df[source_col]=pd.to_datetime(df[source_col], format='mixed').dt.strftime('%Y-%m-%d')
            elif 'remove_currency_cast_float' in val:
                df[source_col]=df[source_col].astype(str).str.replace('$','', regex=False).astype(float)
            elif 'trim' in val:
                if df[source_col].dtype == object:
                    df[source_col]=df[source_col].str.strip()
            elif 'cast_integer' in val:
                df[source_col]=df[source_col].astype(int)

        df.to_parquet(f"data/bronze/{object_name}_bronze.parquet", index=False)
        return f"data/bronze/{object_name}_bronze.parquet"
    except Exception as e:
        print(f"Error in bronze_ingestion_tool: {e}")
        return False
            

def main():
    results=inspect_task_tool("data/raw/sales.csv","data/bronze/sttm_data.csv")
    bronze_ingestion_tool("data/raw/sales.csv","data/bronze/sttm_data.csv","sales")

if __name__=="__main__":
    main()