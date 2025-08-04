// AskAIPage.tsx (using CSS Modules)
import React, { useState } from 'react';
import axios from 'axios';
import styles from './AskAI.module.css';

const AskAIPage: React.FC = () => {
  const [shipperId, setShipperId] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [count, setCount] = useState<number | null>(null);
  const [shipments, setShipments] = useState<any[]>([]);

  const formatDateTime = (iso: string): string => {
    try {
      return new Intl.DateTimeFormat('en-US', {
        weekday: 'short', year: 'numeric', month: 'short', day: 'numeric',
        hour: 'numeric', minute: '2-digit', hour12: true
      }).format(new Date(iso));
    } catch {
      return iso;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAnswer('💭 Analyzing shipments...');

    try {
      const response = await axios.post(`${process.env.REACT_APP_API_BASE_URL}/api/ask-ai`, {
        question,
        shipper_id: shipperId || null,
      });

      const { ai_response, shipments, count } = response.data;

      setAnswer(ai_response || '⚠️ No AI response returned.');
      setShipments(shipments || []);
      setCount(count ?? null);
    } catch (err) {
      setAnswer('⚠️ Error retrieving answer from server.');
      console.error(err);
    }

    setLoading(false);
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.heading}>Ask AI About a Shipper</h1>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.formGroup}>
          <label className={styles.label}>Shipper ID (optional)</label>
          <input
            type="text"
            className={styles.input}
            value={shipperId}
            onChange={(e) => setShipperId(e.target.value)}
            placeholder="e.g. shipper-ln2-20-0010"
          />
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>Question</label>
          <textarea
            className={styles.textarea}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            placeholder="e.g. What was the evaporation rate for this shipment?"
            required
          />
        </div>

        <button
          type="submit"
          className={styles.button}
          disabled={loading}
        >
          {loading ? 'Asking AI...' : 'Submit'}
        </button>
      </form>

      {answer && (
        <div className={styles.answerBlock}>
          <h2 className={styles.answerTitle}>AI Answer:</h2>

          {!Array.isArray(answer) && typeof answer === 'string' && (
            <pre className={styles.answerText}>{answer}</pre>
          )}
        </div>
      )}

      {shipments.length > 0 && (
        <div className={styles.shipmentSection}>
          <h3 className={styles.shipmentTitle}>Shipment Logs ({shipments.length})</h3>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Pickup</th>
                  <th>Dropoff</th>
                  <th>Transit Time</th>
                  <th>Evap Rate</th>
                </tr>
              </thead>
              <tbody>
                {shipments.map((s, idx) => (
                  <tr key={idx}>
                    <td>{s.shipment_id}</td>
                    <td>
                      <div>{formatDateTime(s.pickup_time)}</div>
                      <div className={styles.subtext}>{s.pickup_contact}</div>
                    </td>
                    <td>
                      <div>{formatDateTime(s.delivery_time)}</div>
                      <div className={styles.subtext}>{s.receiver}</div>
                    </td>
                    <td>{s.transit_time_hours} hrs</td>
                    <td>{s.evaporation_rate_kg_per_hour} kg/hr</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AskAIPage;
