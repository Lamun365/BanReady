const API_BASE_URL = "https://smock-suggest-vagabond.ngrok-free.dev";


export type ParkingCheckRequest = {
  latitude: number;
  longitude: number;

  declared_ban_active: boolean;
  snow_emergency_active: boolean;
  permanent_time_restriction_active: boolean;
};


export type ParkingCheckResponse = {
  matched: boolean;

  status:
    | "MUST_MOVE"
    | "CAN_STAY_DURING_BAN"
    | "NOT_AFFECTED"
    | "VERIFY_RULE";

  reason: string;

  street_name: string;

  segment_id: number | null;
  street_id: number | null;

  distance_meters: number | null;

  ban_type: string;
  ban_zone: string;

  restricted_side: string;

  geometric_side: string;

  parked_side: string;

  left_parity: string;
  right_parity: string;

  parity_confidence: string;

  // Added in API 0.4.0
  permanent_ban_active?: boolean;
  checked_at?: string;
};


export async function checkParking(
  request: ParkingCheckRequest
): Promise<ParkingCheckResponse> {
  const response = await fetch(
    `${API_BASE_URL}/parking/check`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(request),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();

    throw new Error(
      `BanReady API error ${response.status}: ${errorText}`
    );
  }

  const data =
    (await response.json()) as ParkingCheckResponse;

  return data;
}

export type ParkingOption = {
  parking_id: string;

  name: string;

  destination_type: string;

  latitude: number;
  longitude: number;

  address: string | null;

  distance_meters: number;
  distance_km: number;

  verification_status: string;

  ban_available: boolean | null;

  availability_status: string;

  total_capacity: number | null;
  ban_capacity: number | null;

  overnight_allowed: boolean | null;

  price_type: string | null;
  price_amount: number | null;

  source_name: string | null;
  source_url: string | null;

  notes: string | null;

  ban_availability_note?: string | null;
};


export type ParkingOptionsResponse = {
  origin_latitude: number;
  origin_longitude: number;

  candidate_count: number;
  returned_count: number;

  options: ParkingOption[];

  reason: string;
};


export type ParkingOptionsRequest = {
  latitude: number;
  longitude: number;

  limit?: number;

  max_distance_meters?: number;
};


export async function getParkingOptions(
  request: ParkingOptionsRequest
): Promise<ParkingOptionsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/parking/options`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        latitude: request.latitude,
        longitude: request.longitude,
        limit: request.limit ?? 5,

        max_distance_meters:
          request.max_distance_meters,
      }),
    }
  );

  if (!response.ok) {
    const errorText =
      await response.text();

    throw new Error(
      `BanReady parking-options API error ${response.status}: ${errorText}`
    );
  }

  const data =
    (await response.json()) as ParkingOptionsResponse;

  return data;
}