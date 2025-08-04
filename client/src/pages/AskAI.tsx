import React, { useState } from 'react';
import axios from 'axios';
import { PackageCheck, PackageOpen } from 'lucide-react';
import { Truck, CheckCircle } from 'lucide-react';

const AskAIPage: React.FC = () => {
  const [shipperId, setShipperId] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [count, setCount] = useState<number | null>(null);
  const [shipments, setShipments] = useState<any[]>([]);

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
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Ask AI About a Shipper</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Shipper ID (optional)</label>
          <input
            type="text"
            className="w-full p-2 border rounded"
            value={shipperId}
            onChange={(e) => setShipperId(e.target.value)}
            placeholder="e.g. shipper-ln2-20-0010"
          />
        </div>

        <div>
          <label className="block text-sm font-medium">Question</label>
          <textarea
            className="w-full p-2 border rounded"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            placeholder="e.g. What was the evaporation rate for this shipment?"
            required
          />
        </div>

        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          disabled={loading}
        >
          {loading ? 'Asking AI...' : 'Submit'}
        </button>
      </form>

      {answer && (
        <div className="mt-6 bg-gray-100 p-4 rounded border">
          <h2 className="font-semibold mb-2">AI Answer:</h2>
          {Array.isArray(answer) && (
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {answer.map((card, idx) => (
                <div key={idx} className="bg-white p-4 border rounded shadow">
                  <h3 className="text-lg font-semibold">{card.title}</h3>
                  <p className="text-blue-700 text-xl">{card.value}</p>
                  {card.note && <p className="text-sm text-gray-500 mt-2">{card.note}</p>}
                </div>
              ))}
            </div>
          )}


          {shipments.length > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold mb-2">Shipment Logs</h3>
              <div className="overflow-x-auto border rounded shadow-sm">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50 text-left">
                  <tr>
                    <th className="px-4 py-2 font-medium text-gray-700">ID</th>
                    <th className="px-4 py-2 font-medium text-gray-700">
                      <div className="flex items-center gap-1">
                        <Truck className="w-4 h-4" /> Pickup
                      </div>
                    </th>
                    <th className="px-4 py-2 font-medium text-gray-700">
                      <div className="flex items-center gap-1">
                        <CheckCircle className="w-4 h-4" /> Dropoff
                      </div>
                    </th>
                    <th className="px-4 py-2 font-medium text-gray-700">Transit Time</th>
                    <th className="px-4 py-2 font-medium text-gray-700">Evap Rate</th>
                  </tr>
                </thead>
                  <tbody className="divide-y divide-gray-100 bg-white">
                    {shipments.map((s, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium text-blue-700">{s.shipment_id}</td>
                        <td className="px-4 py-2 text-gray-800">
                          <div>{s.pickup_time}</div>
                          <div className="text-gray-500 text-xs">{s.pickup_contact}</div>
                        </td>
                        <td className="px-4 py-2 text-gray-800">
                          <div>{s.delivery_time}</div>
                          <div className="text-gray-500 text-xs">{s.receiver}</div>
                        </td>
                        <td className="px-4 py-2 text-gray-800">{s.transit_time_hours} hrs</td>
                        <td className="px-4 py-2 text-gray-800">{s.evaporation_rate_kg_per_hour} kg/hr</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        

          {!Array.isArray(answer) && typeof answer === 'string' && (
            <div className="mt-6 bg-gray-100 p-4 rounded border">
              <h2 className="font-semibold mb-2"></h2>
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>{answer}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AskAIPage;
