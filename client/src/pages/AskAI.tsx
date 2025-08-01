import React, { useState } from 'react';
import axios from 'axios';

const AskAIPage: React.FC = () => {
  const [shipperId, setShipperId] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAnswer('');

    try {
      console.log("url: ", process.env.REACT_APP_API_BASE_URL, question);
      const response = await axios.post(`${process.env.REACT_APP_API_BASE_URL}/api/ask-ai`, {
        question,
        shipper_id: shipperId || null
      });

      setAnswer(response.data.answer);
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
