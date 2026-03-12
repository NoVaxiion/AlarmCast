import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';

interface DashboardProps {
  onNavigate: (screen: 'dashboard' | 'settings' | 'history') => void;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [soundLevel, setSoundLevel] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
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

  const handleStartStop = () => {
    setIsMonitoring(!isMonitoring);
  };

  const handleTest = () => {
    Alert.alert('Test Alert', 'Fire alarm test notification sent.');
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        
        {/* Status */}
        <View style={styles.card}>
          <Text style={styles.label}>Status</Text>
          <Text style={styles.status}>
            {isMonitoring ? 'Monitoring Active' : 'Stopped'}
          </Text>
        </View>

        {/* Sound Level */}
        <View style={styles.card}>
          <Text style={styles.label}>Sound Level</Text>
          <Text style={styles.value}>{soundLevel} dB</Text>
          
          <View style={styles.bar}>
            <View style={[styles.barFill, { width: `${soundLevel}%` }]} />
          </View>
        </View>

        {/* Buttons */}
        <TouchableOpacity 
          style={styles.button} 
          onPress={handleStartStop}
        >
          <Text style={styles.buttonText}>
            {isMonitoring ? 'Stop' : 'Start'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.button} 
          onPress={handleTest}
        >
          <Text style={styles.buttonText}>Test Alert</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.button} 
          onPress={() => onNavigate('history')}
        >
          <Text style={styles.buttonText}>View History</Text>
        </TouchableOpacity>

      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  content: {
    padding: 20,
  },
  card: {
    backgroundColor: '#1a1a1a',
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#333333',
  },
  label: {
    fontSize: 14,
    color: '#999999',
    marginBottom: 8,
  },
  status: {
    fontSize: 18,
    color: '#ffffff',
    fontWeight: '500',
  },
  value: {
    fontSize: 32,
    color: '#ffffff',
    fontWeight: 'bold',
    marginBottom: 16,
  },
  bar: {
    height: 8,
    backgroundColor: '#333333',
    width: '100%',
  },
  barFill: {
    height: '100%',
    backgroundColor: '#ffffff',
  },
  button: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333333',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '500',
  },
});