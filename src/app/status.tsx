import { router, useLocalSearchParams } from "expo-router";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";


type ParkingStatus =
  | "MUST_MOVE"
  | "CAN_STAY_DURING_BAN"
  | "NOT_AFFECTED"
  | "VERIFY_RULE";


type StatusConfig = {
  symbol: string;
  title: string;
  subtitle: string;
  backgroundColor: string;
  borderColor: string;
  accentColor: string;
  badgeBackground: string;
};


const STATUS_CONFIG: Record<ParkingStatus, StatusConfig> = {
  MUST_MOVE: {
    symbol: "⚠️",
    title: "MUST MOVE",
    subtitle:
      "Your parking position is restricted by the current winter parking-ban rule.",
    backgroundColor: "#FFF7F6",
    borderColor: "#FECDCA",
    accentColor: "#B42318",
    badgeBackground: "#FEE4E2",
  },

  CAN_STAY_DURING_BAN: {
    symbol: "✓",
    title: "CAN STAY",
    subtitle:
      "Your side of the street is not prohibited by the modeled winter parking-ban rule.",
    backgroundColor: "#F0FDF4",
    borderColor: "#ABEFC6",
    accentColor: "#067647",
    badgeBackground: "#D1FADF",
  },

  NOT_AFFECTED: {
    symbol: "✓",
    title: "NOT AFFECTED",
    subtitle:
      "This location is not affected by the modeled Worcester winter parking-ban restriction.",
    backgroundColor: "#EFF8FF",
    borderColor: "#B2DDFF",
    accentColor: "#175CD3",
    badgeBackground: "#D1E9FF",
  },

  VERIFY_RULE: {
    symbol: "!",
    title: "VERIFY PARKING",
    subtitle:
      "BanReady could not verify this parking position with enough confidence.",
    backgroundColor: "#FFFAEB",
    borderColor: "#FEDF89",
    accentColor: "#B54708",
    badgeBackground: "#FEF0C7",
  },
};


function getSingleParam(
  value: string | string[] | undefined,
  fallback: string
) {
  if (Array.isArray(value)) {
    return value[0] ?? fallback;
  }

  return value ?? fallback;
}


function isParkingStatus(
  value: string
): value is ParkingStatus {
  return (
    value === "MUST_MOVE" ||
    value === "CAN_STAY_DURING_BAN" ||
    value === "NOT_AFFECTED" ||
    value === "VERIFY_RULE"
  );
}


export default function StatusScreen() {
  const params = useLocalSearchParams();

  const rawStatus = getSingleParam(
    params.status,
    "VERIFY_RULE"
  );

  const status: ParkingStatus =
    isParkingStatus(rawStatus)
      ? rawStatus
      : "VERIFY_RULE";

  const street = getSingleParam(
    params.street,
    "Unknown street"
  );

  const segmentId = getSingleParam(
  params.segmentId,
  ""
);

  const parkedSide = getSingleParam(
    params.parkedSide,
    "UNSURE"
  );

  const restrictedSide = getSingleParam(
    params.restrictedSide,
    "UNKNOWN"
  );

  const banType = getSingleParam(
    params.banType,
    "UNKNOWN"
  );

  // const banZone = getSingleParam(
  //   params.banZone,
  //   "UNKNOWN"
  // );

  const distance = getSingleParam(
    params.distance,
    "Unknown"
  );

  const reason = getSingleParam(
    params.reason,
    ""
  );

  const latitude = getSingleParam(
    params.latitude,
    ""
  );

  const longitude = getSingleParam(
    params.longitude,
    ""
  );

  const config = STATUS_CONFIG[status];

  const shouldShowSideDetails =
    parkedSide !== "UNSURE" ||
    restrictedSide !== "UNKNOWN";

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
      >
        {/* Back button */}

        <Pressable
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Text style={styles.backText}>
            ‹ Back
          </Text>
        </Pressable>


        {/* BanReady heading */}

        <View style={styles.brandRow}>
          <Text style={styles.brandIcon}>
            ❄️
          </Text>

          <Text style={styles.brand}>
            BanReady
          </Text>
        </View>


        {/* Main status card */}

        <View
          style={[
            styles.statusCard,
            {
              backgroundColor:
                config.backgroundColor,

              borderColor:
                config.borderColor,
            },
          ]}
        >
          <View
            style={[
              styles.statusIconCircle,
              {
                backgroundColor:
                  config.badgeBackground,
              },
            ]}
          >
            <Text
              style={[
                styles.statusIcon,
                {
                  color:
                    config.accentColor,
                },
              ]}
            >
              {config.symbol}
            </Text>
          </View>

          <Text
            style={[
              styles.statusTitle,
              {
                color:
                  config.accentColor,
              },
            ]}
          >
            {config.title}
          </Text>

          <Text style={styles.statusSubtitle}>
            {config.subtitle}
          </Text>
        </View>


        {/* Street */}

        <View style={styles.card}>
          <Text style={styles.sectionLabel}>
            STREET
          </Text>

          <Text style={styles.streetName}>
            {street}
          </Text>

          {distance !== "Unknown" && (
            <Text style={styles.distanceText}>
              Approximately {distance} m from mapped street centerline
            </Text>
          )}
        </View>


        {/* Parking-rule details */}

        <View style={styles.card}>
          <Text style={styles.cardTitle}>
            Parking rule
          </Text>

          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>
              Ban type
            </Text>

            <Text style={styles.detailValue}>
              {banType}
            </Text>
          </View>

          {/* <View style={styles.divider} />

          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>
              Ban zone
            </Text>

            <Text style={styles.detailValue}>
              {banZone}
            </Text>
          </View> */}

          {shouldShowSideDetails && (
            <>
              <View style={styles.divider} />

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>
                  Your parked side
                </Text>

                <Text style={styles.detailValue}>
                  {parkedSide}
                </Text>
              </View>

              <View style={styles.divider} />

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>
                  Restricted side
                </Text>

                <Text style={styles.detailValue}>
                  {restrictedSide}
                </Text>
              </View>
            </>
          )}
        </View>


        {/* Reason */}

        {reason !== "" && (
          <View style={styles.reasonCard}>
            <Text style={styles.reasonTitle}>
              Why?
            </Text>

            <Text style={styles.reasonText}>
              {reason}
            </Text>
          </View>
        )}

        {/* must move */}
        {status === "MUST_MOVE" && (
          <Pressable
            style={styles.dangerButton}
            onPress={() => {
              router.push({
                pathname: "/parking",

                params: {
                  street,
                  segmentId,
                  latitude,
                  longitude,
                  parkedSide,
                  restrictedSide,
                  banType,
                },
              });
            }}
          >
            <Text style={styles.dangerButtonText}>
              Find Parking
            </Text>
          </Pressable>
        )}


        {/* Verify-rule notice */}

        {status === "VERIFY_RULE" && (
          <View style={styles.warningCard}>
            <Text style={styles.warningTitle}>
              Check before leaving your car
            </Text>

            <Text style={styles.warningText}>
              BanReady does not have enough information
              to confidently determine this parking
              position. Verify the restriction with
              Worcester's official parking information.
            </Text>
          </View>
        )}


        {/* Check another location */}

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


        {/* Disclaimer */}

        <Text style={styles.footer}>
          BanReady currently evaluates modeled winter
          parking-ban restrictions. Other posted,
          temporary, or general parking rules may still apply.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}


const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F5F7FA",
  },

  container: {
    padding: 24,
    paddingBottom: 50,
  },

  backButton: {
    alignSelf: "flex-start",
    marginBottom: 20,
  },

  backText: {
    color: "#1769E0",
    fontSize: 17,
    fontWeight: "600",
  },

  brandRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 22,
  },

  brandIcon: {
    fontSize: 26,
    marginRight: 9,
  },

  brand: {
    color: "#12223B",
    fontSize: 22,
    fontWeight: "800",
  },

  statusCard: {
    borderWidth: 1,
    borderRadius: 26,
    padding: 26,
    alignItems: "center",
    marginBottom: 18,
  },

  statusIconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 18,
  },

  statusIcon: {
    fontSize: 30,
    fontWeight: "800",
  },

  statusTitle: {
    fontSize: 30,
    fontWeight: "900",
    textAlign: "center",
  },

  statusSubtitle: {
    color: "#475467",
    fontSize: 16,
    lineHeight: 23,
    textAlign: "center",
    marginTop: 10,
  },

  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 20,
    marginBottom: 14,
  },

  sectionLabel: {
    fontSize: 12,
    fontWeight: "800",
    color: "#667085",
    letterSpacing: 1,
  },

  streetName: {
    color: "#12223B",
    fontSize: 25,
    fontWeight: "800",
    marginTop: 7,
  },

  distanceText: {
    color: "#667085",
    fontSize: 13,
    lineHeight: 19,
    marginTop: 7,
  },

  cardTitle: {
    color: "#12223B",
    fontSize: 19,
    fontWeight: "800",
    marginBottom: 15,
  },

  detailRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 20,
  },

  detailLabel: {
    flex: 1,
    color: "#667085",
    fontSize: 14,
  },

  detailValue: {
    flex: 1,
    color: "#12223B",
    fontSize: 14,
    fontWeight: "700",
    textAlign: "right",
  },

  divider: {
    height: 1,
    backgroundColor: "#EAECF0",
    marginVertical: 13,
  },

  reasonCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 20,
    marginBottom: 14,
  },

  reasonTitle: {
    color: "#12223B",
    fontSize: 17,
    fontWeight: "800",
    marginBottom: 7,
  },

  reasonText: {
    color: "#667085",
    fontSize: 14,
    lineHeight: 21,
  },

  dangerButton: {
    backgroundColor: "#D92D20",
    borderRadius: 14,
    paddingVertical: 17,
    alignItems: "center",
    marginTop: 4,
  },

  dangerButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "800",
  },

  warningCard: {
    backgroundColor: "#FFFAEB",
    borderColor: "#FEDF89",
    borderWidth: 1,
    borderRadius: 18,
    padding: 18,
    marginTop: 4,
  },

  warningTitle: {
    color: "#93370D",
    fontSize: 15,
    fontWeight: "800",
  },

  warningText: {
    color: "#B54708",
    fontSize: 14,
    lineHeight: 21,
    marginTop: 7,
  },

  secondaryButton: {
    backgroundColor: "#FFFFFF",
    borderColor: "#D0D5DD",
    borderWidth: 1,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 14,
  },

  secondaryButtonText: {
    color: "#344054",
    fontSize: 15,
    fontWeight: "700",
  },

  footer: {
    color: "#98A2B3",
    fontSize: 12,
    lineHeight: 18,
    textAlign: "center",
    marginTop: 18,
  },
});