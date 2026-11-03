import { useColorScheme } from "react-native";

import { Colors } from "@/constants/theme";

export function useTheme() {
  const scheme = useColorScheme();

  const theme: "light" | "dark" =
    scheme === "dark"
      ? "dark"
      : "light";

  return Colors[theme];
}