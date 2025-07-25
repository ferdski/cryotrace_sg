import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './server')))

import pandas as pd
import requests
import os
from db import get_connection
from datetime import datetime


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
        try:
            photo = row['photo']
            pickup_data = {
                'manifest_id': row['manifest_id_x'],
                'measured_weight_kg': row['measured_weight_kg'],
                "weight_measured_at" : row['dev_current_time_x'],
                "actual_departure_at" : row['dev_current_time_x'],
                'driver_user_id': row['driver_user_id'],
                'image_path' : 'image_path',
                'notes': row['notes'],
                'created_at' : row['dev_current_time_x'],
                'dev_current_time': row['dev_current_time_x']

            }


            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # get required info from Manifest Id
            cursor.execute("""
            SELECT 
                sm.manifest_id,
                sm.shipper_id,
                sm.origin_location_id,
                sm.destination_location_id,
                sm.scheduled_ship_time,
                sm.expected_receive_time,
                sm.created_by_user_id,
                CONCAT(origin.city, ', ', origin.state, ', ', origin.company_name, ' ', origin.company_address) AS origin,
                CONCAT(dest.city, ', ', dest.state, ', ', dest.company_name, ' ', dest.company_address) AS destination
            FROM shipping_manifest sm
            LEFT JOIN locations origin ON sm.origin_location_id = origin.id
            LEFT JOIN locations dest ON sm.destination_location_id = dest.id
            WHERE sm.manifest_id = %s
            ORDER BY sm.manifest_id DESC
            """, (row['manifest_id_x'],))  # for pickup events

            results_manifest = cursor.fetchall()
            print(f"manifest query results: {results_manifest}")


            weight_type = "pickup"


            cursor.execute("""
                INSERT INTO container_weight_event (
                    manifest_id,
                    weight_type,
                    event_time,
                    location_id,
                    recorded_by_user_id,
                    weight_kg,
                    notes,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                pickup_data['manifest_id'],
                weight_type,
                datetime.strptime(pickup_data['weight_measured_at'], "%Y-%m-%dT%H:%M:%S"),
                results_manifest[0]['origin_location_id'],
                pickup_data['driver_user_id'],
                pickup_data['measured_weight_kg'],
                pickup_data['notes'],
                datetime.strptime(row['dev_current_time_x'], "%Y-%m-%dT%H:%M:%S"),  # created_at

            ))
            conn.commit()            
            # also write the container_weight_event for this entry
            print(f"Posting cwe from manifest data: {row['manifest_id_x']}  , {pickup_data}")



            cursor.execute("""
                INSERT INTO pickup_event (
                    manifest_id,
                    measured_weight_kg,
                    weight_measured_at,
                    actual_departure_at,
                    driver_user_id,
                    image_path,
                    notes,
                    created_at, 
                    dev_current_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                pickup_data['manifest_id'],
                pickup_data['measured_weight_kg'],
                pickup_data['weight_measured_at'],  #weight_measured_at,
                datetime.strptime(pickup_data['actual_departure_at'], "%Y-%m-%dT%H:%M:%S"),  #actual_departure_at
                pickup_data['driver_user_id'],
                pickup_data['image_path'],
                pickup_data['notes'],
                datetime.strptime(pickup_data['created_at'], "%Y-%m-%dT%H:%M:%S"),  # created_at
                datetime.strptime(pickup_data['dev_current_time'], "%Y-%m-%dT%H:%M:%S"),  #dev_current_time
            ))
            conn.commit()
            print(f"Posting pickup for manifest {row['manifest_id_x']}  , {pickup_data}")


            cursor.close()


            return {"status": "Pickup event recorded."}

        except Exception as e:
            print("❌ Pickup event failed:", e)
            return
            #return JSONResponse(status_code=500, content={"error": str(e)})


        #print(f"Pickup response: {pickup_response.status_code} - {pickup_response.text}")

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
    load_demo_events('./cryotrace_sg/', 'http://localhost:8000')
