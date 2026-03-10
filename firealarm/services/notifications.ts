import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export async function registerForPushNotificationsAsync(): Promise<string | null> {
  console.log('registerForPushNotificationsAsync: start');

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      sound: 'default',
      lockscreenVisibility: Notifications.AndroidNotificationVisibility.PUBLIC,
    });
  }

  if (!Device.isDevice) {
    console.log('registerForPushNotificationsAsync: not a physical device');
    return null;
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  console.log('existing notification status:', existingStatus);

  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
    console.log('requested notification status:', finalStatus);
  }

  if (finalStatus !== 'granted') {
    console.log('registerForPushNotificationsAsync: permission not granted');
    return null;
  }

  const projectId =
    Constants?.expoConfig?.extra?.eas?.projectId ??
    Constants?.easConfig?.projectId;

  console.log('projectId:', projectId);

  if (!projectId) {
    throw new Error('Expo projectId not found');
  }

  const token = (
    await Notifications.getExpoPushTokenAsync({
      projectId,
    })
  ).data;

  console.log('Expo push token:', token);
  return token;
}

export async function savePushTokenToBackend(
  apiBase: string,
  userId: string | number,
  expoPushToken: string
): Promise<void> {
  console.log('Saving push token to backend:', `${apiBase}/api/users/${userId}/push-token`);

  const response = await fetch(`${apiBase}/api/users/${userId}/push-token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      expo_push_token: expoPushToken,
    }),
  });

  const rawText = await response.text();
  console.log('savePushTokenToBackend status:', response.status);
  console.log('savePushTokenToBackend response:', rawText);

  if (!response.ok) {
    throw new Error(`Failed to save push token: ${response.status} ${rawText}`);
  }
}

export async function setupPushForLoggedInUser(
  apiBase: string,
  userId: string | number
): Promise<string | null> {
  console.log('setupPushForLoggedInUser: start', { apiBase, userId });

  const expoPushToken = await registerForPushNotificationsAsync();

  if (!expoPushToken) {
    console.log('setupPushForLoggedInUser: no expo push token returned');
    return null;
  }

  await savePushTokenToBackend(apiBase, userId, expoPushToken);
  return expoPushToken;
}