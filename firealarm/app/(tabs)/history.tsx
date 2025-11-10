import { useState } from 'react';
import {
  Alert,
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
}

export default function History() {
  const [history] = useState<HistoryItem[]>([
    { id: '1', time: '2025-10-29 14:30', level: 85, type: 'Alert' },
    { id: '2', time: '2025-10-29 10:15', level: 72, type: 'Alert' },
    { id: '3', time: '2025-10-28 22:08', level: 0, type: 'Test' },
  ]);

  const viewDetails = (item: HistoryItem) => {
    Alert.alert(
      'Details',
      `Time: ${item.time}\nType: ${item.type}\nLevel: ${
        item.level > 0 ? item.level + ' dB' : 'N/A'
      }`
    );
  };

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
              onPress={() => viewDetails(item)}
            >
              <View>
                <Text style={styles.type}>{item.type}</Text>
                <Text style={styles.time}>{item.time}</Text>
                {item.level > 0 && (
                  <Text style={styles.level}>{item.level} dB</Text>
                )}
              </View>
              <Text style={styles.arrow}>›</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
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
});
