import * as Location from "expo-location";
import { router } from "expo-router";
import { useState } from "react";

import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from "react-native";

import { SafeAreaView } from "react-native-safe-area-context";

import { checkParking } from "@/services/banreadyApi";


export default function LocationScreen() {
  const [street, setStreet] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");

  const [banActive, setBanActive] = useState(true);

  // Demo switch: force the permanent 2-6 a.m. ban on.
  // When off, the backend still turns it on automatically
  // between Dec 1 and Apr 30, 2-6 a.m. Worcester time.
  const [overnightBanActive, setOvernightBanActive] =
    useState(false);

  const [isChecking, setIsChecking] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");


  // =========================================================
  // Fill latitude / longitude from the phone's GPS
  // =========================================================

  async function handleUseMyLocation() {
    setErrorMessage("");
    setIsLocating(true);

    try {
      const permission =
        await Location.requestForegroundPermissionsAsync();

      if (permission.status !== "granted") {
        setErrorMessage(
          "Location permission was not granted. You can still enter coordinates manually."
        );

        return;
      }

      const position =
        await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.High,
        });

      setLatitude(
        position.coords.latitude.toFixed(6)
      );

      setLongitude(
        position.coords.longitude.toFixed(6)
      );

      if (street.trim() === "") {
        setStreet("My current location");
      }
    } catch (error) {
      setErrorMessage(
        "BanReady could not read your location. Check that location services are on, or enter coordinates manually."
      );
    } finally {
      setIsLocating(false);
    }
  }


  // =========================================================
  // Validate location and call the real BanReady API
  // =========================================================

  async function handleSaveLocation() {
    const lat = Number(latitude);
    const lng = Number(longitude);

    setErrorMessage("");

    // -------------------------------------------------------
    // Required fields
    // -------------------------------------------------------

    if (
      street.trim() === "" ||
      latitude.trim() === "" ||
      longitude.trim() === ""
    ) {
      setErrorMessage(
        "Enter a street label, latitude, and longitude."
      );

      return;
    }


    // -------------------------------------------------------
    // Coordinate number validation
    // -------------------------------------------------------

    if (
      Number.isNaN(lat) ||
      Number.isNaN(lng)
    ) {
      setErrorMessage(
        "Latitude and longitude must be valid numbers."
      );

      return;
    }


    // -------------------------------------------------------
    // Coordinate range validation
    // -------------------------------------------------------

    if (
      lat < -90 ||
      lat > 90 ||
      lng < -180 ||
      lng > 180
    ) {
      setErrorMessage(
        "The latitude or longitude is outside the valid range."
      );

      return;
    }


    // -------------------------------------------------------
    // Start API request
    // -------------------------------------------------------

    setIsChecking(true);

    try {
      const result = await checkParking({
        latitude: lat,
        longitude: lng,

        // Development simulation:
        //
        // The current Snow Ban switch represents an active
        // declared ban.
        declared_ban_active: banActive,

        // For current development testing, the same switch
        // also activates snow-emergency rules so permanent
        // Worcester ban streets can be tested.
        snow_emergency_active: banActive,

        // The backend turns the permanent 2 AM–6 AM ban on
        // automatically (Dec 1 – Apr 30, Worcester time).
        // This switch forces it on for testing and demos.
        permanent_time_restriction_active:
          overnightBanActive,
      });


      // -----------------------------------------------------
      // Send the real API result to status.tsx
      // -----------------------------------------------------

      router.push({
        pathname: "/status",

        params: {
          status: result.status,

          street:
            result.street_name ||
            street,

          latitude: latitude,
          longitude: longitude,

          parkedSide:
            result.parked_side,

          restrictedSide:
            result.restricted_side,

          banType:
            result.ban_type,

          banZone:
            result.ban_zone,

          distance:
            result.distance_meters !== null
              ? result.distance_meters.toFixed(2)
              : "Unknown",

          reason:
            result.reason,
        },
      });
    } catch (error) {
      // -----------------------------------------------------
      // API/network error
      // -----------------------------------------------------

      if (error instanceof Error) {
        setErrorMessage(
          error.message
        );
      } else {
        setErrorMessage(
          "BanReady could not contact the backend."
        );
      }
    } finally {
      setIsChecking(false);
    }
  }


  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={
          Platform.OS === "ios"
            ? "padding"
            : undefined
        }
      >
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Back button */}

          <Pressable
            onPress={() => router.back()}
          >
            <Text style={styles.back}>
              ‹ Back
            </Text>
          </Pressable>


          {/* Page header */}

          <View style={styles.header}>
            <Text style={styles.logo}>
              ❄️
            </Text>

            <Text style={styles.title}>
              Test Location
            </Text>

            <Text style={styles.subtitle}>
              Use your phone's location or enter a Worcester
              location manually.
            </Text>
          </View>


          {/* Development indicator */}

          <View style={styles.testBadge}>
            <Text style={styles.testBadgeText}>
              DEVELOPMENT MODE
            </Text>
          </View>


          {/* Car location form */}

          <View style={styles.card}>
            <Text style={styles.cardTitle}>
              Car location
            </Text>


            {/* Use the phone's GPS */}

            <Pressable
              style={[
                styles.locationButton,

                (isLocating || isChecking) &&
                  styles.primaryButtonDisabled,
              ]}
              onPress={handleUseMyLocation}
              disabled={isLocating || isChecking}
            >
              <Text style={styles.locationButtonText}>
                {isLocating
                  ? "Finding your location..."
                  : "📍 Use my current location"}
              </Text>
            </Pressable>


            {/* Street label */}

            <Text style={styles.label}>
              Street or location name
            </Text>

            <TextInput
              style={styles.input}
              value={street}
              onChangeText={(value) => {
                setStreet(value);
                setErrorMessage("");
              }}
              placeholder="Example: Conway St"
              placeholderTextColor="#98A2B3"
              editable={!isChecking}
            />


            {/* Latitude */}

            <Text style={styles.label}>
              Latitude
            </Text>

            <TextInput
              style={styles.input}
              value={latitude}
              onChangeText={(value) => {
                setLatitude(value);
                setErrorMessage("");
              }}
              placeholder="Example: 42.211284604405"
              placeholderTextColor="#98A2B3"
              keyboardType="numbers-and-punctuation"
              editable={!isChecking}
            />


            {/* Longitude */}

            <Text style={styles.label}>
              Longitude
            </Text>

            <TextInput
              style={styles.input}
              value={longitude}
              onChangeText={(value) => {
                setLongitude(value);
                setErrorMessage("");
              }}
              placeholder="Example: -71.795189475878"
              placeholderTextColor="#98A2B3"
              keyboardType="numbers-and-punctuation"
              editable={!isChecking}
            />
          </View>


          {/* Snow ban simulator */}

          <View style={styles.card}>
            <View style={styles.switchRow}>
              <View style={styles.switchText}>
                <Text style={styles.cardTitle}>
                  Snow ban
                </Text>

                <Text style={styles.description}>
                  Simulate Worcester snow-ban status.
                </Text>
              </View>

              <Switch
                value={banActive}
                onValueChange={(value) => {
                  setBanActive(value);
                  setErrorMessage("");
                }}
                disabled={isChecking}
                trackColor={{
                  false: "#D0D5DD",
                  true: "#A9C9F8",
                }}
                thumbColor={
                  banActive
                    ? "#1769E0"
                    : "#F2F4F7"
                }
              />
            </View>


            {/* Ban status indicator */}

            <View
              style={[
                styles.banStatus,

                banActive
                  ? styles.banActive
                  : styles.banInactive,
              ]}
            >
              <View
                style={[
                  styles.statusDot,

                  {
                    backgroundColor:
                      banActive
                        ? "#D92D20"
                        : "#12B76A",
                  },
                ]}
              />

              <Text
                style={[
                  styles.statusText,

                  {
                    color:
                      banActive
                        ? "#B42318"
                        : "#027A48",
                  },
                ]}
              >
                {banActive
                  ? "SNOW BAN ACTIVE"
                  : "NO ACTIVE SNOW BAN"}
              </Text>
            </View>
          </View>


          {/* Overnight permanent-ban simulator */}

          <View style={styles.card}>
            <View style={styles.switchRow}>
              <View style={styles.switchText}>
                <Text style={styles.cardTitle}>
                  Overnight ban (2–6 a.m.)
                </Text>

                <Text style={styles.description}>
                  Simulate the permanent winter ban on main
                  roads and bus routes. Applied automatically
                  Dec 1 – Apr 30, 2–6 a.m.
                </Text>
              </View>

              <Switch
                value={overnightBanActive}
                onValueChange={(value) => {
                  setOvernightBanActive(value);
                  setErrorMessage("");
                }}
                disabled={isChecking}
                trackColor={{
                  false: "#D0D5DD",
                  true: "#A9C9F8",
                }}
                thumbColor={
                  overnightBanActive
                    ? "#1769E0"
                    : "#F2F4F7"
                }
              />
            </View>
          </View>


          {/* Real API check button */}

          <Pressable
            style={[
              styles.primaryButton,

              isChecking &&
                styles.primaryButtonDisabled,
            ]}
            onPress={handleSaveLocation}
            disabled={isChecking}
          >
            <Text style={styles.primaryButtonText}>
              {isChecking
                ? "Checking Worcester..."
                : "Test This Location"}
            </Text>
          </Pressable>


          {/* API / validation error */}

          {errorMessage !== "" && (
            <View style={styles.errorCard}>
              <Text style={styles.errorTitle}>
                Could not check parking
              </Text>

              <Text style={styles.errorText}>
                {errorMessage}
              </Text>
            </View>
          )}


          {/* Development explanation */}

          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>
              What happens when you test?
            </Text>

            <Text style={styles.infoText}>
              BanReady checks this coordinate against Worcester street
              data, determines the parked side, and evaluates the
              simulated winter parking ban.
            </Text>
          </View>


          {/* Footer */}

          <Text style={styles.footer}>
            Development mode uses your phone's location or
            manual Worcester coordinates, and simulated ban
            switches.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}


const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },


  safeArea: {
    flex: 1,
    backgroundColor: "#F5F7FA",
  },


  container: {
    padding: 24,
    paddingBottom: 60,
  },


  back: {
    color: "#1769E0",
    fontSize: 17,
    fontWeight: "600",
    marginBottom: 24,
  },


  header: {
    marginBottom: 18,
  },


  logo: {
    fontSize: 40,
    marginBottom: 10,
  },


  title: {
    fontSize: 34,
    fontWeight: "800",
    color: "#12223B",
  },


  subtitle: {
    marginTop: 8,
    fontSize: 17,
    lineHeight: 24,
    color: "#667085",
  },


  testBadge: {
    alignSelf: "flex-start",
    backgroundColor: "#FFF3D6",
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    marginBottom: 20,
  },


  testBadgeText: {
    color: "#965C00",
    fontSize: 12,
    fontWeight: "700",
  },


  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 22,
    padding: 22,
    marginBottom: 16,
  },


  cardTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: "#12223B",
  },


  label: {
    marginTop: 18,
    marginBottom: 7,
    color: "#344054",
    fontSize: 14,
    fontWeight: "600",
  },


  input: {
    height: 54,
    borderWidth: 1,
    borderColor: "#D0D5DD",
    borderRadius: 12,
    paddingHorizontal: 15,
    fontSize: 16,
    color: "#101828",
    backgroundColor: "#FFFFFF",
  },


  switchRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },


  switchText: {
    flex: 1,
    paddingRight: 20,
  },


  description: {
    color: "#667085",
    fontSize: 14,
    marginTop: 5,
  },


  banStatus: {
    marginTop: 20,
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 12,
    padding: 13,
  },


  banActive: {
    backgroundColor: "#FEF3F2",
  },


  banInactive: {
    backgroundColor: "#ECFDF3",
  },


  statusDot: {
    width: 9,
    height: 9,
    borderRadius: 5,
    marginRight: 9,
  },


  statusText: {
    fontSize: 13,
    fontWeight: "800",
  },


  primaryButton: {
    backgroundColor: "#1769E0",
    paddingVertical: 17,
    borderRadius: 14,
    alignItems: "center",
    marginTop: 4,
  },


  primaryButtonDisabled: {
    opacity: 0.6,
  },


  locationButton: {
    marginTop: 16,
    borderWidth: 1,
    borderColor: "#1769E0",
    backgroundColor: "#EFF8FF",
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
  },


  locationButtonText: {
    color: "#1769E0",
    fontSize: 15,
    fontWeight: "700",
  },


  primaryButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },


  errorCard: {
    marginTop: 14,
    backgroundColor: "#FEF3F2",
    borderColor: "#FECDCA",
    borderWidth: 1,
    borderRadius: 16,
    padding: 16,
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
    marginTop: 5,
  },


  infoCard: {
    marginTop: 18,
    backgroundColor: "#EFF8FF",
    borderColor: "#B2DDFF",
    borderWidth: 1,
    borderRadius: 18,
    padding: 18,
  },


  infoTitle: {
    color: "#175CD3",
    fontSize: 15,
    fontWeight: "800",
  },


  infoText: {
    color: "#344054",
    fontSize: 13,
    lineHeight: 20,
    marginTop: 6,
  },


  footer: {
    textAlign: "center",
    color: "#98A2B3",
    fontSize: 12,
    lineHeight: 18,
    marginTop: 20,
  },
});