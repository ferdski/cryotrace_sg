import { useEffect, useState } from "react";
import axios from "axios";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";

export default function ShipperRouteViewer() {
  const [shipperId, setShipperId] = useState("shipper-ln2-30-0008");
  const [routeData, setRouteData] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchRouteData = async () => {
    console.log("🟡 fetchRouteData called"); // <-- NEW
    if (!shipperId) {
      console.log("⚠️ shipperId is blank, exiting.");
      return;
    }
    console.log("✅ Fetching routes for:", shipperId);
    setLoading(true);
    try {
      const API_BASE = process.env.REACT_APP_API_BASE_URL || '';
      const res = await axios.get(`${API_BASE}/api/shippers/${shipperId}/routes`);
      console.log("res.data:", res.data);
      setRouteData(res.data);
    } catch (error) {
      console.error("❌ Error fetching route data:", error);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="p-6 space-y-4">
      <div className="flex gap-2 items-center">
        <Input
          placeholder="Enter Shipper ID (e.g. shipper-ln2-30-0008)"
          value={shipperId}
          onChange={(e) => setShipperId(e.target.value)}
        />
      <button onClick={fetchRouteData}>
        Fetch Route (test button)
      </button>
      </div>

      {routeData.length > 0 ? (
        <div className="grid gap-4">
          {Array.isArray(routeData) && routeData.length > 0 ? (
            <div className="grid gap-4">
                {routeData.map((entry, index) => (
                <Card key={index}>
                    <CardContent className="p-4 space-y-2">
                      <div><strong>Manifest ID:</strong> {entry.manifest_id}</div>
                      <div><strong>Scheduled Ship Time:</strong> {entry.scheduled_ship_time}</div>
                      <div><strong>Expected Receive Time:</strong> {entry.expected_receive_time}</div>

                      <div><strong>Pickup:</strong></div>
                      <ul className="ml-4 list-disc">
                        <li><strong>Company:</strong> {entry.Origin}</li>
                        <li><strong>Contact:</strong> {entry.contact_name}</li>
                        <li><strong>Time:</strong> {entry.pickup_time}</li>
                        <li><strong>Weight:</strong> {entry.pickup_weight} kg</li>
                        <li><strong>User ID:</strong> {entry.pickup_user_id}</li>
                      </ul>

                      <div><strong>Dropoff:</strong></div>
                      <ul className="ml-4 list-disc">
                        <li><strong>Company:</strong> {entry.Destination}</li>
                        <li><strong>Contact:</strong> {entry.dropoff_contact}</li>
                        <li><strong>Time:</strong> {entry.dropoff_time}</li>
                        <li><strong>Weight:</strong> {entry.received_weight_kg} kg</li>
                        <li><strong>User ID:</strong> {entry.dropoff_user_id}</li>
                        <li><strong>Evap Rate (kg/hr):</strong> {entry.evaporation_rate_kg_per_hour}</li>
                      </ul>
                    </CardContent>
                </Card>
                ))}
            </div>
            ) : (
            <p className="text-gray-600">1 No data found for this shipper.</p>
            )}
        </div>
      ) : (
        <p className="text-gray-600">2 No data found for this shipper.</p>
      )}
    </div>
  );
}
