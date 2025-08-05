// src/components/RecordsTable.js
import React from 'react';
import './ContainersList.css'; // Reuse the styling

function RenderTransitShipperTableLocation({ records }) {
  return (
    <div className="containers-list">
      <h2>Transit Records for this Shipper by Origin </h2>
      <table>
      <thead>
          <tr>
          <th>Origin</th>
          <th>Manifest ID</th>
            <th>Manifest Created time</th>
            <th>Shipper ID</th>
            <th>Pickup date/time</th>
            <th>Pickup Contact</th>
            <th>Pickup Weight (kg)</th>   
            <th>Dropoff date (kg)</th>            
            <th>Destination</th>
            <th>Dropoff Contact</th>
            <th>Dropoff Weight (kg)</th>            
            <th>User id</th>
            <th>Condition</th>
            <th>Image</th>
          </tr>
        </thead>
        <tbody>
        {records.map(record => (
            <tr key={record.record_id}>
              <td>{record.origin}</td>
              <td>{record.manifest_id}</td>
              <td>{new Date(record.created_at).toLocaleString()}</td>
              <td>{record.shipper_id}</td>
              <td>{new Date(record.pickup_time).toLocaleString()}</td>
              <td>{record.pickup_contact}</td>
              <td>{parseFloat(record.pickup_weight).toFixed(1)}</td>              
              <td>{new Date(record.dropoff_time).toLocaleString()}</td>
              <td>{record.destination}</td>
              <td>{record.dropoff_contact}</td>
              <td>{parseFloat(record.dropoff_weight).toFixed(1)}</td>
              <td>{record.dropoff_user_id}</td>
              <td>{record.dropoff_notes}</td>
              <td>
                {record.image_path ? (
                  <a href={record.image_path} target="_blank" rel="noopener noreferrer">View</a>
                ) : (
                  'image path'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default RenderTransitShipperTableLocation;
