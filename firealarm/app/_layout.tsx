import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      {/* Home Screen (AlarmCast) */}
      <Stack.Screen name="index" />

      {/* Login & Register */}
      <Stack.Screen name="login" />
      <Stack.Screen name="register" />

      {/* Tabs Layout (Dashboard, History, Settings) */}
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
    </Stack>
  );
}
