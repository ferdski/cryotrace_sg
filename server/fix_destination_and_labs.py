import mysql.connector

# Mapping of destination city/state → correct lab name
city_lab_map = {
    ("Augusta", "GA"): "Augusta Cryo Lab",
    ("Raleigh", "NC"): "Raleigh Genetics Lab",
    ("Milledgeville", "GA"): "Milledgeville Biotech",
    ("Gainesville", "FL"): "Gainesville Analytical Lab",
    ("Ashburn", "VA"): "VA Cryo Research",
    ("Richmond", "VA"): "Richmond Diagnostics",
    ("Charlotte", "NC"): "Charlotte Research Partners"
}

# Connect to database
conn = mysql.connector.connect(
    host="localhost",
    user="myappuser",
    password="mypassword",
    database="sg_shippers"
)
cursor = conn.cursor()

# Select movements with destination info
cursor.execute("""
    SELECT id, destination_city, destination_state, destination_company_name
    FROM movements
    WHERE destination_city IS NOT NULL AND destination_company_name IS NOT NULL
""")
rows = cursor.fetchall()
for r in rows: print(r)

updated_count = 0

for row in rows:
    movement_id, city, state, current_lab = row
    expected_lab = city_lab_map.get((city, state))

    if expected_lab and current_lab.strip().lower() != expected_lab.lower():
        cursor.execute("""
            UPDATE movements
            SET destination_company_name = %s
            WHERE id = %s
        """, (expected_lab, movement_id))
        updated_count += 1
        print(f"✔️ Updated movement {movement_id}: {current_lab} → {expected_lab}")

# Commit and close
conn.commit()
cursor.close()
conn.close()

print(f"\n✅ {updated_count} mismatched lab names corrected.")

