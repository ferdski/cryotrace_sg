import React, { useEffect, useState } from 'react';
import '../components/ContainersList.css';  // use same CSS for pickup and dropoff
const baseUrl = process.env.REACT_APP_API_BASE_URL;

function PreparationRecords() {
const [shippers, setShippers] = useState([]);
const [selectedShipperId, setSelectedShipperId] = useState("");
const [preps, setPreps] = useState([]);


  const baseUrl = process.env.REACT_APP_API_BASE_URL;
  const fullUrl_preps = `${baseUrl}/api/preparations`;
  //const fullUrl_shippers = `${baseUrl}/api/shippers`;
  
useEffect(() => {
  fetch(`${baseUrl}/api/preparations`)
    .then(res => res.json())
    .then(data => setShippers(data))
    .catch(err => console.error(err));
}, []);

  // When user selects one preparation
useEffect(() => {
  if (!selectedShipperId) {
    setPreps([]);
    return;
  }

  fetch(`${baseUrl}/api/preparations?shipperId=${selectedShipperId}`)
    .then(res => res.json())
    .then(data => setPreps(data))
    .catch(err => console.error(err));
}, [selectedShipperId]);

  return (
    <div className="containers-list">
      <h2>Preparations</h2>

      <label>
        Select Shipper:
        <select
        value={selectedShipperId}
        onChange={(e) => setSelectedShipperId(e.target.value)}>
        <option value="">Choose a Shipper</option>
        {shippers.map(s => (
          <option key={s.shipper_id} value={s.shipper_id}>
            {s.shipper_id}
          </option>
      ))}
      </select>
      </label>

      {preps.length > 0 && (
        <div className="containers-list">
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
                <th>Notes (Internal)</th>
                <th>Notes (Public)</th>
                <th>Created At</th>
                <th>Updated At</th>
                </tr>
            </thead>
            <tbody>
                
            {preps.map(selectedPrep => (
            <tr key={selectedPrep.id}>
                <td>{selectedPrep.id}</td>
                <td>{selectedPrep.shipper_id}</td>
                <td>{selectedPrep.created_by}</td>
                <td>{selectedPrep.status}</td>
                <td>{selectedPrep.ner}</td>
                <td>{selectedPrep.started_at}</td>
                <td>{selectedPrep.finalized_at}</td>

                <td> {selectedPrep.ambient_temp_c}</td>

                <td> {selectedPrep.customer_ref}</td>
                <td> {selectedPrep.destination}</td>

                <td> {selectedPrep.notes_internal}</td>
                <td> {selectedPrep.notes_public}</td>
                <td> {selectedPrep.created_at}</td>
                <td> {selectedPrep.updated_at}</td>
          </tr>
          
            ))
            }
          </tbody>
        </table>
        </div>
      )}
    </div>
   );
}

export default PreparationRecords;
