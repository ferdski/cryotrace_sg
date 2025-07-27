import { useState } from "react";
import axios from "axios";
import { format } from "date-fns";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";

export default function ShipperRouteViewer() {
  const [shipperId, setShipperId] = useState("shipper-ln2-30-0008");
  const [routeData, setRouteData] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchRouteData = async () => {
    if (!shipperId) return;
    setLoading(true);
    try {
      const API_BASE = process.env.REACT_APP_API_BASE_URL || "";
      const res = await axios.get(`${API_BASE}/api/shippers/${shipperId}/routes`);
      setRouteData(res.data);
    } catch (error) {
      console.error("❌ Error fetching route data:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), "MMM d, yyyy h:mm a");
    } catch {
      return "Invalid date";
    }
  };

  const renderField = (label: string, value: any, highlight?: boolean) => (
    <div className="flex gap-1">
      <span className="font-semibold text-gray-700">{label}:</span>
      <span className={highlight ? "text-red-600 font-bold" : "text-gray-900"}>
        {value ?? "N/A"}
      </span>
    </div>
  );

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="flex gap-3 items-center">
        <Input
          className="flex-1"
          placeholder="Enter Shipper ID (e.g. shipper-ln2-30-0008)"
          value={shipperId}
          onChange={(e) => setShipperId(e.target.value)}
        />
        <button
          onClick={fetchRouteData}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Fetch Route
        </button>
        <p>

        </p>
      </div>

      {loading && <p className="text-gray-600">Loading route data...</p>}

      {routeData.length > 0 ? (
        <div className="grid gap-10">
          {routeData.map((entry, index) => {
            const pickupWeight = parseFloat(entry.pickup_weight);
            const receivedWeight = parseFloat(entry.received_weight_kg);
            const weightLoss = pickupWeight - receivedWeight;
            const highlightLoss = !isNaN(weightLoss) && weightLoss > 1;

            return (
              <div key={index}>
                <Card className="shadow-md border border-gray-200 rounded-lg">
                  <CardContent className="p-6 space-y-6">
                    {/* Manifest */}
                    <div className="space-y-2 border-b pb-3">
                      <div className="flex items-center gap-2 text-xl font-bold text-gray-800">
                        <span className="text-gray-700 text-xl">📄</span>
                        <span>Manifest ID: {entry.manifest_id}</span>
                      </div>
                      <div className="grid md:grid-cols-2 gap-4">
                        {renderField("Scheduled Ship Time", formatDate(entry.scheduled_ship_time))}
                        {renderField("Expected Receive Time", formatDate(entry.expected_receive_time))}
                        {renderField("Evaporation Rate", `${entry.evaporation_rate_kg_per_hour || "N/A"} kg/hr`)}
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      {/* Pickup */}
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-lg font-semibold text-blue-700 border-b pb-1">
                          <span className="text-xl">📍</span>
                          <span>Pickup</span>
                        </div>
                        {renderField("Company", entry.Origin)}
                        {renderField("Contact", entry.contact_name)}
                        {renderField("Time", formatDate(entry.pickup_time))}
                        {renderField("Weight", `${pickupWeight.toFixed(2)} kg`)}
                        {renderField("User ID", entry.pickup_user_id)}
                      </div>

                      {/* Dropoff */}
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-lg font-semibold text-green-700 border-b pb-1">
                          <span className="text-xl">✅</span>
                          <span>Dropoff</span>
                        </div>
                        {renderField("Company", entry.Destination)}
                        {renderField("Contact", entry.dropoff_contact)}
                        {renderField("Time", formatDate(entry.dropoff_time))}
                        {renderField(
                          "Weight",
                          `${receivedWeight.toFixed(2)} kg${highlightLoss ? ` (↓ ${weightLoss.toFixed(2)} kg)` : ""}`,
                          highlightLoss
                        )}
                        {renderField("User ID", entry.dropoff_user_id)}
                        {renderField("Evap rate (kg/hour)", entry.evaporation_rate_kg_per_hour)}
                        
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Divider between manifests */}
                {index < routeData.length - 1 && (
                  <hr className="my-6 border-t border-gray-300" />
                )}
              </div>
            );
          })}
        </div>
      ) : (
        !loading && <p className="text-gray-600">No data found for this shipper.</p>
      )}
    </div>
  );
}
