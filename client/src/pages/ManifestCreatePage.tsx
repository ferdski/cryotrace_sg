import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import styles from './ManifestCreatePage.module.css';

type LocationOpt = { id: number; label: string };
type ShipperOpt = { shipper_id: string };
type ContactOpt = { id: number; name: string };

const toMySQLDateTime = (d: Date | null) => {
  if (!d) return null;
  // YYYY-MM-DD HH:MM:SS (local -> assume server expects local; if UTC needed, use d.toISOString())
  const pad = (n: number) => String(n).padStart(2, '0');
  const yyyy = d.getFullYear();
  const mm = pad(d.getMonth() + 1);
  const dd = pad(d.getDate());
  const hh = pad(d.getHours());
  const mi = pad(d.getMinutes());
  const ss = pad(d.getSeconds());
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`;
};

// Fallback local generator if backend "next-id" not available
const generateManifestPreview = (latest?: string) => {
  const match = latest?.match(/MAN-(\d{6})/);
  console.log("match = ", match);
  if (match) {
    const next = String(parseInt(match[1], 10) + 1).padStart(6, '0');
    console.log("next = ", match);
    return `MAN-${next}`;
  }
  // Timestamp-based fallback
  const stamp = Date.now().toString().slice(-6);
  return `MAN-${stamp}`;
};

const ManifestCreatePage: React.FC = () => {
  const [manifestId, setManifestId] = useState<string>(''); // preview (read-only)
  const [shipperId, setShipperId] = useState('');
  const [originLocationId, setOriginLocationId] = useState<number | ''>('');
  const [originContactName, setOriginContactName] = useState('');
  const [destinationLocationId, setDestinationLocationId] = useState<number | ''>('');
  const [destinationContactName, setDestinationContactName] = useState('');
  const [scheduledShipTime, setScheduledShipTime] = useState<Date | null>(null);
  const [expectedReceiveTime, setExpectedReceiveTime] = useState<Date | null>(null);
  const [projectedWeightKg, setProjectedWeightKg] = useState<string>('');
  const [temperatureC, setTemperatureC] = useState<string>('');
  const [notes, setNotes] = useState('');
  const [createdByUserId, setCreatedByUserId] = useState<string>('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [shipperOpts, setShipperOpts] = useState<ShipperOpt[]>([]);
  const [locationOpts, setLocationOpts] = useState<LocationOpt[]>([]);
  const [originContacts, setOriginContacts] = useState<ContactOpt[]>([]);
  const [destContacts, setDestContacts] = useState<ContactOpt[]>([]);

  // Load shippers + locations + next manifest id
  useEffect(() => {
    console.log('origin:', window.location.origin);
    axios.get(`${process.env.REACT_APP_API_BASE_URL}/api/containers`)
      .then(res => setShipperOpts((res.data || []).map((r: any) => ({ shipper_id: r.shipper_id }))));

    axios.get(`${process.env.REACT_APP_API_BASE_URL}/api/locations`)
      .then(res => setLocationOpts((res.data || []).map((r: any) => ({
        id: r.id,
        label: `${r.city}, ${r.state}${r.company_name ? ' — ' + r.company_name : ''}`
      }))));

    // Try to fetch a server-provided next id; fallback locally
    axios.get(`${process.env.REACT_APP_API_BASE_URL}/api/manifests?filter=next-id`)
    .then(res => {
      console.log("API response data:", res.data.res)   // full object
      console.log("next_id:", res.data['next_id'])    // specific value
      setManifestId(res.data.res || generateManifestPreview())
    })
    .catch(err => {
      console.error("Error fetching next-id:", err)
      setManifestId(generateManifestPreview())
    })
  }, []);

  // When origin/destination location changes, fetch contacts for that location (if endpoint exists)
  useEffect(() => {
    if (originLocationId) {
      axios.get(`${process.env.REACT_APP_API_BASE_URL}/api/contacts?location_id=${originLocationId}`)
        .then(res => setOriginContacts(res.data || []))
        .catch(() => setOriginContacts([]));
    } else {
      setOriginContacts([]);
    }
  }, [originLocationId]);

  useEffect(() => {
    if (destinationLocationId) {
      axios.get(`${process.env.REACT_APP_API_BASE_URL}/api/contacts?location_id=${destinationLocationId}`)
        .then(res => setDestContacts(res.data || []))
        .catch(() => setDestContacts([]));
    } else {
      setDestContacts([]);
    }
  }, [destinationLocationId]);

  const canSubmit = useMemo(() => {
    return shipperId && originLocationId && destinationLocationId && scheduledShipTime;
  }, [shipperId, originLocationId, destinationLocationId, scheduledShipTime]);

  const reset = () => {
    setOriginContactName('');
    setDestinationContactName('');
    setScheduledShipTime(null);
    setExpectedReceiveTime(null);
    setProjectedWeightKg('');
    setTemperatureC('');
    setNotes('');
    setCreatedByUserId('');
    // Generate a new preview after save
    setManifestId(generateManifestPreview(manifestId));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = {
        // If backend expects you to send it, include; otherwise server should generate & return it.
        manifest_id: manifestId || null,
        shipper_id: shipperId,
        origin_location_id: Number(originLocationId),
        origin_contact_name: originContactName || null,
        destination_location_id: Number(destinationLocationId),
        destination_contact_name: destinationContactName || null,
        scheduled_ship_time: toMySQLDateTime(scheduledShipTime),
        expected_receive_time: expectedReceiveTime ? toMySQLDateTime(expectedReceiveTime) : null,
        projected_weight_kg: projectedWeightKg ? Number(projectedWeightKg) : null,
        temperature_c: temperatureC ? Number(temperatureC) : null,
        notes: notes || null,
        created_by_user_id: createdByUserId ? Number(createdByUserId) : null
      };

      await axios.post(`${process.env.REACT_APP_API_BASE_URL}/api/create-manifest`, payload);
      setSuccess('✅ Manifest created successfully.');
      reset();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to create manifest.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.heading}>Create Shipping Manifest</h1>

      <form className={styles.form} onSubmit={handleSubmit}>
        {/* Shipper */}
        <h2 className={styles.sectionHeading}>Shipper</h2>

        <div className={styles.rowInline}>
          <div className={styles.col}>
            <label htmlFor="manifest-id" className={styles.label}>Manifest ID (preview)</label>
            <input id="manifest-id" className={styles.input} value={manifestId} readOnly />
            <div className={styles.help}>Generated preview. The server may finalize this on save.</div>
          </div>

          <div className={styles.col}>
            <label htmlFor="shipper-id" className={styles.label}>Shipper ID *</label>
            <select
              id="shipper-id"
              className={styles.input}
              value={shipperId}
              onChange={(e) => setShipperId(e.target.value)}
              required
            >
              <option value="">-- Select a shipper --</option>
              {shipperOpts.map(s => (
                <option key={s.shipper_id} value={s.shipper_id}>{s.shipper_id}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Origin */}
        <h2 className={styles.sectionHeading}>Origin</h2>
        <div className={styles.rowInline}>
          <div className={styles.col}>
            <label htmlFor="origin-location" className={styles.label}>Origin Location *</label>
            <select
              id="origin-location"
              className={styles.input}
              value={originLocationId}
              onChange={(e) => setOriginLocationId(e.target.value ? Number(e.target.value) : '')}
              required
            >
              <option value="">-- Select origin --</option>
              {locationOpts.map(l => (
                <option key={l.id} value={l.id}>{l.label}</option>
              ))}
            </select>
          </div>

          <div className={styles.col}>
            <label htmlFor="origin-contact" className={styles.label}>Origin Contact</label>
            {originContacts.length > 0 ? (
              <select
                id="origin-contact"
                className={styles.input}
                value={originContactName}
                onChange={(e) => setOriginContactName(e.target.value)}
              >
                <option value="">-- Select contact --</option>
                {originContacts.map(c => (
                  <option key={c.id} value={c.name}>{c.name}</option>
                ))}
              </select>
            ) : (
              <input
                id="origin-contact"
                className={styles.input}
                value={originContactName}
                onChange={(e) => setOriginContactName(e.target.value)}
                placeholder="Full name, role"
              />
            )}
          </div>
        </div>

        {/* Destination */}
        <h2 className={styles.sectionHeading}>Destination</h2>
        <div className={styles.rowInline}>
          <div className={styles.col}>
            <label htmlFor="destination-location" className={styles.label}>Destination Location *</label>
            <select
              id="destination-location"
              className={styles.input}
              value={destinationLocationId}
              onChange={(e) => setDestinationLocationId(e.target.value ? Number(e.target.value) : '')}
              required
            >
              <option value="">-- Select destination --</option>
              {locationOpts.map(l => (
                <option key={l.id} value={l.id}>{l.label}</option>
              ))}
            </select>
          </div>

          <div className={styles.col}>
            <label htmlFor="destination-contact" className={styles.label}>Destination Contact</label>
            {destContacts.length > 0 ? (
              <select
                id="destination-contact"
                className={styles.input}
                value={destinationContactName}
                onChange={(e) => setDestinationContactName(e.target.value)}
              >
                <option value="">-- Select contact --</option>
                {destContacts.map(c => (
                  <option key={c.id} value={c.name}>{c.name}</option>
                ))}
              </select>
            ) : (
              <input
                id="destination-contact"
                className={styles.input}
                value={destinationContactName}
                onChange={(e) => setDestinationContactName(e.target.value)}
                placeholder="Full name, role"
              />
            )}
          </div>
        </div>

        {/* Shipment Details */}
        <h2 className={styles.sectionHeading}>Shipment Details</h2>

        <div className={styles.rowInline}>
          <div className={styles.col}>
            <label htmlFor="scheduled-ship-time" className={styles.label}>Scheduled Ship Time *</label>
            <DatePicker
              id="scheduled-ship-time"
              selected={scheduledShipTime}
              onChange={(date) => setScheduledShipTime(date as Date)}
              showTimeSelect
              timeIntervals={15}
              dateFormat="eee, MMM d, yyyy h:mm aa"
              placeholderText="Select date & time"
              className={styles.input}
              isClearable
            />
          </div>

          <div className={styles.col}>
            <label htmlFor="expected-receive-time" className={styles.label}>Expected Receive Time</label>
            <DatePicker
              id="expected-receive-time"
              selected={expectedReceiveTime}
              onChange={(date) => setExpectedReceiveTime(date as Date)}
              showTimeSelect
              timeIntervals={15}
              dateFormat="eee, MMM d, yyyy h:mm aa"
              placeholderText="Select date & time"
              className={styles.input}
              isClearable
            />
          </div>
        </div>

        <div className={styles.rowInline}>
          <div className={styles.col}>
            <label htmlFor="weight" className={styles.label}>Projected Weight (kg)</label>
            <input
              id="weight"
              className={styles.input}
              type="number"
              step="0.01"
              value={projectedWeightKg}
              onChange={(e) => setProjectedWeightKg(e.target.value)}
              placeholder="e.g. 19.50"
            />
          </div>
          <div className={styles.col}>
            <label htmlFor="temperature" className={styles.label}>Temperature (°C)</label>
            <input
              id="temperature"
              className={styles.input}
              type="number"
              step="0.1"
              value={temperatureC}
              onChange={(e) => setTemperatureC(e.target.value)}
              placeholder="-196.0"
            />
          </div>
        </div>

        <div className={styles.rowInline}>
          <div className={styles.col}>
            <label htmlFor="created-by" className={styles.label}>Created By (user id)</label>
            <input
              id="created-by"
              className={styles.input}
              type="number"
              value={createdByUserId}
              onChange={(e) => setCreatedByUserId(e.target.value)}
            />
          </div>
          <div className={styles.col}>
            <label htmlFor="notes" className={styles.label}>Notes</label>
            <textarea
              id="notes"
              className={styles.textarea}
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        </div>

        {error && <div className={styles.error}>{error}</div>}
        {success && <div className={styles.success}>{success}</div>}

        <div className={styles.actions}>
          <button type="submit" className={styles.button} disabled={!canSubmit || submitting}>
            {submitting ? 'Saving…' : 'Create Manifest'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ManifestCreatePage;
