import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { API_BASE } from '../../constants/api';
const HUB_ID = 1;

type AlertItem = {
  alert_id: number;
  hub_id: number;
  device_event_id: number;
  device_id: number;
  status: string;
  event_type: string;
  detected_at: string;
};

export default function Dashboard() {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [activeDevices, setActiveDevices] = useState(0);
  const [lastAlarm, setLastAlarm] = useState<AlertItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = useCallback(async (showLoader = true) => {
    try {
      if (showLoader) setLoading(true);

      const [statusRes, alertsRes] = await Promise.all([
        fetch(`${API_BASE}/api/hubs/${HUB_ID}/monitoring/status`),
        fetch(`${API_BASE}/api/hubs/${HUB_ID}/alerts?limit=1`),
      ]);

      if (!statusRes.ok) {
        throw new Error('Failed to load monitoring status');
      }

      if (!alertsRes.ok) {
        throw new Error('Failed to load alert history');
      }

      const statusData = await statusRes.json();
      const alertsData = await alertsRes.json();

      setIsMonitoring(statusData.is_monitoring ?? false);
      setActiveDevices(statusData.active_devices ?? 0);
      setLastAlarm(Array.isArray(alertsData) && alertsData.length > 0 ? alertsData[0] : null);
    } catch (error) {
      console.log('Dashboard fetch error:', error);
      if (showLoader) {
        Alert.alert('Error', 'Could not load dashboard data.');
      }
    } finally {
      if (showLoader) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData(true);

    const interval = setInterval(() => {
      fetchDashboardData(false);
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  const onRefresh = async () => {
    try {
      setRefreshing(true);
      await fetchDashboardData(false);
    } finally {
      setRefreshing(false);
    }
  };

  const handleStartStop = async () => {
    try {
      const endpoint = isMonitoring ? 'stop' : 'start';

      const res = await fetch(
        `${API_BASE}/api/hubs/${HUB_ID}/monitoring/${endpoint}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.error || `Failed to ${endpoint} monitoring`);
      }

      await fetchDashboardData(false);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Could not update monitoring status.');
    }
  };

  const handleTest = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/hubs/${HUB_ID}/test-alert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.error || 'Failed to send test alert');
      }

      Alert.alert('Success', 'Test alert notification sent.');
      await fetchDashboardData(false);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Could not send test alert.');
    }
  };

  const formatDateTime = (value?: string) => {
  if (!value) return 'N/A';

  const date = new Date(value);
  if (isNaN(date.getTime())) return value;

  return date.toLocaleString('en-US', {
    timeZone: 'America/New_York',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#11daabff" />
        }
      >
        <Text style={styles.title}>Dashboard</Text>

        <View style={styles.card}>
          <Text style={styles.label}>Monitoring Status</Text>
          <Text style={styles.status}>
            {loading
              ? 'Loading...'
              : isMonitoring
              ? 'Monitoring Active'
              : 'Monitoring Stopped'}
          </Text>
          <Text style={styles.subText}>
            Active Devices: {loading ? '...' : activeDevices}
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>Last Alarm Recorded</Text>
          {loading ? (
            <Text style={styles.subText}>Loading...</Text>
          ) : lastAlarm ? (
            <>
              <Text style={styles.alarmType}>{lastAlarm.event_type}</Text>
              <Text style={styles.subText}>Device ID: {lastAlarm.device_id}</Text>
              <Text style={styles.subText}>Status: {lastAlarm.status}</Text>
              <Text style={styles.subText}>
                Detected: {formatDateTime(lastAlarm.detected_at)}
              </Text>
            </>
          ) : (
            <Text style={styles.subText}>No alarms recorded yet</Text>
          )}
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>Note</Text>
          <Text style={styles.subText}>
            This currently shows monitoring status and latest recorded alert.
          </Text>
          <Text style={styles.subText}>
          </Text>
        </View>

        <TouchableOpacity style={styles.btnPrimary} onPress={handleStartStop}>
          <Text style={styles.btnText}>
            {isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.btnSecondary} onPress={handleTest}>
          <Text style={styles.btnText}>Send Test Alert</Text>
        </TouchableOpacity>
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
  label: {
    color: '#aaa',
    fontSize: 14,
    marginBottom: 8,
  },
  status: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 8,
  },
  alarmType: {
    color: '#11daabff',
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  subText: {
    color: '#ddd',
    fontSize: 15,
    marginBottom: 4,
  },
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
    borderWidth: 1,
    borderColor: '#11daabff',
  },
  btnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});