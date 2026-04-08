import * as Notifications from 'expo-notifications';
import { router, Stack } from 'expo-router';
import { useEffect } from 'react';

function goToNotificationDetails(data: any) {
  if (!data) return;

  router.push({
    pathname: '/notification-details',
    params: {
      alert_id: String(data.alert_id ?? ''),
      device_event_id: String(data.device_event_id ?? ''),
      event_type: String(data.event_type ?? data.alarm_type ?? ''),
      hub_id: String(data.hub_id ?? ''),
      status: String(data.status ?? ''),
      alarm_type: String(data.alarm_type ?? data.event_type ?? ''),
      alarm_datetime: String(data.alarm_datetime ?? ''),
      client_id: String(data.client_id ?? ''),
      audio_url: String(data.audio_url ?? data.recording_url ?? ''),    },
  });
}

export default function RootLayout() {
  useEffect(() => {
    Notifications.getLastNotificationResponseAsync().then((response) => {
      if (response?.notification?.request?.content?.data) {
        goToNotificationDetails(response.notification.request.content.data);
      }
    });

    const subscription = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data;
      goToNotificationDetails(data);
    });

    return () => {
      subscription.remove();
    };
  }, []);

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Screen name="login" />
      <Stack.Screen name="register" />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="notification-details" />
    </Stack>
  );
}