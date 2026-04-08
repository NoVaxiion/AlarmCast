import { Audio } from 'expo-av';
import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as API from '../../constants/api';

interface HistoryItem {
  alert_id: number;
  event_type: string;
  detected_at: string;
  device_id: number;
  status: string;
  audio_url?: string | null;
}

export default function History() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);
  const [playingId, setPlayingId] = useState<number | null>(null);

  useEffect(() => {
    loadHistory();

    const setupAudio = async () => {
      try {
        await Audio.setAudioModeAsync({
          playsInSilentModeIOS: true,
          staysActiveInBackground: false,
          shouldDuckAndroid: true,
          playThroughEarpieceAndroid: false,
        });
      } catch (error) {
        console.log('History audio mode error:', error);
      }
    };

    setupAudio();

    return () => {
      unloadSound();
    };
  }, []);

  const unloadSound = async () => {
    try {
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }
    } catch (error) {
      console.log('History unload error:', error);
    }
    setPlayingId(null);
  };

  const loadHistory = async () => {
    try {
      setLoading(true);
      const hubId = 1;
      const data = await API.getAlertHistory(hubId);
      setHistory(Array.isArray(data) ? data : []);
    } catch (error) {
      Alert.alert('Error', 'Failed to load alert history.');
    } finally {
      setLoading(false);
    }
  };

  const playRecording = async (item: HistoryItem) => {
    try {
      if (!item.audio_url) {
        Alert.alert('No Recording', 'This alert has no recording available.');
        return;
      }

      await Audio.setAudioModeAsync({
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

      if (soundRef.current) {
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }

      const { sound } = await Audio.Sound.createAsync(
        { uri: item.audio_url },
        {
          shouldPlay: false,
          volume: 1.0,
          progressUpdateIntervalMillis: 250,
        }
      );

      soundRef.current = sound;
      setPlayingId(item.alert_id);

      sound.setOnPlaybackStatusUpdate((status) => {
        if (!status.isLoaded) return;
        if (status.didJustFinish) {
          setPlayingId(null);
        }
      });

      await sound.playAsync();
    } catch (error) {
      console.log('History playback error:', error);
      Alert.alert('Playback Error', 'Could not play recording.');
      setPlayingId(null);
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
      console.log('History stop error:', error);
    }
    setPlayingId(null);
  };

  const closeModal = async () => {
    setSelectedItem(null);
    await unloadSound();
  };

  const formatTime = (value: string) => {
    return new Date(value).toLocaleString('en-US', {
      timeZone: 'America/New_York',
    });
  };

  const getCardStyle = (type: string) => {
    const upper = type.toUpperCase();
    if (upper === 'TEST') return styles.testItem;
    return styles.alertItem;
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={loadHistory} />
        }
      >
        <View style={styles.header}>
          <Text style={styles.headerText}>Alert History</Text>
          <Text style={styles.count}>{history.length} records</Text>
        </View>

        {loading && history.length === 0 ? (
          <View style={styles.loadingWrap}>
            <ActivityIndicator size="large" color="#11daabff" />
          </View>
        ) : (
          <View style={styles.list}>
            {history.length === 0 ? (
              <View style={styles.emptyBox}>
                <Text style={styles.emptyText}>No alert history yet</Text>
              </View>
            ) : (
              history.map((item) => (
                <TouchableOpacity
                  key={item.alert_id.toString()}
                  style={[styles.item, getCardStyle(item.event_type)]}
                  onPress={() => setSelectedItem(item)}
                >
                  <View>
                    <Text style={styles.type}>{item.event_type}</Text>
                    <Text style={styles.time}>{formatTime(item.detected_at)}</Text>
                    <Text style={styles.level}>Device #{item.device_id}</Text>
                  </View>
                  <Text style={styles.arrow}>›</Text>
                </TouchableOpacity>
              ))
            )}
          </View>
        )}
      </ScrollView>

      <Modal
        visible={selectedItem !== null}
        animationType="fade"
        transparent={true}
        onRequestClose={closeModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            {selectedItem && (
              <>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>Alert Details</Text>
                  <TouchableOpacity onPress={closeModal}>
                    <Text style={styles.closeText}>Close</Text>
                  </TouchableOpacity>
                </View>

                <View style={styles.detailRow}>
                  <Text style={styles.label}>Type:</Text>
                  <Text style={styles.value}>{selectedItem.event_type}</Text>
                </View>

                <View style={styles.detailRow}>
                  <Text style={styles.label}>Time:</Text>
                  <Text style={styles.value}>
                    {formatTime(selectedItem.detected_at)}
                  </Text>
                </View>

                <View style={styles.detailRow}>
                  <Text style={styles.label}>Device:</Text>
                  <Text style={styles.value}>{selectedItem.device_id}</Text>
                </View>

                <View style={styles.detailRow}>
                  <Text style={styles.label}>Status:</Text>
                  <Text style={styles.value}>{selectedItem.status}</Text>
                </View>

                <View style={styles.audioSection}>
                  <Text style={styles.audioTitle}>Recording</Text>

                  <View style={styles.progressBar}>
                    <View
                      style={[
                        styles.progressFill,
                        {
                          width:
                            playingId === selectedItem.alert_id ? '60%' : '0%',
                        },
                      ]}
                    />
                  </View>

                  <View style={styles.timeRow}>
                    <Text style={styles.timeLabel}>
                      {playingId === selectedItem.alert_id ? 'Playing...' : 'Ready'}
                    </Text>
                    <Text style={styles.timeLabel}>
                      {selectedItem.audio_url ? 'Audio available' : 'No audio'}
                    </Text>
                  </View>

                  <TouchableOpacity
                    style={styles.playButton}
                    onPress={() =>
                      playingId === selectedItem.alert_id
                        ? stopRecording()
                        : playRecording(selectedItem)
                    }
                  >
                    <Text style={styles.playButtonText}>
                      {playingId === selectedItem.alert_id ? 'Stop' : 'Play'}
                    </Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#000000ff',
  },
  scrollContent: {
    flexGrow: 1,
    paddingVertical: 20,
    paddingHorizontal: 15,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
    backgroundColor: '#071d50ff',
    borderBottomWidth: 1,
    borderBottomColor: '#11daabff',
    padding: 15,
    borderRadius: 8,
  },
  headerText: {
    fontSize: 18,
    color: '#11daabff',
    fontWeight: 'bold',
  },
  count: {
    fontSize: 12,
    color: '#aaa',
  },
  loadingWrap: {
    paddingVertical: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  list: {
    flexGrow: 1,
  },
  emptyBox: {
    marginTop: 20,
    padding: 20,
    borderRadius: 8,
    backgroundColor: '#071d50ff',
    borderWidth: 1,
    borderColor: '#11daabff',
    alignItems: 'center',
  },
  emptyText: {
    color: '#fff',
    fontSize: 15,
  },
  item: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    marginTop: 12,
    borderRadius: 8,
    backgroundColor: '#071d50ff',
    borderWidth: 1,
    borderColor: '#11daabff',
  },
  alertItem: {
    backgroundColor: '#11daab22',
  },
  testItem: {
    backgroundColor: '#071d50cc',
  },
  type: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
    marginBottom: 4,
  },
  time: {
    fontSize: 12,
    color: '#ccc',
    marginBottom: 4,
  },
  level: {
    fontSize: 12,
    color: '#11daabff',
  },
  arrow: {
    fontSize: 20,
    color: '#fff',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#000000ff',
    borderWidth: 2,
    borderColor: '#11daabff',
    borderRadius: 10,
    width: '100%',
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#11daabff',
  },
  closeText: {
    color: '#11daabff',
    fontSize: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#071d50ff',
  },
  label: {
    color: '#11daabff',
    fontSize: 16,
  },
  value: {
    color: '#fff',
    fontSize: 16,
    maxWidth: '60%',
    textAlign: 'right',
  },
  audioSection: {
    marginTop: 20,
    padding: 15,
    backgroundColor: '#071d50ff',
    borderRadius: 8,
  },
  audioTitle: {
    color: '#11daabff',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 15,
  },
  progressBar: {
    height: 6,
    backgroundColor: '#222',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 10,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#11daabff',
  },
  timeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 15,
  },
  timeLabel: {
    color: '#aaa',
    fontSize: 14,
  },
  playButton: {
    backgroundColor: '#11daabff',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  playButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '600',
  },
});