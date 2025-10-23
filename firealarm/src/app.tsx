import { useEffect } from "react";
import { View, Text } from "react-native";
import * as Notifications from "expo-notifications";

export default function App() {
  useEffect(() => {
    (async () => {
      const { status } = await Notifications.requestPermissionsAsync();
      console.log("notif perm:", status);
      console.log("transport start (MQTT/WebSocket placeholder)");
    })();
    return () => console.log("transport stop");
  }, []);
  return (
    <View style={{flex:1,alignItems:"center",justifyContent:"center"}}>
      <Text>Firewatch App Skeleton</Text>
      <Text>owner/member role to be added</Text>
    </View>
  );
}
