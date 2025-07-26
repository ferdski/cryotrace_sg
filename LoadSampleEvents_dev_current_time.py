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
    csv_path = "/home/ubuntu/sg_shippers_prototype/cryotrace_sg/Corrected_Pickup_Dropoff_Events_All_Manifests_corrected_v2.csv"

    if not csv_path:
        print(f"❌ File not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    for index, row in df.iterrows():
        if index == 0:
            continue
        # --- Pickup event ---
        '''pickup_files = {
            'photo': (row['photo'], open(row['photo'], 'rb')) if pd.notna(row['photo']) else None
        }'''
        try:

            pickup_data = {
                'manifest_id': row['manifest_id'],
                'measured_weight_kg': row['pickup_weight'],
                "weight_measured_at" : row['pickup_time'],
                "actual_departure_at" : row['pickup_time'],
                'driver_user_id': row['pickup_user_id'],
                'image_path' : 'image_path',
                'notes': 'pickup_note',
                'created_at' : row['manifest_created_at'],
                'dev_current_time': row['pickup_time']

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
                sm.destination_contact_name,
                sm.created_by_user_id,
                CONCAT(origin.city, ', ', origin.state, ', ', origin.company_name, ' ', origin.company_address) AS origin,
                CONCAT(dest.city, ', ', dest.state, ', ', dest.company_name, ' ', dest.company_address) AS destination
            FROM shipping_manifest sm
            LEFT JOIN locations origin ON sm.origin_location_id = origin.id
            LEFT JOIN locations dest ON sm.destination_location_id = dest.id
            WHERE sm.manifest_id = %s
            ORDER BY sm.manifest_id DESC
            """, (row['manifest_id'],))  # for pickup events

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
                datetime.strptime(pickup_data['weight_measured_at'], "%Y-%m-%d %H:%M:%S"),
                results_manifest[0]['origin_location_id'],
                pickup_data['driver_user_id'],
                pickup_data['measured_weight_kg'],
                pickup_data['notes'],
                datetime.strptime(pickup_data['dev_current_time'], "%Y-%m-%d %H:%M:%S"),  # created_at

            ))
            conn.commit()            
            # also write the container_weight_event for this entry
            print(f"Posting cwe from pickup manifest data: {row['manifest_id']}  , {pickup_data}")

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
                datetime.strptime(pickup_data['actual_departure_at'], "%Y-%m-%d %H:%M:%S"),  #actual_departure_at
                pickup_data['driver_user_id'],
                pickup_data['image_path'],
                pickup_data['notes'],
                datetime.strptime(pickup_data['created_at'], "%Y-%m-%d %H:%M:%S"),  # created_at
                datetime.strptime(pickup_data['dev_current_time'], "%Y-%m-%d %H:%M:%S"),  #dev_current_time
            ))
            conn.commit()
            print(f"Posting pickup for manifest {row['manifest_id']}  , {pickup_data}")

        except Exception as e:
            print("❌ Pickup Event failed:", e)


        try:
            dropoff_data = {
                'manifest_id': row['manifest_id'],
                'received_location_id':  row['dropoff_location_id'],
                'received_contact_name':  row['destination_contact_name'],
                'actual_receive_time':  row['dropoff_time'],
                'received_weight_kg':  row['dropoff_weight'],
                'condition_notes':  'dropoff note',
                'image_path':  'image_path',
                'received_by_user_id':  1,
                'created_at' : row['dropoff_time'],
                'dev_current_time': row['dropoff_time']
            }

            
            weight_type = "dropoff"

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
                ) VALUES (%s, %s, %s, %s, %s, %s, %s,  %s)
            """, (
                dropoff_data['manifest_id'],
                weight_type,
                datetime.strptime(dropoff_data['dev_current_time'], "%Y-%m-%d %H:%M:%S"),
                dropoff_data['received_location_id'],
                dropoff_data['received_by_user_id'],
                dropoff_data['received_weight_kg'],
                dropoff_data['condition_notes'],
                datetime.strptime(dropoff_data['dev_current_time'], "%Y-%m-%d %H:%M:%S")  # created_at
            ))
            conn.commit()            
            # also write the container_weight_event for this entry
            print(f"Posting cwe from pickup manifest data: {row['manifest_id']}  , {pickup_data}")

            cursor.execute("""
                INSERT INTO dropoff_event (
                    manifest_id,
                    received_location_id,
                    received_contact_name,
                    actual_receive_time,
                    received_weight_kg,
                    condition_notes,
                    image_path,
                    received_by_user_id,
                    created_at, 
                    dev_current_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                dropoff_data['manifest_id'],
                dropoff_data['received_location_id'],
                dropoff_data['received_contact_name'],  #weight_measured_at,
                datetime.strptime(dropoff_data['dev_current_time'], "%Y-%m-%d %H:%M:%S"),  #actual_departure_at
                dropoff_data['received_weight_kg'],
                dropoff_data['condition_notes'],
                dropoff_data['image_path'],
                dropoff_data['received_by_user_id'],
                datetime.strptime(dropoff_data['dev_current_time'], "%Y-%m-%d %H:%M:%S"),  # created_at
                datetime.strptime(dropoff_data['dev_current_time'], "%Y-%m-%d %H:%M:%S"), #dev_current_time
            ))
            conn.commit()
            cursor.close()

            print({f"status": "Dropoff event recorded."})


        except Exception as e:
            print("❌ Dropoff Event failed:", e)

            #return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    load_demo_events('./cryotrace_sg/', 'http://localhost:8000')
