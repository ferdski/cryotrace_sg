// src/components/RecordsAll.js
import React, { useEffect, useState } from 'react';
import RecordsTableAll from './RenderRecordsAll';


function RecordsAll() {
  const [containers, setContainers] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [records, setRecords] = useState([]);

  console.log(`ip = `, process.env.REACT_APP_API_BASE_URL);

  console.log(`baseUrl: ${process.env.REACT_APP_API_BASE_URL}`);

  const baseUrl = process.env.REACT_APP_API_BASE_URL;
  const fullUrl = `${baseUrl}/api/records`;
  console.log("Fetching from:", fullUrl); // ✅ Confirm this prints


  useEffect(() => {
      fetch(`${fullUrl}?filter=all&shipperId=${selectedId}`)
        .then((res) => res.json())
        .then((data) => setRecords(data))
        .catch((err) => {
          console.error('Error fetching records:', err);
        });

  }, [selectedId, fullUrl]);

  return (
    <div className="containers-list">
      <label htmlFor="container-select"><strong>Shipper Id:    </strong></label>


      {records.length > 0 && <RecordsTableAll records={records} />}
    </div>
  );
}

export default RecordsAll;

