// src/components/RecordsTable.js
import React from 'react';
import './ContainersList.css'; // Reuse the styling

function RenderRecordsTableDate({ records }) {
  return (
    <div className="containers-list">
      <h2>Shipment Records</h2>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Location</th>
            <th>Transit</th>
            <th>Weight (kg)</th>
            <th>User id</th>
            <th>Condition</th>
            <th>Image</th>
          </tr>
        </thead>
        <tbody>
          {records.map(record => (
            <tr key={record.record_id}>
              <td>{new Date(record.timestamp).toLocaleString()}</td>
              <td>{record.location}</td>
              <td>{record.transit}</td>
              <td>{parseFloat(record.weight).toFixed(1)}</td>
              <td>{record.user_id}</td>
              <td>{record.condition_notes}</td>
              <td>
                {record.image_path ? (
                  <a href={record.image_path} target="_blank" rel="noopener noreferrer">View</a>
                ) : (
                  '—'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default RenderRecordsTableDate;
