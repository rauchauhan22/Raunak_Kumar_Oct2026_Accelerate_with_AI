import pandas as pd

data={
    "transaction_id": ["a001","a002","a003","a004","a005",None,"b002","b003","b004","b005"],
    "date": ["2024-06-05","2024-06-05","2024-06-05","2024/04/17","2024-08-24","2024-09-07","2025-06-25","2026-06-05","2024-06-05","2024-06-05"],
    "customer_id": ["c001",None,"c003","c004","c005","c001","c002",None,"c004","c005"],
    "product_id": ["p001","p002","p003","p004","p005","p001","p002","p003",None,"p005"],
    "quantity": [2,1,3,2,1,2,1,3,2,1],
    "unit_price": [50.0,30.0,20.0,40.0,"$10.0",50.0,30.0,20.0,40.0,10.0],
    "total_amount": [100.0,30.0,60.0,80.0,10.0,100.0,"$30.0","$60.0","$80.0","$10.0"],
    "store_region": ["North","South",None,"West","North","South",None,"West","North","South"]
}

df=pd.DataFrame(data)
df.to_csv("data/raw/sales.csv", index=False)