import React, { useEffect, useState } from 'react';

function RecordsFilterPage({ filterType }) {
  const [containers, setContainers] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [records, setRecords] = useState([]);

  useEffect(() => {
    fetch('http://localhost:3001/api/containers')
      .then(res => res.json())
      .then(data => setContainers(data))
      .catch(err => console.error('Error fetching containers:', err));
  }, []);

  useEffect(() => {
    if (selectedId) {
        console.log(`filter: ${filterType}, ${selectedId}` );
        console.log(`http://localhost:3001/api/records?filter=${filterType}&containerId=${selectedId}`);
      fetch(`http://localhost:3001/api/records?filter=${filterType}&containerId=${selectedId}`)
        .then(res => res.json())
        .then(data => setRecords(data))
        .catch(err => console.error('Error fetching records:', err));
    }
  }, [selectedId, filterType]);

  return (
    <div>
      <label htmlFor="containerSelect">Container:</label>
      <select
        id="containerSelect"
        value={selectedId}
        onChange={(e) => setSelectedId(e.target.value)}
      >
        <option value="">-- Select a container --</option>
        {containers.map(c => (
          <option key={c.container_id} value={c.container_id}>
            {c.container_id}
          </option>
        ))}
      </select>

      {records.length > 0 && (
        <table className="records-table">
          <thead>
            <tr>
              {Object.keys(records[0]).map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {records.map((row, idx) => (
              <tr key={idx}>
                {Object.values(row).map((val, i) => (
                  <td key={i}>{val}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default RecordsFilterPage;
