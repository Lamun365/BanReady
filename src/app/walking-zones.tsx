import {
  router,
  useLocalSearchParams,
} from "expo-router";

import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import {
  SafeAreaView,
} from "react-native-safe-area-context";

import {
  useEffect,
  useState,
} from "react";

import {
  getModeledWalkingZones,
  type HistoricalParkingFacility,
  type ModeledWalkingZone,
  type ModeledWalkingZonesResponse,
} from "@/services/banreadyApi";


function getSingleParam(
  value: string | string[] | undefined,
  fallback = ""
): string {
  if (Array.isArray(value)) {
    return value[0] ?? fallback;
  }

  return value ?? fallback;
}


function parseOptionalNumber(
  value: string
): number | null {
  if (value.trim() === "") {
    return null;
  }

  const parsedValue = Number(value);

  return Number.isFinite(parsedValue)
    ? parsedValue
    : null;
}


function formatDistance(
  distanceMeters: number
): string {
  if (distanceMeters < 1000) {
    return (
      `${Math.round(distanceMeters)} m`
    );
  }

  return (
    `${(distanceMeters / 1000).toFixed(2)} km`
  );
}


function formatMinutes(
  minutes: number
): string {
  if (minutes === 0) {
    return "At this location";
  }

  if (minutes === 1) {
    return "Approx. 1 min by distance";
  }

  return (
    `Approx. ${minutes} mins by distance`
  );
}


function GarageRow({
  garage,
}: {
  garage: HistoricalParkingFacility;
}) {
  return (
    <View style={styles.garageRow}>
      <View style={styles.parkingIcon}>
        <Text style={styles.parkingIconText}>
          P
        </Text>
      </View>

      <View style={styles.garageDetails}>
        <Text style={styles.garageName}>
          {garage.name}
        </Text>

        <Text style={styles.garageMeta}>
          {formatDistance(
            garage.distance_meters
          )}
          {" • "}
          {formatMinutes(
            garage.approximate_minutes
          )}
        </Text>

        <Text style={styles.availabilityText}>
          Live availability:{" "}
          {garage.availability_status}
        </Text>
      </View>
    </View>
  );
}


function ZoneCard({
  zone,
  accentColor,
  backgroundColor,
}: {
  zone: ModeledWalkingZone;
  accentColor: string;
  backgroundColor: string;
}) {
  return (
    <View
      style={[
        styles.zoneCard,
        {
          borderColor:
            accentColor,
          backgroundColor,
        },
      ]}
    >
      <View style={styles.zoneHeader}>
        <View>
          <Text
            style={[
              styles.zoneMinutes,
              {
                color:
                  accentColor,
              },
            ]}
          >
            Within approx.{" "}
            {zone.approximate_minutes}
            {" "}
            minutes
          </Text>

          <Text style={styles.zoneRadius}>
            {zone.radius_meters} m
            straight-line radius
          </Text>
        </View>

        <View
          style={[
            styles.radiusBadge,
            {
              backgroundColor:
                accentColor,
            },
          ]}
        >
          <Text style={styles.radiusBadgeText}>
            {zone.radius_meters} m
          </Text>
        </View>
      </View>

      <View style={styles.zoneMetrics}>
        <View style={styles.zoneMetric}>
          <Text style={styles.zoneMetricValue}>
            {
              zone
                .unique_legal_street_count
            }
          </Text>

          <Text style={styles.zoneMetricLabel}>
            unique modeled
            legal streets
          </Text>
        </View>

        <View style={styles.zoneMetricDivider} />

        <View style={styles.zoneMetric}>
          <Text style={styles.zoneMetricValue}>
            {
              zone
                .historical_garage_count
            }
          </Text>

          <Text style={styles.zoneMetricLabel}>
            historical parking
            facilities
          </Text>
        </View>
      </View>

      {zone.garages.length > 0 ? (
        <View style={styles.zoneGarageList}>
          <Text style={styles.zoneGarageTitle}>
            Facilities in this zone
          </Text>

          {zone.garages.map((garage) => (
            <GarageRow
              key={
                garage.parking_id
                ?? `${garage.name}-${garage.distance_meters}`
              }
              garage={garage}
            />
          ))}
        </View>
      ) : (
        <View style={styles.noGarageCard}>
          <Text style={styles.noGarageText}>
            No historical parking facility
            appears within this radius.
          </Text>
        </View>
      )}
    </View>
  );
}


export default function WalkingZonesScreen() {
  const params = useLocalSearchParams();

  const latitudeText = getSingleParam(
    params.latitude
  );

  const longitudeText = getSingleParam(
    params.longitude
  );

  const streetName = getSingleParam(
    params.streetName,
    "CURRENT LOCATION"
  );

  const segmentIdText = getSingleParam(
    params.segmentId
  );

  const latitude = parseOptionalNumber(
    latitudeText
  );

  const longitude = parseOptionalNumber(
    longitudeText
  );

  const segmentId = parseOptionalNumber(
    segmentIdText
  );

  const [result, setResult] =
    useState<
      ModeledWalkingZonesResponse | null
    >(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  useEffect(() => {
    let isActive = true;

    async function loadWalkingZones() {
      if (
        latitude === null
        || longitude === null
      ) {
        setError(
          "Location coordinates are unavailable."
        );

        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError("");

        const response =
          await getModeledWalkingZones({
            latitude,
            longitude,

            origin_segment_id:
              segmentId,

            radii_meters: [
              400,
              800,
            ],
          });

        if (isActive) {
          setResult(response);
        }
      } catch (loadError) {
        if (!isActive) {
          return;
        }

        const message =
          loadError instanceof Error
            ? loadError.message
            : (
              "Unable to load approximate "
              + "parking zones."
            );

        setError(message);
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    loadWalkingZones();

    return () => {
      isActive = false;
    };
  }, [
    latitude,
    longitude,
    segmentId,
  ]);


  if (loading) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator
          size="large"
          color="#2070C0"
        />

        <Text style={styles.loadingText}>
          Building approximate parking zones...
        </Text>
      </SafeAreaView>
    );
  }


  if (error || !result) {
    return (
      <SafeAreaView style={styles.center}>
        <View style={styles.errorIcon}>
          <Text style={styles.errorIconText}>
            !
          </Text>
        </View>

        <Text style={styles.errorTitle}>
          Parking zones unavailable
        </Text>

        <Text style={styles.errorText}>
          {error || (
            "BanReady could not load the "
            + "approximate parking zones."
          )}
        </Text>

        <Pressable
          style={styles.secondaryButton}
          onPress={() => router.back()}
        >
          <Text style={styles.secondaryButtonText}>
            Go Back
          </Text>
        </Pressable>
      </SafeAreaView>
    );
  }


  const nearestGarage =
    result.nearest_historical_garage;

  const firstZone =
    result.zones[0] ?? null;

  const secondZone =
    result.zones[1] ?? null;


  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
      >
        <Pressable
          onPress={() => router.back()}
          hitSlop={12}
        >
          <Text style={styles.backText}>
            ‹ Back
          </Text>
        </Pressable>


        <Text style={styles.eyebrow}>
          PROTOTYPE PARKING ANALYTICS
        </Text>

        <Text style={styles.title}>
          Parking Within Walking Distance
        </Text>

        <Text style={styles.description}>
          Approximate parking zones centered
          on {streetName}.
        </Text>


        <View style={styles.zoneVisualCard}>
          <View style={styles.outerCircle}>
            <Text style={styles.outerCircleLabel}>
              800 m
            </Text>

            <View style={styles.innerCircle}>
              <Text style={styles.innerCircleLabel}>
                400 m
              </Text>

              <View style={styles.originMarker}>
                <View style={styles.originMarkerCenter} />
              </View>
            </View>
          </View>

          <Text style={styles.originLabel}>
            Current checked location
          </Text>

          <View style={styles.legendRow}>
            <View style={styles.legendItem}>
              <View
                style={
                  styles.originLegendMarker
                }
              />

              <Text style={styles.legendText}>
                Origin
              </Text>
            </View>

            <View style={styles.legendItem}>
              <View
                style={
                  styles.innerLegendMarker
                }
              />

              <Text style={styles.legendText}>
                Approx. 5 min
              </Text>
            </View>

            <View style={styles.legendItem}>
              <View
                style={
                  styles.outerLegendMarker
                }
              />

              <Text style={styles.legendText}>
                Approx. 10 min
              </Text>
            </View>
          </View>
        </View>


        {firstZone ? (
          <ZoneCard
            zone={firstZone}
            accentColor="#1570EF"
            backgroundColor="#EFF8FF"
          />
        ) : null}


        {secondZone ? (
          <ZoneCard
            zone={secondZone}
            accentColor="#7F56D9"
            backgroundColor="#F9F5FF"
          />
        ) : null}


        {nearestGarage ? (
          <View style={styles.nearestCard}>
            <Text style={styles.nearestEyebrow}>
              NEAREST HISTORICAL FACILITY
            </Text>

            <View style={styles.nearestHeader}>
              <View style={styles.largeParkingIcon}>
                <Text
                  style={
                    styles.largeParkingIconText
                  }
                >
                  P
                </Text>
              </View>

              <View style={styles.nearestDetails}>
                <Text style={styles.nearestName}>
                  {nearestGarage.name}
                </Text>

                <Text style={styles.nearestDistance}>
                  {formatDistance(
                    nearestGarage
                      .distance_meters
                  )}
                  {" straight-line distance"}
                </Text>

                <Text style={styles.nearestTime}>
                  {formatMinutes(
                    nearestGarage
                      .approximate_minutes
                  )}
                </Text>
              </View>
            </View>

            <View style={styles.availabilityBadge}>
              <Text
                style={
                  styles.availabilityBadgeText
                }
              >
                Live availability:{" "}
                {
                  nearestGarage
                    .availability_status
                }
              </Text>
            </View>
          </View>
        ) : (
          <View style={styles.nearestCard}>
            <Text style={styles.nearestEyebrow}>
              HISTORICAL FACILITIES
            </Text>

            <Text style={styles.nearestName}>
              No facility data available
            </Text>
          </View>
        )}


        <View style={styles.noticeCard}>
          <Text style={styles.noticeTitle}>
            Approximate zones
          </Text>

          <Text style={styles.noticeText}>
            These zones use straight-line
            distance, not calculated pedestrian
            routes. Street demand and parking
            chance values are prototype estimates.
            Live availability is not provided.
          </Text>
        </View>


        <Pressable
          style={styles.secondaryButton}
          onPress={() =>
            router.replace("/location")
          }
        >
          <Text style={styles.secondaryButtonText}>
            Check Another Location
          </Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}


const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F5F7FA",
  },

  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    backgroundColor: "#F5F7FA",
  },

  container: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 44,
  },

  backText: {
    color: "#2070C0",
    fontSize: 17,
    fontWeight: "800",
    marginBottom: 20,
  },

  eyebrow: {
    color: "#2070C0",
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 1.15,
  },

  title: {
    color: "#10243F",
    fontSize: 29,
    fontWeight: "900",
    lineHeight: 35,
    marginTop: 6,
  },

  description: {
    color: "#667085",
    fontSize: 15,
    lineHeight: 22,
    marginTop: 7,
    marginBottom: 17,
  },

  zoneVisualCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 24,
    paddingVertical: 24,
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: "#E4E7EC",
    alignItems: "center",
  },

  outerCircle: {
    width: 242,
    height: 242,
    borderRadius: 121,
    borderWidth: 3,
    borderColor: "#7F56D9",
    borderStyle: "dashed",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F9F5FF",
  },

  outerCircleLabel: {
    position: "absolute",
    top: 17,
    color: "#6941C6",
    fontSize: 13,
    fontWeight: "900",
  },

  innerCircle: {
    width: 142,
    height: 142,
    borderRadius: 71,
    borderWidth: 3,
    borderColor: "#1570EF",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#EFF8FF",
  },

  innerCircleLabel: {
    position: "absolute",
    bottom: 13,
    color: "#175CD3",
    fontSize: 13,
    fontWeight: "900",
  },

  originMarker: {
    width: 31,
    height: 31,
    borderRadius: 16,
    backgroundColor: "#FEF3F2",
    borderColor: "#D92D20",
    borderWidth: 3,
    alignItems: "center",
    justifyContent: "center",
  },

  originMarkerCenter: {
    width: 9,
    height: 9,
    borderRadius: 5,
    backgroundColor: "#D92D20",
  },

  originLabel: {
    color: "#344054",
    fontSize: 13,
    fontWeight: "800",
    marginTop: 15,
  },

  legendRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    flexWrap: "wrap",
    gap: 15,
    marginTop: 15,
  },

  legendItem: {
    flexDirection: "row",
    alignItems: "center",
  },

  legendText: {
    color: "#667085",
    fontSize: 11,
    marginLeft: 5,
  },

  originLegendMarker: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#D92D20",
  },

  innerLegendMarker: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#1570EF",
  },

  outerLegendMarker: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#7F56D9",
  },

  zoneCard: {
    borderRadius: 21,
    borderWidth: 1,
    padding: 18,
    marginTop: 14,
  },

  zoneHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
  },

  zoneMinutes: {
    fontSize: 18,
    fontWeight: "900",
  },

  zoneRadius: {
    color: "#667085",
    fontSize: 12,
    marginTop: 4,
  },

  radiusBadge: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginLeft: 10,
  },

  radiusBadgeText: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "900",
  },

  zoneMetrics: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 19,
  },

  zoneMetric: {
    flex: 1,
    alignItems: "center",
  },

  zoneMetricValue: {
    color: "#10243F",
    fontSize: 28,
    fontWeight: "900",
  },

  zoneMetricLabel: {
    color: "#667085",
    fontSize: 11,
    lineHeight: 16,
    textAlign: "center",
    marginTop: 4,
    maxWidth: 120,
  },

  zoneMetricDivider: {
    width: 1,
    height: 52,
    backgroundColor: "#D0D5DD",
  },

  zoneGarageList: {
    borderTopWidth: 1,
    borderTopColor: "#D0D5DD",
    marginTop: 18,
    paddingTop: 15,
  },

  zoneGarageTitle: {
    color: "#10243F",
    fontSize: 14,
    fontWeight: "900",
    marginBottom: 4,
  },

  garageRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginTop: 12,
  },

  parkingIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: "#2070C0",
    alignItems: "center",
    justifyContent: "center",
  },

  parkingIconText: {
    color: "#FFFFFF",
    fontSize: 17,
    fontWeight: "900",
  },

  garageDetails: {
    flex: 1,
    marginLeft: 11,
  },

  garageName: {
    color: "#10243F",
    fontSize: 14,
    fontWeight: "900",
  },

  garageMeta: {
    color: "#667085",
    fontSize: 12,
    lineHeight: 18,
    marginTop: 3,
  },

  availabilityText: {
    color: "#B54708",
    fontSize: 11,
    fontWeight: "800",
    marginTop: 3,
  },

  noGarageCard: {
    backgroundColor: "rgba(255,255,255,0.68)",
    borderRadius: 14,
    padding: 13,
    marginTop: 16,
  },

  noGarageText: {
    color: "#667085",
    fontSize: 12,
    lineHeight: 18,
    textAlign: "center",
  },

  nearestCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 21,
    borderWidth: 1,
    borderColor: "#E4E7EC",
    padding: 18,
    marginTop: 14,
  },

  nearestEyebrow: {
    color: "#2070C0",
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 0.8,
  },

  nearestHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 12,
  },

  largeParkingIcon: {
    width: 52,
    height: 52,
    borderRadius: 15,
    backgroundColor: "#2070C0",
    alignItems: "center",
    justifyContent: "center",
  },

  largeParkingIconText: {
    color: "#FFFFFF",
    fontSize: 27,
    fontWeight: "900",
  },

  nearestDetails: {
    flex: 1,
    marginLeft: 13,
  },

  nearestName: {
    color: "#10243F",
    fontSize: 19,
    fontWeight: "900",
  },

  nearestDistance: {
    color: "#475467",
    fontSize: 13,
    marginTop: 4,
  },

  nearestTime: {
    color: "#667085",
    fontSize: 12,
    marginTop: 3,
  },

  availabilityBadge: {
    alignSelf: "flex-start",
    backgroundColor: "#FFFAEB",
    borderRadius: 999,
    paddingHorizontal: 11,
    paddingVertical: 7,
    marginTop: 14,
  },

  availabilityBadgeText: {
    color: "#B54708",
    fontSize: 11,
    fontWeight: "900",
  },

  noticeCard: {
    backgroundColor: "#FFFAEB",
    borderColor: "#FEDF89",
    borderWidth: 1,
    borderRadius: 17,
    padding: 16,
    marginTop: 14,
  },

  noticeTitle: {
    color: "#93370D",
    fontSize: 14,
    fontWeight: "900",
  },

  noticeText: {
    color: "#B54708",
    fontSize: 13,
    lineHeight: 19,
    marginTop: 4,
  },

  secondaryButton: {
    backgroundColor: "#FFFFFF",
    borderColor: "#D0D5DD",
    borderWidth: 1,
    borderRadius: 15,
    paddingVertical: 15,
    paddingHorizontal: 18,
    alignItems: "center",
    marginTop: 14,
  },

  secondaryButtonText: {
    color: "#344054",
    fontSize: 15,
    fontWeight: "800",
  },

  loadingText: {
    color: "#667085",
    fontSize: 14,
    marginTop: 13,
    textAlign: "center",
  },

  errorIcon: {
    width: 55,
    height: 55,
    borderRadius: 28,
    backgroundColor: "#FEF3F2",
    alignItems: "center",
    justifyContent: "center",
  },

  errorIconText: {
    color: "#D92D20",
    fontSize: 28,
    fontWeight: "900",
  },

  errorTitle: {
    color: "#10243F",
    fontSize: 23,
    fontWeight: "900",
    marginTop: 16,
  },

  errorText: {
    color: "#667085",
    fontSize: 14,
    lineHeight: 21,
    textAlign: "center",
    marginTop: 7,
    maxWidth: 330,
  },
});