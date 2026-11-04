
import {
    getParkingOptions,
    ParkingOption,
} from "@/services/banreadyApi";

import {
    useEffect,
    useState,
} from "react";

import {
    router,
    useLocalSearchParams,
} from "expo-router";

import {
    Pressable,
    ScrollView,
    StyleSheet,
    Text,
    View,
} from "react-native";

import { SafeAreaView } from "react-native-safe-area-context";


function getSingleParam(
  value: string | string[] | undefined,
  fallback: string
) {
  if (Array.isArray(value)) {
    return value[0] ?? fallback;
  }

  return value ?? fallback;
}


function prettyDestinationType(
  value: string
) {
  if (value === "MUNICIPAL_GARAGE") {
    return "Municipal garage";
  }

  if (value === "MUNICIPAL_LOT") {
    return "Municipal lot";
  }

  if (value === "PARTNER_LOT") {
    return "Partner lot";
  }

  if (value === "STREET") {
    return "Street parking";
  }

  return value;
}


function ParkingOptionCard({
  option,
  recommended,
}: {
  option: ParkingOption;
  recommended: boolean;
}) {
  return (
    <View
      style={[
        styles.optionCard,

        recommended &&
          styles.recommendedCard,
      ]}
    >
      {recommended && (
        <View style={styles.recommendedBadge}>
          <Text
            style={styles.recommendedBadgeText}
          >
            NEAREST VERIFIED OPTION
          </Text>
        </View>
      )}

      <View style={styles.optionHeader}>
        <View style={styles.parkingIcon}>
          <Text style={styles.parkingIconText}>
            P
          </Text>
        </View>

        <View style={styles.optionHeading}>
          <Text style={styles.optionName}>
            {option.name}
          </Text>

          <Text style={styles.optionAddress}>
            {option.address}
          </Text>
        </View>
      </View>

      <View style={styles.optionDivider} />

      <View style={styles.detailRow}>
        <Text style={styles.detailLabel}>
          Type
        </Text>

        <Text style={styles.detailValue}>
          {prettyDestinationType(
            option.destination_type
          )}
        </Text>
      </View>

      <View style={styles.detailRow}>
        <Text style={styles.detailLabel}>
          Straight-line distance
        </Text>

        <Text style={styles.distanceValue}>
          {option.distance_km.toFixed(2)} km
        </Text>
      </View>

      <View style={styles.detailRow}>
        <Text style={styles.detailLabel}>
          Verification
        </Text>

        <Text style={styles.verifiedValue}>
          Verified
        </Text>
      </View>

      <View style={styles.detailRow}>
        <Text style={styles.detailLabel}>
          Winter-ban evidence
        </Text>

        <Text style={styles.verifiedValue}>
          Confirmed
        </Text>
      </View>

      <View style={styles.detailRow}>
        <Text style={styles.detailLabel}>
          Live availability
        </Text>

        <Text style={styles.unknownValue}>
          Unknown
        </Text>
      </View>

      <View style={styles.optionDivider} />

      <View style={styles.capacityNotice}>
        <Text style={styles.capacityNoticeTitle}>
          Capacity not available yet
        </Text>

        <Text style={styles.capacityNoticeText}>
          BanReady has not yet verified live
          occupancy or available space at this
          facility.
        </Text>
      </View>

      {option.ban_availability_note ? (
        <View style={styles.banNotice}>
          <Text style={styles.banNoticeTitle}>
            Winter-ban note
          </Text>

          <Text style={styles.banNoticeText}>
            {option.ban_availability_note}
          </Text>
        </View>
      ) : null}
    </View>
  );
}


export default function ParkingScreen() {
    const params = useLocalSearchParams();

    const [options, setOptions] = useState<ParkingOption[]>([]);

    const [isLoading, setIsLoading] = useState(true);

    const [errorMessage, setErrorMessage] = useState("");


    const street = getSingleParam(
    params.street,
    "Your parked location"
    );

    const latitude = getSingleParam(
    params.latitude,
    ""
    );

    const longitude = getSingleParam(
    params.longitude,
    ""
    );

    const segmentId = getSingleParam(
      params.segmentId,
      ""
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


    const originLatitude = Number(latitude);

    const originLongitude = Number(longitude);

    useEffect(() => {
    async function loadOptions() {
        if (
        Number.isNaN(originLatitude) ||
        Number.isNaN(originLongitude)
        ) {
        setErrorMessage(
            "BanReady could not determine the parked-car location."
        );

        setIsLoading(false);

        return;
        }

        try {
        setIsLoading(true);
        setErrorMessage("");

        const result =
            await getParkingOptions({
            latitude:
                originLatitude,

            longitude:
                originLongitude,

            limit: 5,
            });

        setOptions(
            result.options
        );
        } catch (error) {
        if (error instanceof Error) {
            setErrorMessage(
            error.message
            );
        } else {
            setErrorMessage(
            "BanReady could not load parking options."
            );
        }
        } finally {
        setIsLoading(false);
        }
    }

    loadOptions();
    }, [
    originLatitude,
    originLongitude,
    ]);



  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
      >
        {/* Back */}

        <Pressable
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Text style={styles.backText}>
            ‹ Back
          </Text>
        </Pressable>


        {/* Brand */}

        <View style={styles.brandRow}>
          <Text style={styles.brandIcon}>
            ❄️
          </Text>

          <Text style={styles.brand}>
            BanReady
          </Text>
        </View>


        {/* Header */}

        <Text style={styles.title}>
          Parking Options
        </Text>

        <Text style={styles.subtitle}>
          Verified municipal parking candidates
          near your parked location.
        </Text>


        {/* Origin */}

        <View style={styles.originCard}>
          <Text style={styles.originLabel}>
            MOVING FROM
          </Text>

          <Text style={styles.originStreet}>
            {street}
          </Text>

          {latitude !== "" &&
            longitude !== "" && (
              <Text style={styles.originCoordinate}>
                {latitude}, {longitude}
              </Text>
            )}
        </View>


        {/* Important current limitation */}

        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>
            About these options
          </Text>

          <Text style={styles.infoText}>
            These facilities are verified parking
            candidates with historical Worcester
            winter-ban evidence.
          </Text>

          <Text style={styles.infoText}>
            BanReady does not yet know live space
            availability or capacity. Distances shown
            here are straight-line estimates, not
            walking routes.
          </Text>
        </View>


        {/* Result summary */}

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            Nearby options
          </Text>

          <Text style={styles.sectionCount}>
            {options.length}
          </Text>
        </View>


        {/* Parking options */}

        {isLoading && (
        <View style={styles.loadingCard}>
            <Text style={styles.loadingText}>
            Finding verified parking options...
            </Text>
        </View>
        )}


        {errorMessage !== "" && (
        <View style={styles.errorCard}>
            <Text style={styles.errorTitle}>
            Could not load parking options
            </Text>

            <Text style={styles.errorText}>
            {errorMessage}
            </Text>
        </View>
        )}


        {!isLoading &&
        errorMessage === "" &&
        options.length === 0 && (
            <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>
                No verified options found
            </Text>

            <Text style={styles.emptyText}>
                BanReady did not find an eligible
                verified winter-ban parking destination
                for this location.
            </Text>
            </View>
        )}


        {options.map(
        (option, index) => (
            <ParkingOptionCard
            key={option.parking_id}
            option={option}
            recommended={index === 0}
            />
        )
        )}




        {/* Return */}

        <Pressable
          style={({ pressed }) => [
            styles.analyticsButton,

            pressed
              ? styles.analyticsButtonPressed
              : null,
          ]}
          onPress={() => {
            router.push({
              pathname: "/street-chance",

              params: {
                streetName: street,
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
          <View style={styles.analyticsButtonContent}>
            <View style={styles.analyticsIcon}>
              <Text style={styles.analyticsIconText}>
                %
              </Text>
            </View>

            <View style={styles.analyticsTextGroup}>
              <Text style={styles.analyticsTitle}>
                Explore Modeled Parking Chance
              </Text>

              <Text style={styles.analyticsSubtitle}>
                Compare prototype parking estimates
                across nearby streets
              </Text>
            </View>

            <Text style={styles.analyticsArrow}>
              ›
            </Text>
          </View>
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


        {/* Disclaimer */}

        <Text style={styles.footer}>
          A listed destination is not a guarantee
          that parking is currently available.
          Follow posted facility rules and current
          City of Worcester instructions.
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
    marginBottom: 18,
    },


    backText: {
    color: "#1769E0",
    fontSize: 17,
    fontWeight: "600",
    },


    brandRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 20,
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


    title: {
    color: "#12223B",
    fontSize: 34,
    fontWeight: "900",
    },


    subtitle: {
    color: "#667085",
    fontSize: 16,
    lineHeight: 23,
    marginTop: 8,
    marginBottom: 20,
    },


    originCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 20,
    marginBottom: 14,
    },


    originLabel: {
    color: "#667085",
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1,
    },


    originStreet: {
    color: "#12223B",
    fontSize: 23,
    fontWeight: "800",
    marginTop: 7,
    },


    originCoordinate: {
    color: "#98A2B3",
    fontSize: 12,
    marginTop: 6,
    },


    infoCard: {
    backgroundColor: "#EFF8FF",
    borderColor: "#B2DDFF",
    borderWidth: 1,
    borderRadius: 18,
    padding: 18,
    marginBottom: 22,
    },


    infoTitle: {
    color: "#175CD3",
    fontSize: 15,
    fontWeight: "800",
    marginBottom: 7,
    },


    infoText: {
    color: "#344054",
    fontSize: 13,
    lineHeight: 20,
    marginTop: 4,
    },


    sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
    },


    sectionTitle: {
    color: "#12223B",
    fontSize: 21,
    fontWeight: "800",
    },


    sectionCount: {
    marginLeft: 9,
    backgroundColor: "#E8F1FF",
    color: "#175CD3",
    fontSize: 12,
    fontWeight: "800",
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: 12,
    overflow: "hidden",
    },


    optionCard: {
    backgroundColor: "#FFFFFF",
    borderColor: "#EAECF0",
    borderWidth: 1,
    borderRadius: 22,
    padding: 20,
    marginBottom: 14,
    },


    recommendedCard: {
    borderColor: "#84ADFF",
    borderWidth: 2,
    },


    recommendedBadge: {
    alignSelf: "flex-start",
    backgroundColor: "#E8F1FF",
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginBottom: 15,
    },


    recommendedBadgeText: {
    color: "#175CD3",
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 0.6,
    },


    optionHeader: {
    flexDirection: "row",
    alignItems: "center",
    },


    parkingIcon: {
    width: 46,
    height: 46,
    borderRadius: 13,
    backgroundColor: "#1769E0",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 13,
    },


    parkingIconText: {
    color: "#FFFFFF",
    fontSize: 24,
    fontWeight: "900",
    },


    optionHeading: {
    flex: 1,
    },


    optionName: {
    color: "#12223B",
    fontSize: 18,
    fontWeight: "800",
    },


    optionAddress: {
    color: "#667085",
    fontSize: 13,
    marginTop: 4,
    },


    optionDivider: {
    height: 1,
    backgroundColor: "#EAECF0",
    marginVertical: 16,
    },


    detailRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
    gap: 18,
    },


    detailLabel: {
    flex: 1,
    color: "#667085",
    fontSize: 13,
    },


    detailValue: {
    flex: 1,
    color: "#344054",
    fontSize: 13,
    fontWeight: "700",
    textAlign: "right",
    },


    distanceValue: {
    flex: 1,
    color: "#175CD3",
    fontSize: 14,
    fontWeight: "800",
    textAlign: "right",
    },


    verifiedValue: {
    flex: 1,
    color: "#067647",
    fontSize: 13,
    fontWeight: "800",
    textAlign: "right",
    },


    unknownValue: {
    flex: 1,
    color: "#B54708",
    fontSize: 13,
    fontWeight: "800",
    textAlign: "right",
    },


    capacityNotice: {
    backgroundColor: "#FFFAEB",
    borderRadius: 14,
    padding: 14,
    },


    capacityNoticeTitle: {
    color: "#93370D",
    fontSize: 13,
    fontWeight: "800",
    },


    capacityNoticeText: {
    color: "#B54708",
    fontSize: 12,
    lineHeight: 18,
    marginTop: 5,
    },


    banNotice: {
    backgroundColor: "#EFF8FF",
    borderRadius: 14,
    padding: 14,
    marginTop: 10,
    },


    banNoticeTitle: {
    color: "#175CD3",
    fontSize: 13,
    fontWeight: "800",
    },


    banNoticeText: {
    color: "#344054",
    fontSize: 12,
    lineHeight: 18,
    marginTop: 5,
    },


    secondaryButton: {
    backgroundColor: "#FFFFFF",
    borderColor: "#D0D5DD",
    borderWidth: 1,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 16,
    },


    secondaryButtonText: {
    color: "#344054",
    fontSize: 15,
    fontWeight: "700",
    },


    footer: {
    color: "#98A2B3",
    fontSize: 11,
    lineHeight: 17,
    textAlign: "center",
    marginTop: 18,
    },

    loadingCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 18,
    padding: 20,
    marginBottom: 14,
    },

    loadingText: {
    color: "#475467",
    fontSize: 14,
    fontWeight: "600",
    textAlign: "center",
    },

    errorCard: {
    backgroundColor: "#FEF3F2",
    borderColor: "#FECDCA",
    borderWidth: 1,
    borderRadius: 18,
    padding: 18,
    marginBottom: 14,
    },

    errorTitle: {
    color: "#B42318",
    fontSize: 15,
    fontWeight: "800",
    },

    errorText: {
    color: "#B42318",
    fontSize: 13,
    lineHeight: 19,
    marginTop: 6,
    },

    emptyCard: {
    backgroundColor: "#FFFAEB",
    borderColor: "#FEDF89",
    borderWidth: 1,
    borderRadius: 18,
    padding: 18,
    marginBottom: 14,
    },

    emptyTitle: {
    color: "#93370D",
    fontSize: 15,
    fontWeight: "800",
    },

    emptyText: {
    color: "#B54708",
    fontSize: 13,
    lineHeight: 19,
    marginTop: 6,
    },

    analyticsButton: {
      backgroundColor: "#10243F",
      borderRadius: 18,
      paddingVertical: 16,
      paddingHorizontal: 16,
      marginTop: 16,
    },

    analyticsButtonPressed: {
      opacity: 0.82,
    },

    analyticsButtonContent: {
      flexDirection: "row",
      alignItems: "center",
    },

    analyticsIcon: {
      width: 44,
      height: 44,
      borderRadius: 13,
      backgroundColor: "#2070C0",
      alignItems: "center",
      justifyContent: "center",
    },

    analyticsIconText: {
      color: "#FFFFFF",
      fontSize: 21,
      fontWeight: "900",
    },

    analyticsTextGroup: {
      flex: 1,
      marginLeft: 13,
      paddingRight: 8,
    },

    analyticsTitle: {
      color: "#FFFFFF",
      fontSize: 15,
      fontWeight: "900",
    },

    analyticsSubtitle: {
      color: "#D0D5DD",
      fontSize: 11,
      lineHeight: 16,
      marginTop: 4,
    },

    analyticsArrow: {
      color: "#FFFFFF",
      fontSize: 29,
      fontWeight: "500",
    },

});