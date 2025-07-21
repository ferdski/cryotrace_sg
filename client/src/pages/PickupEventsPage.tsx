import React, { useEffect, useState } from 'react';
import './PickupEventsPage.css';
const baseUrl = process.env.REACT_APP_API_BASE_URL;


type ManifestSummary = {
  manifest_id: string;
};

type Manifest = {
  manifest_id: string;
  shipper_id: string;
  origin: string;
  destination: string;
  scheduled_ship_time: string;
  expected_receive_time: string;
  created_by_user_id: number;
};

export default function PickupEventsPage() {
  const [manifests, setManifests] = useState<ManifestSummary[]>([]);
  const [selectedManifestId, setSelectedManifestId] = useState('');
  const [selectedManifest, setSelectedManifest] = useState<Manifest | null>(null);
  const [weight, setWeight] = useState('');
  const [weightType, setWeightType] = useState('pickup'); // or dropdown
  const [driverUserId, setDriverUserId] = useState('');
  const [photo, setPhoto] = useState<File | null>(null);
  const [notes, setNotes] = useState('');
  const [statusMessage, setStatusMessage] = useState('');

  const fullUrl = `${baseUrl}/api/manifests`;
  useEffect(() => {
    fetch(fullUrl)
      .then(res => res.json())
      .then(data => setManifests(data))
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedManifestId) return;
    fetch(`${fullUrl}?filter=1&manifestId=${selectedManifestId}`)
      .then(res => res.json())
      .then(data => setSelectedManifest(data[0] || null))
      .catch(console.error);
  }, [selectedManifestId]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {

    e.preventDefault();

    const formData = new FormData();
    formData.append('manifest_id', selectedManifestId);
    formData.append('measured_weight_kg', weight);
    formData.append('weight_type', weightType);
    formData.append('driver_user_id', driverUserId);
    if (photo) formData.append('photo', photo);
    formData.append('notes', notes);

    try {
      const res = await fetch(`${baseUrl}/api/pickup-events`, {
        method: 'POST',
        body: formData
      });
      const result = await res.json();
      setStatusMessage(result.status || result.error || 'No response');
    } catch (err) {
      console.error(err);
      setStatusMessage("Submission failed.");
    }
  };

  return (
    <div className="pickup-form-wrapper">
      <h2>Pickup Event</h2>

      <form onSubmit={handleSubmit}>
        <label>
          Manifest ID:
          <select value={selectedManifestId} onChange={e => setSelectedManifestId(e.target.value)} required>
            <option value="">Select</option>
            {manifests.map(m => (
              <option key={m.manifest_id} value={m.manifest_id}>{m.manifest_id}</option>
            ))}
          </select>
        </label>

        {selectedManifest && (
          <div className="manifest-info">
            <p><strong>Shipper ID:</strong> {selectedManifest.shipper_id}</p>
            <p><strong>Origin:</strong> {selectedManifest.origin}</p>
            <p><strong>Destination:</strong> {selectedManifest.destination}</p>
          </div>
        )}

        <label>
          Weight (kg):
          <input type="number" step="0.01" value={weight} onChange={e => setWeight(e.target.value)} required />
        </label>

        <label>
          Weight Type:
          <select value={weightType} onChange={e => setWeightType(e.target.value)} required>
            <option value="pickup">Pickup</option>
            <option value="interim">Interim</option>
            <option value="dropoff">Dropoff</option>
          </select>
        </label>

        <label>
          Driver User ID:
          <input type="number" value={driverUserId} onChange={e => setDriverUserId(e.target.value)} required />
        </label>

        <label>
          Photo:
          <input
            type="file"
            accept="image/*"
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              const file = e.target.files?.[0];
              if (file) {
                setPhoto(file);
              }
            }}
            required
          />
        </label>

        <label>
          Notes:
          <textarea value={notes} onChange={e => setNotes(e.target.value)} />
        </label>

        <button type="submit">Submit Pickup</button>
      </form>

      {statusMessage && <p>{statusMessage}</p>}
    </div>
  );
}
