import {
  router,
  useLocalSearchParams,
} from "expo-router";

import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import {
  SafeAreaView,
} from "react-native-safe-area-context";


export default function ParkingZoneScreen() {
  const params = useLocalSearchParams();

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.eyebrow}>
          PROTOTYPE PARKING ANALYTICS
        </Text>

        <Text style={styles.title}>
          Modeled Parking Zone
        </Text>

        <Text style={styles.description}>
          Screen 5 is ready for implementation.
        </Text>

        <Text style={styles.locationText}>
          Latitude: {String(
            params.latitude ?? ""
          )}
        </Text>

        <Text style={styles.locationText}>
          Longitude: {String(
            params.longitude ?? ""
          )}
        </Text>

        <Pressable
          style={styles.button}
          onPress={() => router.back()}
        >
          <Text style={styles.buttonText}>
            Go Back
          </Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}


const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F5F7FA",
  },

  container: {
    flex: 1,
    justifyContent: "center",
    padding: 24,
  },

  eyebrow: {
    color: "#2070C0",
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 1.1,
  },

  title: {
    color: "#10243F",
    fontSize: 30,
    fontWeight: "900",
    marginTop: 7,
  },

  description: {
    color: "#667085",
    fontSize: 16,
    lineHeight: 23,
    marginTop: 10,
    marginBottom: 18,
  },

  locationText: {
    color: "#344054",
    fontSize: 14,
    marginTop: 5,
  },

  button: {
    backgroundColor: "#2070C0",
    borderRadius: 15,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 24,
  },

  buttonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "900",
  },
});