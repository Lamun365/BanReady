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
  getModeledStreetChance,
  type ModeledStreetResponse,
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


export default function StreetChanceScreen() {
  const params = useLocalSearchParams();

  const streetName = getSingleParam(
    params.streetName,
    "UNKNOWN STREET"
  );

  const segmentIdText = getSingleParam(
    params.segmentId
  );

  const latitudeText = getSingleParam(
    params.latitude
  );

  const longitudeText = getSingleParam(
    params.longitude
  );

  const parkedSide = getSingleParam(
    params.parkedSide,
    "UNKNOWN"
  );

  const restrictedSide = getSingleParam(
    params.restrictedSide,
    "UNKNOWN"
  );

  const banType = getSingleParam(
    params.banType,
    "UNKNOWN"
  );

  const segmentId = parseOptionalNumber(
    segmentIdText
  );

  const latitude = parseOptionalNumber(
    latitudeText
  );

  const longitude = parseOptionalNumber(
    longitudeText
  );

  const [result, setResult] =
    useState<ModeledStreetResponse | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  useEffect(() => {
    let isActive = true;

    async function loadModeledChance() {
      try {
        setLoading(true);
        setError("");

        const response =
          await getModeledStreetChance({
            street_name: streetName,
            segment_id: segmentId,
            parked_side: parkedSide,
            restricted_side: restrictedSide,
            ban_type: banType,
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
              "Unable to load modeled "
              + "parking analytics."
            );

        setError(message);
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    loadModeledChance();

    return () => {
      isActive = false;
    };
  }, [
    streetName,
    segmentId,
    parkedSide,
    restrictedSide,
    banType,
  ]);


  function openParkingZone() {
    if (
      latitude === null
      || longitude === null
    ) {
      setError(
        "Location coordinates are unavailable "
        + "for the modeled parking zone."
      );

      return;
    }

    router.push({
      pathname: "/parking-zone",

      params: {
        latitude: latitude.toString(),
        longitude: longitude.toString(),

        streetName:
          result?.street_name
          ?? streetName,

        segmentId:
          result?.segment_id
          ?.toString()
          ?? "",

        legalSide:
          result?.legal_side
          ?? "VERIFY",
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
          Loading modeled parking chance...
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
          Analytics unavailable
        </Text>

        <Text style={styles.errorText}>
          {error || (
            "BanReady could not load the "
            + "modeled parking estimate."
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


  const chanceColor = getChanceColor(
    result.modeled_chance_percent
  );

  const chanceBackground =
    getChanceBackground(
      result.modeled_chance_percent
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
          Modeled Street Chance
        </Text>

        <Text style={styles.description}>
          A location-specific estimate for the
          matched Worcester street.
        </Text>


        <View style={styles.streetCard}>
          <Text style={styles.streetEyebrow}>
            MODELED LEGAL SIDE
          </Text>

          <Text style={styles.streetName}>
            {result.street_name}
          </Text>

          <View style={styles.sideRow}>
            <View style={styles.sideBadge}>
              <Text style={styles.sideBadgeText}>
                {result.legal_side} SIDE
              </Text>
            </View>

            <Text style={styles.banType}>
              {result.ban_type} ban
            </Text>
          </View>
        </View>


        <View
          style={[
            styles.chanceCard,
            {
              backgroundColor:
                chanceBackground,
            },
          ]}
        >
          <View
            style={[
              styles.chanceCircle,
              {
                borderColor:
                  chanceColor,
              },
            ]}
          >
            <Text
              style={[
                styles.chancePercent,
                {
                  color:
                    chanceColor,
                },
              ]}
            >
              {
                result
                  .modeled_chance_percent
              }%
            </Text>
          </View>

          <Text style={styles.chanceTitle}>
            Modeled parking chance
          </Text>

          <Text style={styles.chanceMessage}>
            {result.message}
          </Text>

          <View
            style={[
              styles.levelBadge,
              {
                backgroundColor:
                  chanceColor,
              },
            ]}
          >
            <Text style={styles.levelBadgeText}>
              {result.chance_level} CHANCE
            </Text>
          </View>
        </View>


        <View style={styles.metricsRow}>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>
              {result.legal_spaces}
            </Text>

            <Text style={styles.metricLabel}>
              modeled legal spaces
            </Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>
              ~{result.expected_vehicles}
            </Text>

            <Text style={styles.metricLabel}>
              vehicles expected
            </Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>
              {result.prototype_requests}
            </Text>

            <Text style={styles.metricLabel}>
              prototype requests
            </Text>
          </View>
        </View>


        <View style={styles.ruleCard}>
          <Text style={styles.ruleTitle}>
            Modeled street rule
          </Text>

          <View style={styles.ruleRow}>
            <Text style={styles.ruleLabel}>
              Parked side
            </Text>

            <Text style={styles.ruleValue}>
              {result.parked_side}
            </Text>
          </View>

          <View style={styles.divider} />

          <View style={styles.ruleRow}>
            <Text style={styles.ruleLabel}>
              Restricted side
            </Text>

            <Text style={styles.ruleValue}>
              {result.restricted_side}
            </Text>
          </View>

          <View style={styles.divider} />

          <View style={styles.ruleRow}>
            <Text style={styles.ruleLabel}>
              Modeled legal side
            </Text>

            <Text style={styles.legalRuleValue}>
              {result.legal_side}
            </Text>
          </View>
        </View>


        <View style={styles.noticeCard}>
          <Text style={styles.noticeTitle}>
            Prototype estimate
          </Text>

          <Text style={styles.noticeText}>
            Prototype estimates, not live
            parking availability.
          </Text>
        </View>


        <Pressable
          style={({ pressed }) => [
            styles.primaryButton,
            pressed
              ? styles.buttonPressed
              : null,
          ]}
          onPress={openParkingZone}
        >
          <Text style={styles.primaryButtonText}>
            See Modeled Parking Zone
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
    paddingBottom: 42,
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

  streetCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 19,
    borderWidth: 1,
    borderColor: "#E4E7EC",
  },

  streetEyebrow: {
    color: "#667085",
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 1,
  },

  streetName: {
    color: "#10243F",
    fontSize: 25,
    fontWeight: "900",
    marginTop: 7,
  },

  sideRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 11,
  },

  sideBadge: {
    backgroundColor: "#EFF8FF",
    borderColor: "#B2DDFF",
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },

  sideBadgeText: {
    color: "#175CD3",
    fontSize: 12,
    fontWeight: "900",
  },

  banType: {
    color: "#667085",
    fontSize: 13,
    fontWeight: "700",
    marginLeft: 10,
    textTransform: "capitalize",
  },

  chanceCard: {
    borderRadius: 24,
    padding: 23,
    alignItems: "center",
    marginTop: 14,
  },

  chanceCircle: {
    width: 132,
    height: 132,
    borderRadius: 66,
    borderWidth: 12,
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
  },

  chancePercent: {
    fontSize: 35,
    fontWeight: "900",
  },

  chanceTitle: {
    color: "#10243F",
    fontSize: 21,
    fontWeight: "900",
    marginTop: 18,
  },

  chanceMessage: {
    color: "#475467",
    fontSize: 14,
    lineHeight: 21,
    textAlign: "center",
    marginTop: 7,
    maxWidth: 310,
  },

  levelBadge: {
    borderRadius: 999,
    paddingHorizontal: 13,
    paddingVertical: 7,
    marginTop: 13,
  },

  levelBadgeText: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 0.6,
  },

  metricsRow: {
    flexDirection: "row",
    gap: 9,
    marginTop: 14,
  },

  metricCard: {
    flex: 1,
    minHeight: 108,
    backgroundColor: "#FFFFFF",
    borderRadius: 17,
    paddingHorizontal: 7,
    paddingVertical: 17,
    borderWidth: 1,
    borderColor: "#E4E7EC",
    alignItems: "center",
    justifyContent: "center",
  },

  metricValue: {
    color: "#10243F",
    fontSize: 25,
    fontWeight: "900",
  },

  metricLabel: {
    color: "#667085",
    fontSize: 11,
    lineHeight: 16,
    textAlign: "center",
    marginTop: 5,
  },

  ruleCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 18,
    marginTop: 14,
    borderWidth: 1,
    borderColor: "#E4E7EC",
  },

  ruleTitle: {
    color: "#10243F",
    fontSize: 17,
    fontWeight: "900",
    marginBottom: 12,
  },

  ruleRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 7,
  },

  ruleLabel: {
    color: "#667085",
    fontSize: 14,
    fontWeight: "600",
  },

  ruleValue: {
    color: "#344054",
    fontSize: 14,
    fontWeight: "900",
  },

  legalRuleValue: {
    color: "#067647",
    fontSize: 14,
    fontWeight: "900",
  },

  divider: {
    height: 1,
    backgroundColor: "#EAECF0",
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