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
  getModeledParkingZone,
  type ModeledStreetItem,
  type ModeledZoneResponse,
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


function getChanceColor(
  chance: number
): string {
  if (chance >= 65) {
    return "#12B76A";
  }

  if (chance >= 35) {
    return "#F79009";
  }

  return "#D92D20";
}


function getChanceBackground(
  chance: number
): string {
  if (chance >= 65) {
    return "#ECFDF3";
  }

  if (chance >= 35) {
    return "#FFFAEB";
  }

  return "#FEF3F2";
}


function StreetCard({
  street,
  recommended,
}: {
  street: ModeledStreetItem;
  recommended: boolean;
}) {
  const chanceColor = getChanceColor(
    street.modeled_chance_percent
  );

  return (
    <View
      style={[
        styles.streetCard,
        recommended
          ? styles.recommendedStreetCard
          : null,
      ]}
    >
      <View style={styles.streetHeader}>
        <View style={styles.streetDetails}>
          <View style={styles.streetNameRow}>
            <Text style={styles.streetName}>
              {street.street_name}
            </Text>

            {recommended ? (
              <View
                style={
                  styles.recommendedBadge
                }
              >
                <Text
                  style={
                    styles.recommendedBadgeText
                  }
                >
                  BEST MODELED OPTION
                </Text>
              </View>
            ) : null}
          </View>

          <Text style={styles.streetSide}>
            {street.legal_side} SIDE
          </Text>
        </View>

        <Text
          style={[
            styles.streetChance,
            {
              color: chanceColor,
            },
          ]}
        >
          {street.modeled_chance_percent}%
        </Text>
      </View>

      <View style={styles.streetMetaRow}>
        <Text style={styles.streetMeta}>
          Approx. {street.approximate_minutes}
          {" "}
          {street.approximate_minutes === 1
            ? "min"
            : "mins"}
          {" "}
          by distance
        </Text>

        <Text style={styles.metaDivider}>
          •
        </Text>

        <Text style={styles.streetMeta}>
          {street.prototype_requests}
          {" "}
          prototype requests
        </Text>
      </View>

      <View style={styles.progressTrack}>
        <View
          style={[
            styles.progressFill,
            {
              width:
                `${street.modeled_chance_percent}%`,
              backgroundColor:
                chanceColor,
            },
          ]}
        />
      </View>

      <View style={styles.streetMetrics}>
        <Text style={styles.streetMetricText}>
          {street.legal_spaces}
          {" "}
          modeled spaces
        </Text>

        <Text style={styles.streetMetricText}>
          ~{street.expected_vehicles}
          {" "}
          vehicles
        </Text>

        <Text style={styles.distanceText}>
          {Math.round(
            street.distance_meters
          )}
          {" "}
          m away
        </Text>
      </View>
    </View>
  );
}


export default function ParkingZoneScreen() {
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
    useState<ModeledZoneResponse | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  useEffect(() => {
    let isActive = true;

    async function loadZone() {
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
          await getModeledParkingZone({
            latitude,
            longitude,
            origin_segment_id:
              segmentId,
            radius_meters: 500,
            limit: 4,
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
              "Unable to load the modeled "
              + "parking zone."
            );

        setError(message);
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    loadZone();

    return () => {
      isActive = false;
    };
  }, [
    latitude,
    longitude,
    segmentId,
  ]);


  function openWalkingZones() {
    if (
      latitude === null
      || longitude === null
    ) {
      setError(
        "Location coordinates are unavailable."
      );

      return;
    }

    router.push({
      pathname: "/walking-zones",

      params: {
        latitude:
          latitude.toString(),

        longitude:
          longitude.toString(),

        streetName,

        segmentId:
          segmentId?.toString()
          ?? "",
      },
    });
  }


  if (loading) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator
          size="large"
          color="#2070C0"
        />

        <Text style={styles.loadingText}>
          Analyzing nearby streets...
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
          Zone analytics unavailable
        </Text>

        <Text style={styles.errorText}>
          {error || (
            "BanReady could not load "
            + "nearby modeled streets."
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


  const zoneColor = getChanceColor(
    result.modeled_zone_chance_percent
  );

  const zoneBackground =
    getChanceBackground(
      result.modeled_zone_chance_percent
    );


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
          Modeled Parking Zone
        </Text>

        <Text style={styles.description}>
          Nearby analyzed streets within
          approximately 500 meters of{" "}
          {streetName}.
        </Text>


        <View
          style={[
            styles.summaryCard,
            {
              backgroundColor:
                zoneBackground,
            },
          ]}
        >
          <Text
            style={[
              styles.summaryPercent,
              {
                color: zoneColor,
              },
            ]}
          >
            {
              result
                .modeled_zone_chance_percent
            }%
          </Text>

          <Text style={styles.summaryTitle}>
            Modeled chance across nearby
            analyzed streets
          </Text>

          <View style={styles.summaryMetaRow}>
            <View style={styles.summaryMetric}>
              <Text
                style={
                  styles.summaryMetricValue
                }
              >
                {
                  result
                    .analyzed_street_count
                }
              </Text>

              <Text
                style={
                  styles.summaryMetricLabel
                }
              >
                analyzed streets
              </Text>
            </View>

            <View style={styles.summaryDivider} />

            <View style={styles.summaryMetric}>
              <Text
                style={
                  styles.summaryMetricValue
                }
              >
                {
                  result
                    .prototype_requests
                }
              </Text>

              <Text
                style={
                  styles.summaryMetricLabel
                }
              >
                prototype requests
              </Text>
            </View>
          </View>
        </View>


        <Text style={styles.sectionTitle}>
          Nearby modeled streets
        </Text>

        {result.streets.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>
              No analyzed streets found
            </Text>

            <Text style={styles.emptyText}>
              BanReady did not find a usable
              modeled street within the
              selected radius.
            </Text>
          </View>
        ) : (
          result.streets.map((street) => (
            <StreetCard
              key={
                street.segment_id
                ?? street.street_name
              }
              street={street}
              recommended={
                street.segment_id
                ===
                result
                  .recommended_segment_id
              }
            />
          ))
        )}


        {result.recommended_street ? (
          <View style={styles.bestOptionCard}>
            <Text style={styles.bestOptionEyebrow}>
              BEST MODELED OPTION
            </Text>

            <Text style={styles.bestOptionName}>
              {
                result
                  .recommended_street
                  .street_name
              }
            </Text>

            <Text style={styles.bestOptionDetails}>
              {
                result
                  .recommended_street
                  .legal_side
              }
              {" "}
              side
              {" • "}
              {
                result
                  .recommended_street
                  .modeled_chance_percent
              }
              % modeled chance
              {" • "}
              {
                Math.round(
                  result
                    .recommended_street
                    .distance_meters
                )
              }
              {" "}
              m away
            </Text>
          </View>
        ) : null}


        <View style={styles.noticeCard}>
          <Text style={styles.noticeTitle}>
            Prototype estimate
          </Text>

          <Text style={styles.noticeText}>
            Real Worcester street names and
            restriction sides are combined with
            modeled supply and demand estimates.
            This is not live parking availability
            or a calculated walking route.
          </Text>
        </View>


        <Pressable
          style={({ pressed }) => [
            styles.primaryButton,
            pressed
              ? styles.buttonPressed
              : null,
          ]}
          onPress={openWalkingZones}
        >
          <Text style={styles.primaryButtonText}>
            Explore Approximate Parking Zones
          </Text>
        </Pressable>


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
    fontSize: 30,
    fontWeight: "900",
    lineHeight: 36,
    marginTop: 6,
  },

  description: {
    color: "#667085",
    fontSize: 15,
    lineHeight: 22,
    marginTop: 7,
    marginBottom: 17,
  },

  summaryCard: {
    borderRadius: 24,
    padding: 23,
    alignItems: "center",
  },

  summaryPercent: {
    fontSize: 48,
    fontWeight: "900",
  },

  summaryTitle: {
    color: "#10243F",
    fontSize: 19,
    lineHeight: 25,
    fontWeight: "900",
    textAlign: "center",
    marginTop: 5,
    maxWidth: 300,
  },

  summaryMetaRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 19,
  },

  summaryMetric: {
    flex: 1,
    alignItems: "center",
  },

  summaryMetricValue: {
    color: "#10243F",
    fontSize: 24,
    fontWeight: "900",
  },

  summaryMetricLabel: {
    color: "#667085",
    fontSize: 12,
    textAlign: "center",
    marginTop: 3,
  },

  summaryDivider: {
    width: 1,
    height: 42,
    backgroundColor: "#D0D5DD",
  },

  sectionTitle: {
    color: "#10243F",
    fontSize: 20,
    fontWeight: "900",
    marginTop: 21,
    marginBottom: 11,
  },

  streetCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 19,
    padding: 17,
    borderWidth: 1,
    borderColor: "#E4E7EC",
    marginBottom: 11,
  },

  recommendedStreetCard: {
    borderColor: "#84ADFF",
    borderWidth: 2,
  },

  streetHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
  },

  streetDetails: {
    flex: 1,
    paddingRight: 10,
  },

  streetNameRow: {
    flexDirection: "row",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 7,
  },

  streetName: {
    color: "#10243F",
    fontSize: 17,
    fontWeight: "900",
  },

  recommendedBadge: {
    backgroundColor: "#EFF8FF",
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },

  recommendedBadgeText: {
    color: "#175CD3",
    fontSize: 8,
    fontWeight: "900",
    letterSpacing: 0.35,
  },

  streetSide: {
    color: "#175CD3",
    fontSize: 12,
    fontWeight: "900",
    marginTop: 5,
  },

  streetChance: {
    fontSize: 23,
    fontWeight: "900",
  },

  streetMetaRow: {
    flexDirection: "row",
    alignItems: "center",
    flexWrap: "wrap",
    marginTop: 10,
  },

  streetMeta: {
    color: "#667085",
    fontSize: 12,
  },

  metaDivider: {
    color: "#98A2B3",
    fontSize: 12,
    marginHorizontal: 7,
  },

  progressTrack: {
    height: 8,
    backgroundColor: "#EAECF0",
    borderRadius: 4,
    overflow: "hidden",
    marginTop: 13,
  },

  progressFill: {
    height: 8,
    borderRadius: 4,
  },

  streetMetrics: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
    marginTop: 10,
  },

  streetMetricText: {
    color: "#475467",
    fontSize: 11,
    fontWeight: "700",
  },

  distanceText: {
    color: "#667085",
    fontSize: 11,
  },

  bestOptionCard: {
    backgroundColor: "#EFF8FF",
    borderColor: "#B2DDFF",
    borderWidth: 1,
    borderRadius: 19,
    padding: 18,
    marginTop: 3,
  },

  bestOptionEyebrow: {
    color: "#175CD3",
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 0.8,
  },

  bestOptionName: {
    color: "#10243F",
    fontSize: 20,
    fontWeight: "900",
    marginTop: 6,
  },

  bestOptionDetails: {
    color: "#475467",
    fontSize: 13,
    lineHeight: 20,
    marginTop: 5,
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

  emptyCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 18,
    borderWidth: 1,
    borderColor: "#E4E7EC",
    padding: 18,
  },

  emptyTitle: {
    color: "#10243F",
    fontSize: 17,
    fontWeight: "900",
  },

  emptyText: {
    color: "#667085",
    fontSize: 13,
    lineHeight: 20,
    marginTop: 5,
  },

  primaryButton: {
    backgroundColor: "#2070C0",
    borderRadius: 15,
    paddingVertical: 17,
    paddingHorizontal: 18,
    alignItems: "center",
    marginTop: 16,
  },

  primaryButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "900",
    textAlign: "center",
  },

  buttonPressed: {
    opacity: 0.82,
  },

  secondaryButton: {
    backgroundColor: "#FFFFFF",
    borderColor: "#D0D5DD",
    borderWidth: 1,
    borderRadius: 15,
    paddingVertical: 15,
    paddingHorizontal: 18,
    alignItems: "center",
    marginTop: 11,
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