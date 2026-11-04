
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
    Dimensions,
    FlatList,
    Pressable,
    ScrollView,
    StyleSheet,
    Text,
    View,
} from "react-native";

import { SafeAreaView } from "react-native-safe-area-context";

const SCREEN_WIDTH =
  Dimensions.get("window").width;

const OPTION_CARD_WIDTH =
  SCREEN_WIDTH - 72;


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
  index,
}: {
  option: ParkingOption;
  recommended: boolean;
  index: number;
}) {
  return (
    <View
      style={[
        styles.optionCard,
        {
          width: OPTION_CARD_WIDTH,
        },
        recommended
          ? styles.recommendedCard
          : null,
      ]}
    >
      {recommended ? (
        <View style={styles.recommendedBadge}>
          <Text style={styles.recommendedBadgeText}>
            NEAREST VERIFIED OPTION
          </Text>
        </View>
      ) : (
        <View style={styles.optionNumberBadge}>
          <Text style={styles.optionNumberBadgeText}>
            OPTION {index + 1}
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
          <Text
            style={styles.optionName}
            numberOfLines={2}
          >
            {option.name}
          </Text>

          <Text
            style={styles.optionAddress}
            numberOfLines={1}
          >
            {option.address ??
              "Address unavailable"}
          </Text>
        </View>
      </View>

      <View style={styles.optionDivider} />

      <View style={styles.compactDetails}>
        <View style={styles.compactDetailItem}>
          <Text style={styles.compactDetailLabel}>
            Type
          </Text>

          <Text
            style={styles.compactDetailValue}
            numberOfLines={1}
          >
            {prettyDestinationType(
              option.destination_type
            )}
          </Text>
        </View>

        <View style={styles.compactDivider} />

        <View style={styles.compactDetailItem}>
          <Text style={styles.compactDetailLabel}>
            Distance
          </Text>

          <Text style={styles.compactDistanceValue}>
            {option.distance_km.toFixed(2)} km
          </Text>
        </View>
      </View>

      <View style={styles.statusRow}>
        <View style={styles.verifiedBadge}>
          <Text style={styles.verifiedBadgeText}>
            ✓ Verified
          </Text>
        </View>

        <View style={styles.confirmedBadge}>
          <Text style={styles.confirmedBadgeText}>
            Ban evidence
          </Text>
        </View>

        <View style={styles.unknownBadge}>
          <Text style={styles.unknownBadgeText}>
            Availability unknown
          </Text>
        </View>
      </View>

      {option.ban_availability_note ? (
        <View style={styles.banNotice}>
          <Text style={styles.banNoticeTitle}>
            Winter-ban note
          </Text>

          <Text
            style={styles.banNoticeText}
            numberOfLines={3}
          >
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

    const [
      activeOptionIndex,
      setActiveOptionIndex,
    ] = useState(0);


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

        setActiveOptionIndex(0);

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

        {/* Main modeled analytics action */}
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


        {/* Important current limitation */}

        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>
            About these options
          </Text>

          <Text style={styles.infoText}>
            Verified Worcester winter-ban parking
            candidates ranked by straight-line distance.
            Live availability is unknown.
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


        {!isLoading &&
          errorMessage === "" &&
          options.length > 0 && (
            <>
              <FlatList
                data={options}
                horizontal
                nestedScrollEnabled
                showsHorizontalScrollIndicator={
                  false
                }
                decelerationRate="fast"
                snapToInterval={
                  OPTION_CARD_WIDTH + 12
                }
                snapToAlignment="start"
                disableIntervalMomentum
                contentContainerStyle={
                  styles.optionsCarousel
                }
                ItemSeparatorComponent={() => (
                  <View
                    style={
                      styles.optionSeparator
                    }
                  />
                )}
                keyExtractor={(option) =>
                  option.parking_id
                }
                renderItem={({
                  item,
                  index,
                }) => (
                  <ParkingOptionCard
                    option={item}
                    index={index}
                    recommended={index === 0}
                  />
                )}
                onMomentumScrollEnd={(
                  event
                ) => {
                  const offset =
                    event.nativeEvent
                      .contentOffset.x;

                  const interval =
                    OPTION_CARD_WIDTH + 12;

                  const newIndex = Math.round(
                    offset / interval
                  );

                  setActiveOptionIndex(
                    Math.max(
                      0,
                      Math.min(
                        newIndex,
                        options.length - 1
                      )
                    )
                  );
                }}
              />

              <View style={styles.carouselFooter}>
                <Text style={styles.carouselCounter}>
                  {activeOptionIndex + 1}
                  {" of "}
                  {options.length}
                </Text>

                <View style={styles.paginationDots}>
                  {options.map(
                    (option, index) => (
                      <View
                        key={option.parking_id}
                        style={[
                          styles.paginationDot,

                          index ===
                          activeOptionIndex
                            ? styles.paginationDotActive
                            : null,
                        ]}
                      />
                    )
                  )}
                </View>

                <Text style={styles.swipeHint}>
                  Swipe for more parking options
                </Text>
              </View>
            </>
          )}

        {/* Return */}

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
      borderRadius: 16,
      padding: 14,
      marginBottom: 18,
    },

    infoTitle: {
      color: "#175CD3",
      fontSize: 13,
      fontWeight: "800",
      marginBottom: 4,
    },

    infoText: {
      color: "#344054",
      fontSize: 11,
      lineHeight: 17,
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
      borderRadius: 20,
      padding: 16,
      marginBottom: 2,
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
      paddingVertical: 5,
      marginBottom: 12,
    },

    recommendedBadgeText: {
      color: "#175CD3",
      fontSize: 9,
      fontWeight: "900",
      letterSpacing: 0.6,
    },

    optionNumberBadge: {
      alignSelf: "flex-start",
      backgroundColor: "#F2F4F7",
      borderRadius: 20,
      paddingHorizontal: 10,
      paddingVertical: 5,
      marginBottom: 12,
    },

    optionNumberBadgeText: {
      color: "#475467",
      fontSize: 9,
      fontWeight: "900",
      letterSpacing: 0.6,
    },

    optionHeader: {
      flexDirection: "row",
      alignItems: "center",
    },

    parkingIcon: {
      width: 42,
      height: 42,
      borderRadius: 12,
      backgroundColor: "#1769E0",
      alignItems: "center",
      justifyContent: "center",
      marginRight: 12,
    },

    parkingIconText: {
      color: "#FFFFFF",
      fontSize: 21,
      fontWeight: "900",
    },

    optionHeading: {
      flex: 1,
    },

    optionName: {
      color: "#12223B",
      fontSize: 17,
      lineHeight: 21,
      fontWeight: "800",
    },

    optionAddress: {
      color: "#667085",
      fontSize: 12,
      marginTop: 3,
    },

    optionDivider: {
      height: 1,
      backgroundColor: "#EAECF0",
      marginVertical: 13,
    },

    compactDetails: {
      flexDirection: "row",
      alignItems: "center",
    },

    compactDetailItem: {
      flex: 1,
    },

    compactDetailLabel: {
      color: "#667085",
      fontSize: 10,
      fontWeight: "700",
    },

    compactDetailValue: {
      color: "#344054",
      fontSize: 12,
      fontWeight: "800",
      marginTop: 3,
    },

    compactDistanceValue: {
      color: "#175CD3",
      fontSize: 14,
      fontWeight: "900",
      marginTop: 3,
    },

    compactDivider: {
      width: 1,
      height: 36,
      backgroundColor: "#EAECF0",
      marginHorizontal: 14,
    },

    statusRow: {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: 6,
      marginTop: 14,
    },

    verifiedBadge: {
      backgroundColor: "#ECFDF3",
      borderRadius: 999,
      paddingHorizontal: 8,
      paddingVertical: 5,
    },

    verifiedBadgeText: {
      color: "#067647",
      fontSize: 9,
      fontWeight: "900",
    },

    confirmedBadge: {
      backgroundColor: "#EFF8FF",
      borderRadius: 999,
      paddingHorizontal: 8,
      paddingVertical: 5,
    },

    confirmedBadgeText: {
      color: "#175CD3",
      fontSize: 9,
      fontWeight: "900",
    },

    unknownBadge: {
      backgroundColor: "#FFFAEB",
      borderRadius: 999,
      paddingHorizontal: 8,
      paddingVertical: 5,
    },

    unknownBadgeText: {
      color: "#B54708",
      fontSize: 9,
      fontWeight: "900",
    },

    banNotice: {
      backgroundColor: "#EFF8FF",
      borderRadius: 13,
      padding: 11,
      marginTop: 13,
    },

    banNoticeTitle: {
      color: "#175CD3",
      fontSize: 11,
      fontWeight: "900",
    },

    banNoticeText: {
      color: "#344054",
      fontSize: 10,
      lineHeight: 15,
      marginTop: 3,
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
      paddingVertical: 14,
      paddingHorizontal: 15,
      marginBottom: 14,
    },

    analyticsButtonPressed: {
      opacity: 0.82,
    },

    analyticsButtonContent: {
      flexDirection: "row",
      alignItems: "center",
    },

    analyticsIcon: {
      width: 40,
      height: 40,
      borderRadius: 12,
      backgroundColor: "#2070C0",
      alignItems: "center",
      justifyContent: "center",
    },

    analyticsIconText: {
      color: "#FFFFFF",
      fontSize: 19,
      fontWeight: "900",
    },

    analyticsTextGroup: {
      flex: 1,
      marginLeft: 12,
      paddingRight: 7,
    },

    analyticsTitle: {
      color: "#FFFFFF",
      fontSize: 14,
      lineHeight: 18,
      fontWeight: "900",
    },

    analyticsSubtitle: {
      color: "#D0D5DD",
      fontSize: 10,
      lineHeight: 14,
      marginTop: 3,
    },

    analyticsArrow: {
      color: "#FFFFFF",
      fontSize: 27,
      fontWeight: "500",
    },

    optionsCarousel: {
      paddingRight: 24,
    },

    optionSeparator: {
      width: 12,
    },

    carouselFooter: {
      alignItems: "center",
      marginTop: 13,
      marginBottom: 5,
    },

    carouselCounter: {
      color: "#344054",
      fontSize: 13,
      fontWeight: "800",
    },

    paginationDots: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "center",
      marginTop: 9,
    },

    paginationDot: {
      width: 7,
      height: 7,
      borderRadius: 4,
      backgroundColor: "#D0D5DD",
      marginHorizontal: 4,
    },

    paginationDotActive: {
      width: 21,
      backgroundColor: "#2070C0",
    },

    swipeHint: {
      color: "#98A2B3",
      fontSize: 11,
      marginTop: 8,
    },

});