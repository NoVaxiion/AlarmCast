import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';

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
      `Time: ${item.time}\nType: ${item.type}\nLevel: ${item.level > 0 ? item.level + ' dB' : 'N/A'}`
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerText}>Alert History</Text>
        <Text style={styles.count}>{history.length} records</Text>
      </View>

      <ScrollView style={styles.list}>
        {history.map(item => (
          <TouchableOpacity
            key={item.id}
            style={styles.item}
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
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#1a1a1a',
    borderBottomWidth: 1,
    borderBottomColor: '#333333',
  },
  headerText: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  count: {
    fontSize: 12,
    color: '#999999',
  },
  list: {
    flex: 1,
  },
  item: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    marginHorizontal: 20,
    marginTop: 12,
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#333333',
  },
  type: {
    fontSize: 14,
    color: '#ffffff',
    fontWeight: '500',
    marginBottom: 4,
  },
  time: {
    fontSize: 12,
    color: '#999999',
    marginBottom: 4,
  },
  level: {
    fontSize: 11,
    color: '#666666',
  },
  arrow: {
    fontSize: 20,
    color: '#666666',
  },
});