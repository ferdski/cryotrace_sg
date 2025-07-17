// src/components/RecordsTable.js
import React from 'react';
import './ContainersList.css'; // Reuse the styling

function RenderRecordsTableManifestId({ records }) {
  return (
    <div className="containers-list">
      <h2>Shipment Records by Manifest Id</h2>
      <table>
        <thead>
          <tr>
          <th>Manifest ID</th>
            <th>Manifest Created time</th>
            <th>Shipper ID</th>
            <th>Scheduled ship time</th>
            <th>Origin</th>
            <th>Destination</th>
            <th>Weight (kg)</th>
            <th>User id</th>
            <th>Condition</th>
            <th>Image</th>
          </tr>
        </thead>
        <tbody>
          {records.map(record => (
            <tr key={record.record_id}>
              <td>{record.manifest_id}</td>
              <td>{new Date(record.created_at).toLocaleString()}</td>
              <td>{record.shipper_id}</td>
              <td>{new Date(record.scheduled_ship_time).toLocaleString()}</td>
              <td>{record.origin}</td>
              <td>{record.destination}</td>
              <td>{parseFloat(record.projected_weight_kg).toFixed(1)}</td>
              <td>{record.created_by_user_id}</td>
              <td>{record.notes}</td>
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

export default RenderRecordsTableManifestId;
