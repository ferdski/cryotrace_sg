import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="server/.env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "sg_shipping")

# Load CSV
df = pd.read_csv("Shipping_Manifest_Sample_Data.csv")

# Basic validation function
def is_valid_row(row):
    required_fields = [
        "manifest_id", "shipper_id", "origin_location_id", "origin_contact_name",
        "destination_location_id", "destination_contact_name", "scheduled_ship_time",
        "expected_receive_time", "projected_weight_kg", "temperature_c", "created_by_user_id"
    ]
    for field in required_fields:
        if pd.isna(row[field]) or row[field] == "":
            return False
    return True

try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )
    cursor = conn.cursor()

    for _, row in df.iterrows():
        if not is_valid_row(row):
            print(f"⚠️ Skipping invalid row: {row.to_dict()}")
            continue

        # Skip if manifest_id already exists
        cursor.execute("SELECT manifest_id FROM shipping_manifest WHERE manifest_id = %s", (row["manifest_id"],))
        if cursor.fetchone():
            print(f"🔁 Skipping duplicate manifest_id: {row['manifest_id']}")
            continue

        insert_query = """
            INSERT INTO shipping_manifest (
                manifest_id, shipper_id, origin_location_id, origin_contact_name,
                destination_location_id, destination_contact_name, scheduled_ship_time,
                expected_receive_time, projected_weight_kg, temperature_c, notes,
                created_by_user_id, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        shipper_id = f"{row['shipper_id']:04}" #f"{row["shipper_id"]:04}"
        values = (
            row["manifest_id"],
            shipper_id,
            int(row["origin_location_id"]),
            row["origin_contact_name"],
            int(row["destination_location_id"]),
            row["destination_contact_name"],
            row["scheduled_ship_time"],
            row["expected_receive_time"],
            float(row["projected_weight_kg"]),
            float(row["temperature_c"]),
            row.get("notes", None),
            int(row["created_by_user_id"]),
            row["created_at"]
        )

        cursor.execute(insert_query, values)
        print(f"✅ Inserted manifest_id: {row['manifest_id']}")

    conn.commit()
    cursor.close()
    conn.close()
    print("🎉 All valid data inserted successfully.")

except Error as e:
    print(f"❌ Database error: {e}")
