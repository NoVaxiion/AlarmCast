import { useEffect, useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function Dashboard() {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [soundLevel, setSoundLevel] = useState(0);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isMonitoring) {
      interval = setInterval(() => {
        const level = Math.floor(Math.random() * 100);
        setSoundLevel(level);
      }, 2000);
    } else {
      setSoundLevel(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isMonitoring]);

  const handleStartStop = () => setIsMonitoring(!isMonitoring);
  const handleTest = () =>
    Alert.alert('Test Alert', 'Fire alarm test notification sent.');

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.title}>Dashboard</Text>

        <View style={styles.card}>
          <Text style={styles.label}>Status</Text>
          <Text style={styles.status}>
            {isMonitoring ? 'Monitoring Active' : 'Stopped'}
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>Sound Level</Text>
          <Text style={styles.value}>{soundLevel} dB</Text>
          <View style={styles.bar}>
            <View style={[styles.barFill, { width: `${soundLevel}%` }]} />
          </View>
        </View>

        <TouchableOpacity style={styles.btnPrimary} onPress={handleStartStop}>
          <Text style={styles.btnText}>{isMonitoring ? 'Stop' : 'Start'}</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.btnSecondary} onPress={handleTest}>
          <Text style={styles.btnText}>Test Alert</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#000000ff' },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingVertical: 40,
    paddingHorizontal: 25,
  },
  title: {
    color: '#11daabff',
    fontSize: 26,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  card: {
    backgroundColor: '#071d50ff',
    padding: 20,
    marginBottom: 20,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#11daabff',
  },
  label: { color: '#aaa', fontSize: 14, marginBottom: 8 },
  status: { color: '#fff', fontSize: 18, fontWeight: '500' },
  value: {
    color: '#fff',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
  },
  bar: { height: 8, backgroundColor: '#333', width: '100%', borderRadius: 4 },
  barFill: { height: '100%', backgroundColor: '#11daabff', borderRadius: 4 },
  btnPrimary: {
    backgroundColor: '#11daabff',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10,
  },
  btnSecondary: {
    backgroundColor: '#071d50ff',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  btnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
