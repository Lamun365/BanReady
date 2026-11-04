const API_BASE_URL = "https://banready.onrender.com";
// const API_BASE_URL = "https://authority-employed-alumni-pacific.trycloudflare.com";


export type ParkingCheckRequest = {
  latitude: number;
  longitude: number;

  declared_ban_active: boolean;
  snow_emergency_active: boolean;
  permanent_time_restriction_active: boolean;

  check_time?: string;
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

// ============================================================
// Modeled parking analytics
// ============================================================

export type ModeledChanceLevel =
  | "LOW"
  | "MEDIUM"
  | "HIGH";

export type ModeledStreetItem = {
  segment_id: number | null;
  street_name: string;

  ban_type: string;
  restricted_side: string;
  legal_side: string;

  distance_meters: number;
  approximate_minutes: number;

  legal_spaces: number;
  expected_vehicles: number;
  prototype_requests: number;

  modeled_chance_percent: number;
  chance_level: ModeledChanceLevel;
  message: string;
};

// ============================================================
// Screen 4: Modeled street chance
// ============================================================

export type ModeledStreetRequest = {
  street_name: string;
  segment_id: number | null;

  parked_side: string;
  restricted_side: string;
  ban_type: string;
};

export type ModeledStreetResponse = {
  data_status: "SYNTHETIC_PROTOTYPE";

  street_name: string;
  segment_id: number | null;

  ban_type: string;
  parked_side: string;
  restricted_side: string;
  legal_side: string;

  legal_spaces: number;
  expected_vehicles: number;
  prototype_requests: number;

  modeled_chance_percent: number;
  chance_level: ModeledChanceLevel;
  message: string;

  disclosure: string;
};

export async function getModeledStreetChance(
  request: ModeledStreetRequest
): Promise<ModeledStreetResponse> {
  const response = await fetch(
    `${API_BASE_URL}/parking/modeled-street`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(request),
    }
  );

  if (!response.ok) {
    const errorText =
      await response.text();

    throw new Error(
      `Modeled street API error ${response.status}: ${errorText}`
    );
  }

  const data =
    (await response.json()) as ModeledStreetResponse;

  return data;
}

// ============================================================
// Screen 5: Modeled parking zone
// ============================================================

export type ModeledZoneRequest = {
  latitude: number;
  longitude: number;

  origin_segment_id?: number | null;

  radius_meters?: number;
  limit?: number;
};

export type ModeledZoneOrigin = {
  latitude: number;
  longitude: number;
  segment_id: number | null;
};

export type ModeledZoneResponse = {
  data_status: "SYNTHETIC_PROTOTYPE";

  origin: ModeledZoneOrigin;

  radius_meters: number;

  modeled_zone_chance_percent: number;
  analyzed_street_count: number;
  prototype_requests: number;

  recommended_segment_id: number | null;
  recommended_street: ModeledStreetItem | null;

  streets: ModeledStreetItem[];

  disclosure: string;
};

export async function getModeledParkingZone(
  request: ModeledZoneRequest
): Promise<ModeledZoneResponse> {
  const response = await fetch(
    `${API_BASE_URL}/parking/modeled-zone`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        latitude: request.latitude,
        longitude: request.longitude,

        origin_segment_id:
          request.origin_segment_id ?? null,

        radius_meters:
          request.radius_meters ?? 500,

        limit:
          request.limit ?? 4,
      }),
    }
  );

  if (!response.ok) {
    const errorText =
      await response.text();

    throw new Error(
      `Modeled zone API error ${response.status}: ${errorText}`
    );
  }

  const data =
    (await response.json()) as ModeledZoneResponse;

  return data;
}

// ============================================================
// Screen 6: Approximate parking zones
// ============================================================

export type ModeledWalkingZonesRequest = {
  latitude: number;
  longitude: number;

  origin_segment_id?: number | null;

  radii_meters?: number[];
};

export type HistoricalParkingFacility = {
  parking_id: string | null;
  name: string;

  latitude: number;
  longitude: number;

  distance_meters: number;
  distance_km: number;
  approximate_minutes: number;

  availability_status: string;
};

export type ModeledWalkingZone = {
  radius_meters: number;
  approximate_minutes: number;

  unique_legal_street_count: number;
  historical_garage_count: number;

  streets: ModeledStreetItem[];
  garages: HistoricalParkingFacility[];
};

export type ModeledWalkingZonesResponse = {
  zone_method: "STRAIGHT_LINE_RADIUS";

  origin: {
    latitude: number;
    longitude: number;
    segment_id: number | null;
  };

  walking_speed_meters_per_minute: number;

  zones: ModeledWalkingZone[];

  nearest_historical_garage:
    | HistoricalParkingFacility
    | null;

  disclosure: string;
};

export async function getModeledWalkingZones(
  request: ModeledWalkingZonesRequest
): Promise<ModeledWalkingZonesResponse> {
  const response = await fetch(
    `${API_BASE_URL}/parking/modeled-walking-zones`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        latitude: request.latitude,
        longitude: request.longitude,

        origin_segment_id:
          request.origin_segment_id ?? null,

        radii_meters:
          request.radii_meters ?? [
            400,
            800,
          ],
      }),
    }
  );

  if (!response.ok) {
    const errorText =
      await response.text();

    throw new Error(
      `Modeled walking-zones API error ${response.status}: ${errorText}`
    );
  }

  const data =
    (await response.json()) as ModeledWalkingZonesResponse;

  return data;
}

