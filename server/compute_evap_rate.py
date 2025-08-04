def compute_evaporation_volume(ship_weight_kg: float, receive_weight_kg: float) -> float:
    """
    Computes volume of LN2 lost (in liters) between shipping and receiving weights.

    Args:
        ship_weight_kg: Weight at time of shipping (kg)
        receive_weight_kg: Weight at time of receiving (kg)

    Returns:
        Volume of liquid nitrogen lost, in liters
    """
    HEAT_OF_VAPORIZATION = 1.992e5     # J/kg (not used here, but kept for context)
    DENSITY_LN2 = 808                  # kg/m³
    CUBIC_METERS_TO_LITERS = 1000

    weight_loss = ship_weight_kg - receive_weight_kg
    if weight_loss <= 0:
        print("⚠️ No weight loss detected or invalid input.")
        return 0.0

    volume_m3 = weight_loss / DENSITY_LN2
    volume_liters = volume_m3 * CUBIC_METERS_TO_LITERS

    print(f"Evaporation volume: {volume_liters:.2f} L from {weight_loss:.2f} kg lost")
    return volume_liters