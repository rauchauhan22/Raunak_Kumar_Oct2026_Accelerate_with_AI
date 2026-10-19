import pandas as pd
import json
from datetime import datetime


def inspect_files_tool(path):
    data_df=pd.read_csv(path)
    shape=data_df.shape
    rows_sample=data_df.head(3).to_dict(orient="records")
    cols=data_df.columns.to_list()
    return {"shape":shape,"data":rows_sample,"columns":cols}

def profiler_tool(path, object_name):
    data_df=pd.read_csv(path)
    total_null=data_df.isnull().sum().to_dict()
    unique=data_df.nunique().to_dict()
    sample_data=data_df.dropna().head(5).to_dict(orient="records")
    desc=data_df.describe().to_dict()

    today = datetime.now().strftime("%Y%m%d")
    result = {"total_null":total_null,"unique":unique,"sample_data":sample_data,"desc":desc}
    with open(f"data/raw/profile_{object_name}_{today}.json","w") as f:
        json.dump(result,f)
    return {"res": result,"path":f"data/raw/profile_{object_name}_{today}.json"}


def main():
    result = inspect_files_tool("data/raw/sales.csv")
    # print(result)
    result = profiler_tool("data/raw/sales.csv", "sales")
    print(result)

if __name__=="__main__":
    main()

