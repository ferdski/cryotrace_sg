import React, { useEffect, useState } from 'react';
import './PickupEventsPage.css';
const baseUrl = process.env.REACT_APP_API_BASE_URL;

interface Manifest {
  manifest_id: string;
  shipper_id: string;
  origin: string;
  destination: string;
  scheduled_ship_time: string;
  expected_receive_time: string;
  created_by_user_id: number;
}

const PickupEventsPage: React.FC = () => {
  const [manifests, setManifests] = useState<Manifest[]>([]);
  const [selectedManifestId, setSelectedManifestId] = useState<string>('');
  const [selectedManifest, setSelectedManifest] = useState<Manifest | null>(null);
  const [weight, setWeight] = useState<number | ''>('');
  const [weightType, setWeightType] = useState<string>('kg');
  const [photo, setPhoto] = useState<File | null>(null);
  const [notes, setNotes] = useState<string>('');

  const fullUrl = `${baseUrl}/api/manifests`;
  console.log('fullUrl:', fullUrl)
  useEffect(() => {
    
    fetch(fullUrl)
      .then(res => res.json())
      .then(data => {
        console.log('Fetched manifests:', data); 
        setManifests(data);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    console.log('selectedmanifestId',selectedManifestId);
    if (selectedManifestId) {
      fetch(`${fullUrl}?filter=manifest&manifestId=${selectedManifestId}`)
        .then(res => res.json())
        .then(data => {
            console.log('Fetched manifest by Id:', data); 
          if (Array.isArray(data) && data.length > 0) {
            setSelectedManifest(data[0]);
          } else {
            setSelectedManifest(null);
          }
        })
        .catch(console.error);
    } else {
      setSelectedManifest(null);
    }
  }, [selectedManifestId]);

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setPhoto(e.target.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!selectedManifestId || weight === '' || !weightType || !photo) {
      alert('Please fill out all required fields.');
      return;
    }

    const fullUrl = `${baseUrl}/api/pickup-events`;
    const formData = new FormData();
    formData.append('manifest_id', selectedManifestId);
    formData.append('weight', weight.toString());
    formData.append('weight_type', weightType);
    formData.append('notes', notes);
    formData.append('photo', photo);
    console.log(formData);

    try {
      const res = await fetch(fullUrl, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Failed to submit pickup event');

      alert('Pickup event submitted successfully!');
      setSelectedManifestId('');
      setWeight('');
      setWeightType('kg');
      setPhoto(null);
      setNotes('');
    } catch (err) {
      console.error(err);
      alert('Error submitting event.');
    }
  };

  return (
    <div className="pickup-form-wrapper">
      <h1>Pickup Event</h1>

      <label>Select Manifest</label>
      <select
        value={selectedManifestId}
        onChange={(e) => setSelectedManifestId(e.target.value)}
      >
        <option value="">-- Select --</option>
        {manifests.map((m) => (
          <option key={m.manifest_id} value={m.manifest_id}>
            {m.manifest_id}
          </option>
        ))}
      </select>

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

      <label>Weight</label>
      <input
        type="number"
        value={weight}
        onChange={(e) => setWeight(parseFloat(e.target.value))}
      />

      <label>Weight Type</label>
      <select value={weightType} onChange={(e) => setWeightType(e.target.value)}>
        <option value="kg">kg</option>
        <option value="lbs">lbs</option>
      </select>

      <label>Photo (Camera)</label>
      <input
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handlePhotoChange}
      />

      <label>Notes</label>
      <textarea
        rows={3}
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />

      <button onClick={handleSubmit}>
        Submit Pickup Event
      </button>
    </div>
  );
};

export default PickupEventsPage;
