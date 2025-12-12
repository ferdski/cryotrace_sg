import React, { useEffect, useState } from 'react';
import './PickupEventsPage.css';  // use same CSS for pickup and dropoff
const baseUrl = process.env.REACT_APP_API_BASE_URL;

function PreparationRecords() {
  const [preparations, setPreparations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const baseUrl = process.env.REACT_APP_API_BASE_URL;
  const fullUrl = `${baseUrl}/api/preparations`;

  useEffect(() => {
    fetch(fullUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setPreparations(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching preparations:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [fullUrl]);

  if (loading) return <p>Loading preparations...</p>;
  if (error) return <p>Error: {error}</p>;

  return (
    <div>
      <h2>Preparations</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Shipper ID</th>
            <th>Created By</th>
            <th>Status</th>
            <th>NER</th>
            <th>Started At</th>
            <th>Finalized At</th>
            <th>Ambient Temp (°C)</th>
            <th>Customer Ref</th>
            <th>Destination</th>
            <th>Notes Internal</th>
            <th>Notes Public</th>
            <th>Created At</th>
            <th>Updated At</th>
          </tr>
        </thead>

        <tbody>
          {preparations.map((p) => (
            <tr key={p.id}>
              <td>{p.id}</td>
              <td>{p.shipper_id}</td>
              <td>{p.created_by}</td>
              <td>{p.status}</td>
              <td>{p.ner}</td>
              <td>{p.started_at}</td>
              <td>{p.finalized_at}</td>
              <td>{p.ambient_temp_c}</td>
              <td>{p.customer_ref}</td>
              <td>{p.destination}</td>
              <td>{p.notes_internal}</td>
              <td>{p.notes_public}</td>
              <td>{p.created_at}</td>
              <td>{p.updated_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default PreparationRecords;
