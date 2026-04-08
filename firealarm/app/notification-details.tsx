import { Ionicons } from "@expo/vector-icons";
import { Audio } from "expo-av";
import { router, useLocalSearchParams } from "expo-router";
import { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { API_BASE } from "../constants/api";

type AlertDetails = {
  alert_id: string;
  device_event_id: string;
  event_type: string;
  hub_id: string;
  status: string;
  alarm_type: string;
  alarm_datetime: string;
  client_id: string;
  audio_url: string;
};

export default function NotificationDetails() {
  const params = useLocalSearchParams();

  const alertId = String(params.alert_id ?? "");
  const fallbackDeviceEventId = String(params.device_event_id ?? "");
  const fallbackEventType = String(params.event_type ?? "");
  const fallbackHubId = String(params.hub_id ?? "");
  const fallbackStatus = String(params.status ?? "");
  const fallbackAlarmType = String(params.alarm_type ?? "");
  const fallbackAlarmDatetime = String(params.alarm_datetime ?? "");
  const fallbackClientId = String(params.client_id ?? "");
  const fallbackAudioUrl = String(params.audio_url ?? "");

  const [details, setDetails] = useState<AlertDetails>({
    alert_id: alertId,
    device_event_id: fallbackDeviceEventId,
    event_type: fallbackEventType,
    hub_id: fallbackHubId,
    status: fallbackStatus,
    alarm_type: fallbackAlarmType || fallbackEventType,
    alarm_datetime: fallbackAlarmDatetime,
    client_id: fallbackClientId,
    audio_url: fallbackAudioUrl,
  });

  const [isFetchingDetails, setIsFetchingDetails] = useState(false);
  const [detailsError, setDetailsError] = useState("");

  const soundRef = useRef<Audio.Sound | null>(null);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioError, setAudioError] = useState("");

  useEffect(() => {
    const setupAudio = async () => {
      try {
        await Audio.setAudioModeAsync({
          playsInSilentModeIOS: true,
          staysActiveInBackground: false,
          shouldDuckAndroid: true,
          playThroughEarpieceAndroid: false,
        });
      } catch (error) {
        console.log("Audio mode error:", error);
      }
    };

    setupAudio();

    return () => {
      unloadSound();
    };
  }, []);

  useEffect(() => {
    if (!alertId) return;
    fetchAlertDetails();
  }, [alertId]);

  const fetchAlertDetails = async () => {
    try {
      setIsFetchingDetails(true);
      setDetailsError("");

      const response = await fetch(`${API_BASE}/api/alerts/${alertId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch alert ${alertId}`);
      }

      const data = await response.json();

      setDetails({
        alert_id: String(data.alert_id ?? alertId),
        device_event_id: String(data.device_event_id ?? fallbackDeviceEventId),
        event_type: String(data.event_type ?? fallbackEventType),
        hub_id: String(data.hub_id ?? fallbackHubId),
        status: String(data.status ?? fallbackStatus),
        alarm_type: String(
          data.alarm_type ??
            data.event_type ??
            fallbackAlarmType ??
            fallbackEventType,
        ),
        alarm_datetime: String(
          data.alarm_datetime ?? data.detected_at ?? fallbackAlarmDatetime,
        ),
        client_id: String(data.client_id ?? fallbackClientId),
        audio_url: String(data.audio_url ?? data.recording_url ?? ""),
      });
    } catch (error) {
      console.log("Fetch alert details error:", error);
      setDetailsError(
        "Could not refresh alert details. Showing available notification info.",
      );
    } finally {
      setIsFetchingDetails(false);
    }
  };

  const unloadSound = async () => {
    try {
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }
    } catch (error) {
      console.log("Unload error:", error);
    }
    setIsPlaying(false);
  };

  const playRecording = async () => {
    if (!details.audio_url) {
      setAudioError("No recording available for this alert.");
      return;
    }

    try {
      setAudioError("");
      setIsLoadingAudio(true);

      if (soundRef.current) {
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }

      await Audio.setAudioModeAsync({
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

      console.log("Trying to play:", details.audio_url);

      const { sound } = await Audio.Sound.createAsync(
        { uri: details.audio_url },
        {
          shouldPlay: false,
          volume: 1.0,
          progressUpdateIntervalMillis: 250,
        },
      );

      soundRef.current = sound;

      sound.setOnPlaybackStatusUpdate((playbackStatus) => {
        console.log("Playback status:", playbackStatus);

        if (!playbackStatus.isLoaded) return;

        if (playbackStatus.didJustFinish) {
          setIsPlaying(false);
        }
      });

      const beforePlay = await sound.getStatusAsync();
      console.log("Before play:", beforePlay);

      await sound.playAsync();

      const afterPlay = await sound.getStatusAsync();
      console.log("After play:", afterPlay);

      setIsPlaying(true);
    } catch (error) {
      console.log("Playback error:", error);
      setAudioError("Could not play the recording.");
      setIsPlaying(false);
    } finally {
      setIsLoadingAudio(false);
    }
  };

  const stopRecording = async () => {
    try {
      if (soundRef.current) {
        await soundRef.current.stopAsync();
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }
    } catch (error) {
      console.log("Stop error:", error);
    }
    setIsPlaying(false);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Ionicons name="arrow-back" size={22} color="#11daabff" />
            <Text style={styles.backText}>Back</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Notification Details</Text>
        </View>

        {isFetchingDetails ? (
          <View style={styles.loadingCard}>
            <ActivityIndicator color="#11daabff" />
            <Text style={styles.loadingText}>
              Loading latest alert details...
            </Text>
          </View>
        ) : null}

        {detailsError ? (
          <View style={styles.errorCard}>
            <Text style={styles.errorCardText}>{detailsError}</Text>
          </View>
        ) : null}

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Alarm Information</Text>

          <View style={styles.detailRow}>
            <Text style={styles.label}>Alert ID</Text>
            <Text style={styles.value}>{details.alert_id || "N/A"}</Text>
          </View>

          <View style={styles.detailRow}>
            <Text style={styles.label}>Device Event ID</Text>
            <Text style={styles.value}>{details.device_event_id || "N/A"}</Text>
          </View>

          <View style={styles.detailRow}>
            <Text style={styles.label}>Event Type</Text>
            <Text style={styles.value}>{details.event_type || "N/A"}</Text>
          </View>

          <View style={styles.detailRow}>
            <Text style={styles.label}>Alarm Type</Text>
            <Text style={styles.value}>{details.alarm_type || "N/A"}</Text>
          </View>

          <View style={styles.detailRow}>
            <Text style={styles.label}>Hub ID</Text>
            <Text style={styles.value}>{details.hub_id || "N/A"}</Text>
          </View>

          <View style={styles.detailRow}>
            <Text style={styles.label}>Status</Text>
            <Text style={styles.value}>{details.status || "N/A"}</Text>
          </View>

          <View style={styles.detailRow}>
            <Text style={styles.label}>Date & Time</Text>
            <Text style={styles.value}>{details.alarm_datetime || "N/A"}</Text>
          </View>

          <View style={styles.detailRow}>
            <Text style={styles.label}>Client ID</Text>
            <Text style={styles.value}>{details.client_id || "N/A"}</Text>
          </View>

          <View style={styles.detailRow}>
            <Text style={styles.label}>Recording URL</Text>
            <Text style={styles.value}>{details.audio_url || "N/A"}</Text>
          </View>
        </View>

        <View style={styles.audioCard}>
          <Text style={styles.audioTitle}>Alarm Recording</Text>

          {!details.audio_url ? (
            <Text style={styles.noAudioText}>
              No recording attached to this alert.
            </Text>
          ) : (
            <>
              <TouchableOpacity
                style={[
                  styles.audioButton,
                  isLoadingAudio && styles.audioButtonDisabled,
                ]}
                onPress={isPlaying ? stopRecording : playRecording}
                disabled={isLoadingAudio}
              >
                {isLoadingAudio ? (
                  <ActivityIndicator color="#000" />
                ) : (
                  <>
                    <Ionicons
                      name={isPlaying ? "stop-circle" : "play-circle"}
                      size={22}
                      color="#000"
                    />
                    <Text style={styles.audioButtonText}>
                      {isPlaying ? "Stop Recording" : "Play Recording"}
                    </Text>
                  </>
                )}
              </TouchableOpacity>

              {audioError ? (
                <Text style={styles.errorText}>{audioError}</Text>
              ) : null}
            </>
          )}
        </View>

        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Summary</Text>
          <Text style={styles.summaryText}>
            {details.alarm_type || details.event_type || "Alarm"} detected
            {details.hub_id ? ` on hub ${details.hub_id}` : ""}.
            {details.alarm_datetime
              ? ` Recorded at ${details.alarm_datetime}.`
              : ""}
            {details.status ? ` Current status: ${details.status}.` : ""}
            {details.audio_url
              ? " A recording is available for playback."
              : " No recording is attached."}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#000000ff",
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 16,
    backgroundColor: "#071d50ff",
    borderWidth: 1,
    borderColor: "#11daabff",
    borderRadius: 10,
    padding: 16,
  },
  backButton: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
    gap: 8,
  },
  backText: {
    color: "#11daabff",
    fontSize: 16,
    fontWeight: "600",
  },
  headerTitle: {
    color: "#fff",
    fontSize: 22,
    fontWeight: "bold",
  },
  loadingCard: {
    backgroundColor: "#071d50ff",
    borderWidth: 1,
    borderColor: "#11daabff",
    borderRadius: 10,
    padding: 16,
    marginBottom: 16,
    alignItems: "center",
    gap: 10,
  },
  loadingText: {
    color: "#fff",
    fontSize: 15,
  },
  errorCard: {
    backgroundColor: "#3a1010",
    borderWidth: 1,
    borderColor: "#ff7b7b",
    borderRadius: 10,
    padding: 16,
    marginBottom: 16,
  },
  errorCardText: {
    color: "#fff",
    fontSize: 14,
    lineHeight: 20,
  },
  card: {
    backgroundColor: "#071d50ff",
    borderWidth: 1,
    borderColor: "#11daabff",
    borderRadius: 10,
    padding: 16,
    marginBottom: 16,
  },
  cardTitle: {
    color: "#11daabff",
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 14,
  },
  detailRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#14306eff",
    gap: 12,
  },
  label: {
    color: "#11daabff",
    fontSize: 15,
    fontWeight: "600",
    flex: 1,
  },
  value: {
    color: "#fff",
    fontSize: 15,
    flex: 1,
    textAlign: "right",
  },
  audioCard: {
    backgroundColor: "#071d50ff",
    borderWidth: 1,
    borderColor: "#11daabff",
    borderRadius: 10,
    padding: 16,
    marginBottom: 16,
  },
  audioTitle: {
    color: "#11daabff",
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 12,
  },
  noAudioText: {
    color: "#fff",
    fontSize: 15,
    lineHeight: 22,
  },
  audioButton: {
    backgroundColor: "#11daabff",
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
  },
  audioButtonDisabled: {
    opacity: 0.7,
  },
  audioButtonText: {
    color: "#000",
    fontSize: 16,
    fontWeight: "700",
  },
  errorText: {
    color: "#ff7b7b",
    fontSize: 14,
    marginTop: 10,
  },
  summaryCard: {
    backgroundColor: "#071d50ff",
    borderWidth: 1,
    borderColor: "#11daabff",
    borderRadius: 10,
    padding: 16,
  },
  summaryTitle: {
    color: "#11daabff",
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 10,
  },
  summaryText: {
    color: "#fff",
    fontSize: 15,
    lineHeight: 22,
  },
});
