import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  CategoryScale,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import './EvaporationRatePage.css'; // ⬅️ add this import

// Register chart components
ChartJS.register(LineElement, PointElement, LinearScale, Title, CategoryScale, Tooltip, Legend);

export default function EvaporationRatePage() {
  const [containers, setContainers] = useState<any[]>([]);
  const [selectedShipper, setSelectedShipper] = useState<string>('');
  const [evapData, setEvapData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const API_BASE = process.env.REACT_APP_API_BASE_URL || '';

  // 1) Fetch list of shipper IDs once on page load
  useEffect(() => {
    async function fetchContainers() {
      try {
        const res = await axios.get(`${API_BASE}/api/containers`);
        setContainers(res.data);
      } catch (err) {
        console.error('Error fetching containers:', err);
      }
    }
    fetchContainers();
  }, []);

  // 2) Fetch evaporation data for selected shipper
  useEffect(() => {
    if (!selectedShipper) return;

    async function fetchEvaporationData() {
      setLoading(true);
      try {
        const res = await axios.get(`${API_BASE}/api/shippers/${selectedShipper}/routes`);
        const cleaned = res.data.map((entry: any, index: number) => ({
          index: index + 1,
          evap: parseFloat(entry.evaporation_rate_kg_per_hour),
          manifest_id: entry.manifest_id,
        }));
        setEvapData(cleaned);
      } catch (err) {
        console.error('Error fetching evaporation data:', err);
        setEvapData([]);
      } finally {
        setLoading(false);
      }
    }
    fetchEvaporationData();
  }, [selectedShipper]);

  return (
    <div className="evap-page">
      <h1 className="evap-title">📊 Evaporation Rates</h1>

      <div className="evap-controls">
        <label htmlFor="shipper-select" className="evap-label">
          Select Shipper:
        </label>
        <select
          id="shipper-select"
          value={selectedShipper}
          onChange={(e) => setSelectedShipper(e.target.value)}
          className="evap-select"
        >
          <option value="">-- Select --</option>
          {containers.map((container) => (
            <option key={container.shipper_id} value={container.shipper_id}>
              {container.shipper_id}
            </option>
          ))}
        </select>
      </div>

      {loading && <p className="evap-loading">Loading evaporation data...</p>}

      {!loading && evapData.length > 0 && (
        <div className="evap-chart">
          <Line
            data={{
              labels: evapData.map((d) => d.manifest_id || `#${d.index}`),
              datasets: [
                {
                  label: 'Evaporation Rate (kg/hr)',
                  data: evapData.map((d) => d.evap),
                  fill: false,
                  borderColor: '#3b82f6',
                  backgroundColor: '#3b82f6',
                  tension: 0.3,
                  pointRadius: 4,
                  pointHoverRadius: 6,
                },
              ],
            }}
            options={{
              responsive: true,
              plugins: {
                legend: { display: true, position: 'top' },
                tooltip: {
                  callbacks: {
                    label: (ctx) => `${ctx.parsed.y} kg/hr`,
                  },
                },
              },
              scales: {
                y: { title: { display: true, text: 'Evap Rate (kg/hr)' } },
                x: { title: { display: true, text: 'Manifest ID' } },
              },
            }}
          />
        </div>
      )}

      {!loading && selectedShipper && evapData.length === 0 && (
        <p className="evap-empty">No evaporation data found for this shipper.</p>
      )}
    </div>
  );
}

