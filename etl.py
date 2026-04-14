import os
import json
import sqlite3
import pandas as pd

# Define paths
DATA_DIR = "c:/Users/rasta/Desktop/pulse/data"
DB_PATH = "c:/Users/rasta/Desktop/pulse/pulse.db"

# Establish DB connection
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def get_state_folders(base_path):
    state_path = os.path.join(base_path, "state")
    if not os.path.exists(state_path):
        return []
    return [d for d in os.listdir(state_path) if os.path.isdir(os.path.join(state_path, d))]

def run_etl():
    print("Starting ETL...")

    # 1. Aggregated Transactions
    print("Processing Aggregated Transactions...")
    path1 = os.path.join(DATA_DIR, "aggregated", "transaction", "country", "india", "state")
    data_list = []
    if os.path.exists(path1):
        for state in os.listdir(path1):
            state_dir = os.path.join(path1, state)
            for year in os.listdir(state_dir):
                year_dir = os.path.join(state_dir, year)
                for q_file in os.listdir(year_dir):
                    quarter = q_file.split(".")[0]
                    with open(os.path.join(year_dir, q_file), 'r') as f:
                        data = json.load(f)
                        if data.get("data") and data["data"].get("transactionData"):
                            for obj in data["data"]["transactionData"]:
                                name = obj["name"]
                                count = obj["paymentInstruments"][0]["count"]
                                amount = obj["paymentInstruments"][0]["amount"]
                                data_list.append({
                                    "State": state, "Year": int(year), "Quarter": int(quarter),
                                    "Transaction_type": name, "Transaction_count": count, "Transaction_amount": amount
                                })
    if data_list:
        df1 = pd.DataFrame(data_list)
        df1.to_sql('Aggregated_transaction', conn, if_exists='replace', index=False)

    # 2. Aggregated Users
    print("Processing Aggregated Users...")
    path2 = os.path.join(DATA_DIR, "aggregated", "user", "country", "india", "state")
    data_list = []
    if os.path.exists(path2):
        for state in os.listdir(path2):
            state_dir = os.path.join(path2, state)
            for year in os.listdir(state_dir):
                year_dir = os.path.join(state_dir, year)
                for q_file in os.listdir(year_dir):
                    quarter = q_file.split(".")[0]
                    with open(os.path.join(year_dir, q_file), 'r') as f:
                        data = json.load(f)
                        if data.get("data") and data["data"] is not None and data["data"].get("usersByDevice"):
                            for obj in data["data"]["usersByDevice"]:
                                data_list.append({
                                    "State": state, "Year": int(year), "Quarter": int(quarter),
                                    "Brand": obj["brand"], "Count": obj["count"], "Percentage": obj["percentage"]
                                })
    if data_list:
        df2 = pd.DataFrame(data_list)
        df2.to_sql('Aggregated_user', conn, if_exists='replace', index=False)

    # 3. Aggregated Insurance
    print("Processing Aggregated Insurance...")
    path3 = os.path.join(DATA_DIR, "aggregated", "insurance", "country", "india", "state")
    data_list = []
    if os.path.exists(path3):
        for state in os.listdir(path3):
            state_dir = os.path.join(path3, state)
            for year in os.listdir(state_dir):
                year_dir = os.path.join(state_dir, year)
                for q_file in os.listdir(year_dir):
                    quarter = q_file.split(".")[0]
                    with open(os.path.join(year_dir, q_file), 'r') as f:
                        data = json.load(f)
                        if data.get("data") and data["data"].get("transactionData"):
                            for obj in data["data"]["transactionData"]:
                                name = obj["name"]
                                count = obj["paymentInstruments"][0]["count"]
                                amount = obj["paymentInstruments"][0]["amount"]
                                data_list.append({
                                    "State": state, "Year": int(year), "Quarter": int(quarter),
                                    "Insurance_type": name, "Insurance_count": count, "Insurance_amount": amount
                                })
    if data_list:
        df3 = pd.DataFrame(data_list)
        df3.to_sql('Aggregated_insurance', conn, if_exists='replace', index=False)

    # 4. Map Transactions
    print("Processing Map Transactions...")
    path4 = os.path.join(DATA_DIR, "map", "transaction", "hover", "country", "india", "state")
    data_list = []
    if os.path.exists(path4):
        for state in os.listdir(path4):
            state_dir = os.path.join(path4, state)
            for year in os.listdir(state_dir):
                year_dir = os.path.join(state_dir, year)
                for q_file in os.listdir(year_dir):
                    quarter = q_file.split(".")[0]
                    with open(os.path.join(year_dir, q_file), 'r') as f:
                        data = json.load(f)
                        if data.get("data") and data["data"].get("hoverDataList"):
                            for obj in data["data"]["hoverDataList"]:
                                dist = obj["name"]
                                count = obj["metric"][0]["count"]
                                amount = obj["metric"][0]["amount"]
                                data_list.append({
                                    "State": state, "Year": int(year), "Quarter": int(quarter),
                                    "District": dist, "Transaction_count": count, "Transaction_amount": amount
                                })
    if data_list:
        df4 = pd.DataFrame(data_list)
        df4.to_sql('Map_transaction', conn, if_exists='replace', index=False)

    # 5. Map Users
    print("Processing Map Users...")
    path5 = os.path.join(DATA_DIR, "map", "user", "hover", "country", "india", "state")
    data_list = []
    if os.path.exists(path5):
        for state in os.listdir(path5):
            state_dir = os.path.join(path5, state)
            for year in os.listdir(state_dir):
                year_dir = os.path.join(state_dir, year)
                for q_file in os.listdir(year_dir):
                    quarter = q_file.split(".")[0]
                    with open(os.path.join(year_dir, q_file), 'r') as f:
                        data = json.load(f)
                        if data.get("data") and data["data"] is not None and data["data"].get("hoverData"):
                            for dist, obj in data["data"]["hoverData"].items():
                                data_list.append({
                                    "State": state, "Year": int(year), "Quarter": int(quarter),
                                    "District": dist, "Registered_users": obj["registeredUsers"], "App_opens": obj["appOpens"]
                                })
    if data_list:
        df5 = pd.DataFrame(data_list)
        df5.to_sql('Map_user', conn, if_exists='replace', index=False)

    # 6. Map Insurance
    print("Processing Map Insurance...")
    path6 = os.path.join(DATA_DIR, "map", "insurance", "hover", "country", "india", "state")
    data_list = []
    if os.path.exists(path6):
        for state in os.listdir(path6):
            state_dir = os.path.join(path6, state)
            for year in os.listdir(state_dir):
                year_dir = os.path.join(state_dir, year)
                for q_file in os.listdir(year_dir):
                    quarter = q_file.split(".")[0]
                    with open(os.path.join(year_dir, q_file), 'r') as f:
                        data = json.load(f)
                        if data.get("data") and data["data"].get("hoverDataList"):
                            for obj in data["data"]["hoverDataList"]:
                                dist = obj["name"]
                                count = obj["metric"][0]["count"]
                                amount = obj["metric"][0]["amount"]
                                data_list.append({
                                    "State": state, "Year": int(year), "Quarter": int(quarter),
                                    "District": dist, "Insurance_count": count, "Insurance_amount": amount
                                })
    if data_list:
        df6 = pd.DataFrame(data_list)
        df6.to_sql('Map_insurance', conn, if_exists='replace', index=False)

    # 7. Top Transactions
    print("Processing Top Transactions...")
    path7 = os.path.join(DATA_DIR, "top", "transaction", "country", "india", "state")
    data_list = []
    if os.path.exists(path7):
        for state in os.listdir(path7):
            state_dir = os.path.join(path7, state)
            for year in os.listdir(state_dir):
                year_dir = os.path.join(state_dir, year)
                for q_file in os.listdir(year_dir):
                    quarter = q_file.split(".")[0]
                    with open(os.path.join(year_dir, q_file), 'r') as f:
                        data = json.load(f)
                        if data.get("data") and data["data"].get("districts"):
                            for obj in data["data"]["districts"]:
                                dist = obj["entityName"]
                                count = obj["metric"]["count"]
                                amount = obj["metric"]["amount"]
                                data_list.append({
                                    "State": state, "Year": int(year), "Quarter": int(quarter),
                                    "EntityType": "District", "EntityName": dist, "Count": count, "Amount": amount
                                })
                        if data.get("data") and data["data"].get("pincodes"):
                            for obj in data["data"]["pincodes"]:
                                pin = obj["entityName"]
                                count = obj["metric"]["count"]
                                amount = obj["metric"]["amount"]
                                data_list.append({
                                    "State": state, "Year": int(year), "Quarter": int(quarter),
                                    "EntityType": "Pincode", "EntityName": pin, "Count": count, "Amount": amount
                                })
    if data_list:
        df7 = pd.DataFrame(data_list)
        df7.to_sql('Top_transaction', conn, if_exists='replace', index=False)

    # 8. Top Users
    print("Processing Top Users...")
    path8 = os.path.join(DATA_DIR, "top", "user", "country", "india", "state")
    data_list = []
    if os.path.exists(path8):
        for state in os.listdir(path8):
            state_dir = os.path.join(path8, state)
            for year in os.listdir(state_dir):
                year_dir = os.path.join(state_dir, year)
                for q_file in os.listdir(year_dir):
                    quarter = q_file.split(".")[0]
                    with open(os.path.join(year_dir, q_file), 'r') as f:
                        data = json.load(f)
                        if data.get("data") and data["data"] is not None:
                            if data["data"].get("districts"):
                                for obj in data["data"]["districts"]:
                                    dist = obj["name"]
                                    users = obj["registeredUsers"]
                                    data_list.append({
                                        "State": state, "Year": int(year), "Quarter": int(quarter),
                                        "EntityType": "District", "EntityName": dist, "RegisteredUsers": users
                                    })
                            if data["data"].get("pincodes"):
                                for obj in data["data"]["pincodes"]:
                                    pin = obj["name"]
                                    users = obj["registeredUsers"]
                                    data_list.append({
                                        "State": state, "Year": int(year), "Quarter": int(quarter),
                                        "EntityType": "Pincode", "EntityName": pin, "RegisteredUsers": users
                                    })
    if data_list:
        df8 = pd.DataFrame(data_list)
        df8.to_sql('Top_user', conn, if_exists='replace', index=False)
        
    # 9. Top Insurance
    print("Processing Top Insurance...")
    path9 = os.path.join(DATA_DIR, "top", "insurance", "country", "india", "state")
    data_list = []
    if os.path.exists(path9):
        for state in os.listdir(path9):
            state_dir = os.path.join(path9, state)
            for year in os.listdir(state_dir):
                year_dir = os.path.join(state_dir, year)
                for q_file in os.listdir(year_dir):
                    quarter = q_file.split(".")[0]
                    with open(os.path.join(year_dir, q_file), 'r') as f:
                        data = json.load(f)
                        if data.get("data") and data["data"].get("districts"):
                            for obj in data["data"]["districts"]:
                                dist = obj["entityName"]
                                count = obj["metric"]["count"]
                                amount = obj["metric"]["amount"]
                                data_list.append({
                                    "State": state, "Year": int(year), "Quarter": int(quarter),
                                    "EntityType": "District", "EntityName": dist, "Count": count, "Amount": amount
                                })
                        if data.get("data") and data["data"].get("pincodes"):
                            for obj in data["data"]["pincodes"]:
                                pin = obj["entityName"]
                                count = obj["metric"]["count"]
                                amount = obj["metric"]["amount"]
                                data_list.append({
                                    "State": state, "Year": int(year), "Quarter": int(quarter),
                                    "EntityType": "Pincode", "EntityName": pin, "Count": count, "Amount": amount
                                })
    if data_list:
        df9 = pd.DataFrame(data_list)
        df9.to_sql('Top_insurance', conn, if_exists='replace', index=False)

    print("ETL Completed Successfully!")

if __name__ == "__main__":
    run_etl()
    conn.close()
