import { router } from "expo-router";

import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { SafeAreaView } from "react-native-safe-area-context";

export default function HomeScreen() {
  function handleManualLocation() {
    router.push("/location");
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.logo}>❄️</Text>
        <Text style={styles.title}>BanReady</Text>

        <Text style={styles.subtitle}>
          Know where to move your car before the snow ban.
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          Where is your car?
        </Text>

        <Text style={styles.description}>
          For initial testing, choose a Worcester parking
          location manually.
        </Text>

        <Pressable
          style={styles.primaryButton}
          onPress={handleManualLocation}
        >
          <Text style={styles.primaryButtonText}>
            Choose Worcester Location
          </Text>
        </Pressable>
      </View>

      <View style={styles.testBadge}>
        <Text style={styles.testBadgeText}>
          TEST MODE
        </Text>
      </View>

      <Text style={styles.footer}>
        Worcester Snow Parking Prototype
      </Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F5F7FA",
    padding: 24,
  },

  header: {
    marginTop: 50,
    marginBottom: 40,
  },

  logo: {
    fontSize: 48,
    marginBottom: 12,
  },

  title: {
    fontSize: 38,
    fontWeight: "800",
    color: "#12223B",
  },

  subtitle: {
    marginTop: 12,
    fontSize: 17,
    lineHeight: 25,
    color: "#667085",
  },

  card: {
    backgroundColor: "#FFFFFF",
    padding: 24,
    borderRadius: 24,
  },

  cardTitle: {
    fontSize: 24,
    fontWeight: "700",
    color: "#12223B",
  },

  description: {
    marginTop: 10,
    marginBottom: 24,
    fontSize: 16,
    lineHeight: 23,
    color: "#667085",
  },

  primaryButton: {
    backgroundColor: "#1769E0",
    paddingVertical: 17,
    paddingHorizontal: 20,
    borderRadius: 14,
    alignItems: "center",
  },

  primaryButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },

  testBadge: {
    marginTop: 24,
    alignSelf: "flex-start",
    paddingHorizontal: 12,
    paddingVertical: 7,
    backgroundColor: "#FFF3D6",
    borderRadius: 20,
  },

  testBadgeText: {
    color: "#965C00",
    fontWeight: "700",
    fontSize: 12,
  },

  footer: {
    marginTop: 10,
    color: "#98A2B3",
    fontSize: 13,
  },
});