// src/components/RecordsByLocation.js
import React, { useEffect, useState } from 'react';
import RecordsTableLocation from './RenderRecordsTableLocation';

function RecordsByLocaton() {
  const [containers, setContainers] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [records, setRecords] = useState([]);

  const baseUrl = process.env.REACT_APP_API_BASE_URL;
  const fullUrl = `${baseUrl}/api/records`;
  const fullUrlContainers = `${baseUrl}/api/containers`;

  useEffect(() => {
    fetch(`${fullUrlContainers}`)
      .then(res => res.json())
      .then(data => setContainers(data))
      .catch(err => console.error('Error fetching containers:', err));
  }, [fullUrlContainers]);

  useEffect(() => {
    if (selectedId) {
      fetch(`${fullUrl}?filter=location&shipperId=${selectedId}`)
        .then(res => res.json())
        .then(data => setRecords(data))
        .catch(err => console.error('Error fetching records:', err));
    }
  }, [selectedId, fullUrl]);

  /*useEffect(() => {
    fetch('http://localhost:3001/api/containers')
      .then(res => res.json())
      .then(data => setContainers(data))
      .catch(err => console.error('Error fetching containers:', err));
  }, []);

  useEffect(() => {
    if (selectedId) {
      fetch(`http://localhost:3001/api/records?filter=location&containerId=${selectedId}`)
        .then(res => res.json())
        .then(data => setRecords(data))
        .catch(err => console.error('Error fetching records:', err));
    }
  }, [selectedId]);*/

  return (
    <div className="containers-list">
      <label htmlFor="container-select"><strong>Shipper Id:    </strong></label>
      <select
        id="container-select"
        value={selectedId}
        onChange={e => setSelectedId(e.target.value)}
      >
        <option value="">-- Select --</option>
        {containers.map(c => (
          <option key={c.shipper_id} value={c.shipper_id}>
            {c.shipper_id}
          </option>
        ))}
      </select>

      {records.length > 0 && <RecordsTableLocation records={records} />}
    </div>
  );
}

export default RecordsByLocaton;
