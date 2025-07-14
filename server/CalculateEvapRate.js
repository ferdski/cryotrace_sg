async function processEvaporationRate(receiveRecord) {
  const { container_id, timestamp: receiveTime, weight: receiveWeight, shipment_id } = receiveRecord;

  // 1. Find the latest "ship" record before the receive
  const [ship] = await pool.query(`
    SELECT * FROM Shipment_Records
    WHERE container_id = ? AND transit = 'ship' AND timestamp < ?
    ORDER BY timestamp DESC LIMIT 1
  `, [container_id, receiveTime]);

  if (!ship.length) return console.warn("No matching ship record found.");

  const shipWeight = ship[0].weight;
  const weightLoss = shipWeight - receiveWeight;

  // Constants
  const HEAT_OF_VAPORIZATION = 1.992e5;
  const DENSITY_LN2 = 808;
  const CUBIC_METERS_TO_LITERS = 1000;

  const energyRequired = weightLoss * HEAT_OF_VAPORIZATION;
  const volume_m3 = weightLoss / DENSITY_LN2;
  const volume_L = volume_m3 * CUBIC_METERS_TO_LITERS;

  print("evap rate: ", volume_L);
  return volume_L;


}
