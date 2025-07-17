import React, { useEffect, useState } from 'react';

interface Manifest {
  manifest_id: string;
  shipper_id: string;
  origin: string;
  destination: string;
  scheduled_ship_time: string;
  expected_receive_time: string;
  created_by_user_id: string;
}

const PickupEventsPage: React.FC = () => {
  const [manifests, setManifests] = useState<Manifest[]>([]);
  const [selectedManifestId, setSelectedManifestId] = useState<string>('');
  const [selectedManifest, setSelectedManifest] = useState<Manifest | null>(null);
  const [weight, setWeight] = useState<number | ''>('');
  const [weightType, setWeightType] = useState<string>('kg');
  const [photo, setPhoto] = useState<File | null>(null);
  const [notes, setNotes] = useState<string>('');

  const baseUrl = process.env.REACT_APP_API_BASE_URL;
  const fullUrl = `${baseUrl}/api/manifests`;
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
    if (selectedManifestId) {
      fetch(`${fullUrl}?filter=manifest&shipperId=${selectedManifestId}`)
        .then(res => res.json())
        .then(data => {
            console.log('Fetched manifest by Id:', data); 
            setSelectedManifest(data);
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

    const formData = new FormData();
    formData.append('manifest_id', selectedManifestId);
    formData.append('weight', weight.toString());
    formData.append('weight_type', weightType);
    formData.append('notes', notes);
    formData.append('photo', photo);

    try {
      const res = await fetch('/api/pickup-events', {
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
    <div className="p-4 max-w-md mx-auto space-y-4">
      <h1 className="text-xl font-bold mb-2">Pickup Event</h1>

      <div>
        <label className="block text-sm font-medium mb-1">Select Manifest</label>
        <select
          className="w-full border p-2 rounded"
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
      </div>

      {selectedManifest && (
        <div className="border rounded p-3 bg-gray-50 text-sm space-y-1">
          <div><strong>Shipper ID:</strong> {selectedManifest.shipper_id}</div>
          <div><strong>Origin:</strong> {selectedManifest.origin}</div>
          <div><strong>Destination:</strong> {selectedManifest.destination}</div>
          <div><strong>Scheduled Ship:</strong> {selectedManifest.scheduled_ship_time}</div>
          <div><strong>Expected Receive:</strong> {selectedManifest.expected_receive_time}</div>
          <div><strong>Created By:</strong> {selectedManifest.created_by_user_id}</div>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium mb-1">Weight</label>
        <input
          type="number"
          className="w-full border p-2 rounded"
          value={weight}
          onChange={(e) => setWeight(parseFloat(e.target.value))}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Weight Type</label>
        <select
          className="w-full border p-2 rounded"
          value={weightType}
          onChange={(e) => setWeightType(e.target.value)}
        >
          <option value="kg">kg</option>
          <option value="lbs">lbs</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Photo (Camera)</label>
        <input
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handlePhotoChange}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Notes</label>
        <textarea
          className="w-full border p-2 rounded"
          value={notes}
          rows={3}
          onChange={(e) => setNotes(e.target.value)}
        />
      </div>

      <button
        onClick={handleSubmit}
        className="w-full bg-blue-600 text-white p-3 rounded font-semibold"
      >
        Submit Pickup Event
      </button>
    </div>
  );
};

export default PickupEventsPage;
