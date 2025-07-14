import React, { useEffect, useState } from 'react';
import './ContainersList.css';

function ContainersList() {
  const [containers, setContainers] = useState([]);

  console.log(`baseUrl: ${process.env.REACT_APP_API_BASE_URL}`);
useEffect(() => {
  const baseUrl = process.env.REACT_APP_API_BASE_URL;
  const fullUrl = `${baseUrl}/api/containers`;

  console.log("Fetching from:", fullUrl); // ✅ Confirm this prints

  fetch(fullUrl)
    .then((res) => res.json())
    .then((data) => setContainers(data))
    .catch((err) => console.error("Error fetching containers:", err));
}, []);

  /*useEffect(() => {
  fetch("http://localhost:3001/api/containers")
    .then((res) => res.json())
    .then((data) => setContainers(data))
    .catch((err) => console.error("Error fetching containers:", err));
}, []);*/

  return (
    <div className="containers-list">
      <h2>Containers</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Shape</th>
            <th>Dimensions</th>
            <th>Max Capacity (kg)</th>
            <th>Manufactured</th>
            <th>Other Specs</th>
          </tr>
        </thead>
        <tbody>
          {containers.map(container => (
            <tr key={container.container_id}>
              <td>{container.container_id}</td>
              <td>{container.type}</td>
              <td>{container.shape}</td>
              <td>{container.dimensions}</td>
              <td>{parseFloat(container.max_capacity).toFixed(1)}</td>
              <td>{new Date(container.manufacture_date).toLocaleDateString()}</td>
              <td>{container.other_specs}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ContainersList;
