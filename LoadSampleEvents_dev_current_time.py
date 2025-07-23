import pandas as pd
import requests
import os


def load_demo_events(csv_path: str, api_base_url: str):
    # Load combined CSV file
    csv_path = "/home/ubuntu/sg_shippers_prototype/cryotrace_sg/Sample_Pickup___Dropoff_Data_23jul25.csv"

    if not csv_path:
        print(f"❌ File not found: {csv_path}")
        return
    df = pd.read_csv(csv_path)

    # POST each pickup and dropoff event from each row
    for _, row in df.iterrows():
        # --- Pickup event ---
        '''pickup_files = {
            'photo': (row['photo'], open(row['photo'], 'rb')) if pd.notna(row['photo']) else None
        }'''
        photo = row['photo']
        pickup_data = {
            'manifest_id': row['manifest_id_x'],
            'measured_weight_kg': row['measured_weight_kg'],
            'weight_type': row['weight_type'],
            'driver_user_id': row['driver_user_id'],
            'notes': row['notes'],
            'dev_current_time': row['dev_current_time_x']
        }
        print(f"Posting pickup for manifest {row['manifest_id_x']}")
        pickup_response = requests.post(
            f"{api_base_url}/api/pickup-events",
            data=pickup_data,
            files=pickup_files if pickup_files['photo'] else None
        )
        print(f"Pickup response: {pickup_response.status_code} - {pickup_response.text}")

        # --- Dropoff event ---
        dropoff_files = {
            'image_path': (row['image_path'], open(row['image_path'], 'rb')) if pd.notna(row['image_path']) else None
        }
        dropoff_data = {
            'manifest_id': row['manifest_id_y'],
            'received_location_id': row['received_location_id'],
            'received_contact_name': row['received_contact_name'],
            'received_weight_kg': row['received_weight_kg'],
            'condition_notes': row['condition_notes'],
            'received_by_user_id': row['received_by_user_id'],
            'dev_current_time': row['dev_current_time_y']
        }
        print(f"Posting dropoff for manifest {row['manifest_id_y']}")
        dropoff_response = requests.post(
            f"{api_base_url}/api/dropoff-events",
            data=dropoff_data,
            files=dropoff_files if dropoff_files['image_path'] else None
        )
        print(f"Dropoff response: {dropoff_response.status_code} - {dropoff_response.text}")


if __name__ == "__main__":
    load_demo_events('./cryotrace_sg/', 'localhost:8000')
