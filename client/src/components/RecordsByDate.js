// src/components/RecordsByDate.js
import React, { useEffect, useState } from 'react';
import RecordsTableDate from './RenderRecordsTableDate';

function RecordsByDate() {
  const [containers, setContainers] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [records, setRecords] = useState([]);

  console.log(`ip = `, process.env.REACT_APP_API_BASE_URL);

  console.log(`baseUrl: ${process.env.REACT_APP_API_BASE_URL}`);

  const baseUrl = process.env.REACT_APP_API_BASE_URL;
  const fullUrl = `${baseUrl}/api/records`;
  const fullUrlContainers = `${baseUrl}/api/containers`;

  console.log("Fetching from:", fullUrl, fullUrlContainers); // ✅ Confirm this prints

  useEffect(() => {
    fetch(`${fullUrlContainers}`)
      .then(res => res.json())
      .then(data => setContainers(data))
      .catch(err => console.error('Error fetching containers:', err));
  }, [fullUrlContainers]);

  useEffect(() => {
    if (selectedId) {
      fetch(`${fullUrl}?filter=date&shipperId=${selectedId}`)
        .then((res) => res.json())
        .then((data) => setRecords(data))
        .catch((err) => {
          console.error('Error fetching records:', err);
        });
    }
  }, [selectedId, fullUrl]);

  return (
    <div className="containers-list">
      <label htmlFor="container-select"><strong>Container:    </strong></label>
      <select
        id="container-select"
        value={selectedId}
        onChange={e => setSelectedId(e.target.value)}
      >
        <option value="">-- Select a container --</option>
        {containers.map(c => (
          <option key={c.shipper_id} value={c.shipper_id}>
            {c.shipper_id}
          </option>
        ))}
      </select>

      {records.length > 0 && <RecordsTableDate records={records} />}
    </div>
  );
}

export default RecordsByDate;

