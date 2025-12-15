import React, { useEffect, useState } from 'react';
import '../components/ContainersList.css';  // use same CSS for pickup and dropoff
const baseUrl = process.env.REACT_APP_API_BASE_URL;

function PreparationRecords() {
  const [preps, setPreps] = useState([]);
  const [selectedPrepId, setSelectedPrepId] = useState("");
  const [selectedPrep, setSelectedPrep] = useState(null);
  const [shippers, setShippers] = useState([]);
  const [selectedShipper, setSelectedShipper] = useState(null);

  const baseUrl = process.env.REACT_APP_API_BASE_URL;
  const fullUrl = `${baseUrl}/api/preparations`;

  useEffect(() => {
    fetch(fullUrl)
      .then((res) => res.json())
      .then((data) => setPreps(data))
      .catch((err) => console.error("Error fetching preparations:", err));
  }, []);

  // When user selects one preparation
  useEffect(() => {
    if (!selectedPrepId) {
      setSelectedPrep(null);
      return;
    }
    const found = preps.find((p) => p.id === selectedPrepId);
    setSelectedPrep(found || null);
  }, [selectedPrepId, preps]);

  return (
    <div className="containers-list">
      <h2>Preparations</h2>

      <label>
        Select Preparation:
        <select
          value={selectedPrepId}
          onChange={(e) => setSelectedPrepId(e.target.value)}
          required
        >
          <option value="">Choose a preparation</option>
          {preps.map((p) => (
            <option key={p.id} value={p.id}>
              {p.id}
            </option>
          ))}
        </select>
      </label>

      {selectedPrep && (
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
