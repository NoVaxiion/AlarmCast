import { useState } from 'react';
import {
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface HistoryItem {
  id: string;
  time: string;
  level: number;
  type: string;
  location: string;
  duration: string;
}

export default function History() {
  const [history] = useState<HistoryItem[]>([
    {
      id: '1',
      time: '2025-10-29 14:30',
      level: 85,
      type: 'Alert',
      location: 'Kitchen',
      duration: '00:45',
    },
    {
      id: '2',
      time: '2025-10-29 10:15',
      level: 72,
      type: 'Alert',
      location: 'Bedroom',
      duration: '01:12',
    },
    {
      id: '3',
      time: '2025-10-28 22:08',
      level: 0,
      type: 'Test',
      location: 'Living Room',
      duration: '00:30',
    },
  ]);

  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.headerText}>Alert History</Text>
          <Text style={styles.count}>{history.length} records</Text>
        </View>

        <View style={styles.list}>
          {history.map((item) => (
            <TouchableOpacity
              key={item.id}
              style={[
                styles.item,
                item.type === 'Alert' && styles.alertItem,
                item.type === 'Test' && styles.testItem,
              ]}
              onPress={() => setSelectedItem(item)}
            >
              <View>
                <Text style={styles.type}>{item.type}</Text>
                <Text style={styles.time}>{item.time}</Text>
                {item.level > 0 && <Text style={styles.level}>{item.level} dB</Text>}
              </View>
              <Text style={styles.arrow}>›</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      {/* Detail Modal with Audio Playback */}
      <Modal
        visible={selectedItem !== null}
        animationType="fade"
        transparent={true}
        onRequestClose={() => {
          setSelectedItem(null);
          setIsPlaying(false);
        }}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            {selectedItem && (
              <>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>Alert Details</Text>
                  <TouchableOpacity
                    onPress={() => {
                      setSelectedItem(null);
                      setIsPlaying(false);
                    }}
                  >
                    <Text style={styles.closeText}>Close</Text>
                  </TouchableOpacity>
                </View>

                <View style={styles.detailRow}>
                  <Text style={styles.label}>Type:</Text>
                  <Text style={styles.value}>{selectedItem.type}</Text>
                </View>

                <View style={styles.detailRow}>
                  <Text style={styles.label}>Time:</Text>
                  <Text style={styles.value}>{selectedItem.time}</Text>
                </View>

                <View style={styles.detailRow}>
                  <Text style={styles.label}>Location:</Text>
                  <Text style={styles.value}>{selectedItem.location}</Text>
                </View>

                {selectedItem.level > 0 && (
                  <View style={styles.detailRow}>
                    <Text style={styles.label}>Sound Level:</Text>
                    <Text style={styles.value}>{selectedItem.level} dB</Text>
                  </View>
                )}

                <View style={styles.detailRow}>
                  <Text style={styles.label}>Duration:</Text>
                  <Text style={styles.value}>{selectedItem.duration}</Text>
                </View>

                {/* Audio Playback Section */}
                <View style={styles.audioSection}>
                  <Text style={styles.audioTitle}>Recording</Text>

                  {/* Progress Bar */}
                  <View style={styles.progressBar}>
                    <View
                      style={[styles.progressFill, { width: isPlaying ? '60%' : '0%' }]}
                    />
                  </View>

                  <View style={styles.timeRow}>
                    <Text style={styles.timeLabel}>{isPlaying ? '00:27' : '00:00'}</Text>
                    <Text style={styles.timeLabel}>{selectedItem.duration}</Text>
                  </View>

                  {/* Play/Pause Button */}
                  <TouchableOpacity
                    style={styles.playButton}
                    onPress={() => setIsPlaying(!isPlaying)}
                  >
                    <Text style={styles.playButtonText}>
                      {isPlaying ? 'Pause' : 'Play'}
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
  list: {
    flexGrow: 1,
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
