import {
  DarkTheme,
  DefaultTheme,
  Stack,
  ThemeProvider,
} from "expo-router";

import * as SplashScreen from "expo-splash-screen";

import { useColorScheme } from "react-native";
import {
  SafeAreaProvider,
} from "react-native-safe-area-context";

import {
  AnimatedSplashOverlay,
} from "@/components/animated-icon";


SplashScreen.preventAutoHideAsync();


export default function RootLayout() {
  const colorScheme = useColorScheme();

  return (
    <SafeAreaProvider>
      <ThemeProvider
        value={
          colorScheme === "dark"
            ? DarkTheme
            : DefaultTheme
        }
      >
        <AnimatedSplashOverlay />

        <Stack
          screenOptions={{
            headerShown: false,
          }}
        >
          <Stack.Screen name="index" />

          <Stack.Screen name="location" />

          <Stack.Screen name="status" />

          <Stack.Screen name="parking" />

          <Stack.Screen
            name="street-chance"
          />

          <Stack.Screen
            name="parking-zone"
          />

          {/* <Stack.Screen
            name="walking-zones"
          /> */}
        </Stack>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}