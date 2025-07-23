
import React, { useEffect, useState } from 'react';
import './PickupEventsPage.css';  // use same CSS for pickup and dropoff
const baseUrl = process.env.REACT_APP_API_BASE_URL;

interface Manifest {
  manifest_id: string;
  shipper_id: string;
  origin: string;
  destination: string;
  destination_location_id: string;
  scheduled_ship_time: string;
  expected_receive_time: string;
  created_by_user_id: number;
}

const DropoffEventsPage: React.FC = () => {
  const [manifests, setManifests] = useState<Manifest[]>([]);
  const [selectedManifestId, setSelectedManifestId] = useState('');
  const [selectedManifest, setSelectedManifest] = useState<Manifest | null>(null);
  const [weight, setWeight] = useState<number | ''>('');
  const [weightType, setWeightType] = useState('kg');
  const [photo, setPhoto] = useState<File | null>(null);
  const [notes, setNotes] = useState('');
  const [driverUserId, setDriverUserId] = useState<number | ''>('');
  const [overrideLocation, setOverrideLocation] = useState('');


  const fullUrl = `${baseUrl}/api/manifests`;
  useEffect(() => {
    fetch(fullUrl)
      .then(res => res.json())
      .then(setManifests)
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedManifestId) return;
    fetch(`${fullUrl}?filter=1&manifestId=${selectedManifestId}`)
      .then(res => res.json())
      .then(data => setSelectedManifest(data[0] || null))
      .catch(console.error);
  }, [selectedManifestId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!photo || !selectedManifestId || !weight || !driverUserId) return alert('All required fields must be filled.');

    console.log(`"photo: ${"photo"}`)
    const formData = new FormData();
    formData.append('manifest_id', selectedManifestId);
    formData.append('received_contact_name', 'Lab Manager')
    formData.append('received_weight_kg', String(weight));
    formData.append('condition_notes', notes);
    formData.append('image_path', photo);
    formData.append('received_by_user_id', String(driverUserId));

    // This field sends the manifest's destination ID or placeholder
    formData.append('received_location_id', selectedManifest?.destination_location_id || '');

    // ✅ Only send override if user typed one
    /*if (overrideLocation.trim()) {
      formData.append('override_location_text', overrideLocation);
    }*/

    try {
      const res = await fetch(`${baseUrl}/api/dropoff-events`, {
        method: 'POST',
        body: formData
      });

      const result = await res.json();
      if (res.ok) {
        alert('Dropoff event submitted!');
        setWeight('');
        setPhoto(null);
        setNotes('');
        setDriverUserId('');
      } else {
        alert(`Error: ${result.error}`);
      }
    } catch (err) {
      console.error('Submit error:', err);
    }
  };

  return (
    <div className={"pickup-form-wrapper"}>
      <h2>Dropoff Event</h2>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <label>
          Manifest ID:
          <select value={selectedManifestId} onChange={e => setSelectedManifestId(e.target.value)} required>
            <option value="">Select manifest</option>
            {manifests.map((m) => (
              <option key={m.manifest_id} value={m.manifest_id}>{m.manifest_id}</option>
            ))}
          </select>
        </label>

        {selectedManifest && (
          <div className="manifest-details">
            <div><strong>Shipper ID:</strong> {selectedManifest.shipper_id}</div>
            <div><strong>Origin:</strong> {selectedManifest.origin}</div>
            <div><strong>Destination:</strong> {selectedManifest.destination}</div>
            <div><strong>Scheduled Ship:</strong> {selectedManifest.scheduled_ship_time}</div>
            <div><strong>Expected Receive:</strong> {selectedManifest.expected_receive_time}</div>
            <div><strong>Created By:</strong> {selectedManifest.created_by_user_id}</div>
          </div>
        )}
        <label>
          Expected Dropoff Location:
          <input
            type="text"
            value={selectedManifest?.destination || ''}
            readOnly
            className="readonly-field"
          />
        </label>

        <label>
          Override Dropoff Location (optional):
          <input
            type="text"
            placeholder="Enter alternate location (if different)"
            value={overrideLocation}
            onChange={e => setOverrideLocation(e.target.value)}
          />
        </label>
        <label>
          Weight:
          <input type="number" step="0.01" value={weight} onChange={e => setWeight(parseFloat(e.target.value) || '')} required />
        </label>

        <label>
          Weight Type:
          <select value={weightType} onChange={e => setWeightType(e.target.value)}>
            <option value="kg">kg</option>
            <option value="lbs">lbs</option>
          </select>
        </label>

        <label>
          Dropoff Photo:
          <input type="file" accept="image/*" onChange={e => setPhoto(e.target.files?.[0] || null)} required />
        </label>

        <label>
          Driver User ID:
          <input type="number" value={driverUserId} onChange={e => setDriverUserId(parseInt(e.target.value) || '')} required />
        </label>

        <label>
          Notes:
          <textarea value={notes} onChange={e => setNotes(e.target.value)} />
        </label>

        <button type="submit" style={{ padding: 10, fontSize: '1em' }}>Submit Dropoff</button>
      </form>
    </div>
  );
};

export default DropoffEventsPage;
