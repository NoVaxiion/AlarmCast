import React, { useState } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, SafeAreaView, StatusBar, Platform } from 'react-native';
import Dashboard from './src/screens/Dashboard';
import Settings from './src/screens/Settings';
import History from './src/screens/History';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<'dashboard' | 'settings' | 'history'>('dashboard');

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>FireAlarm</Text>
      </View>

      {/* Content */}
      <View style={styles.content}>
        {currentScreen === 'dashboard' && <Dashboard onNavigate={setCurrentScreen} />}
        {currentScreen === 'settings' && <Settings />}
        {currentScreen === 'history' && <History />}
      </View>

      {/* Bottom Navigation */}
      <View style={styles.bottomNav}>
        <TouchableOpacity
          style={[
            styles.navButton,
            currentScreen === 'dashboard' && styles.navButtonActive,
          ]}
          onPress={() => setCurrentScreen('dashboard')}
        >
          <Text
            style={[
              styles.navButtonText,
              currentScreen === 'dashboard' && styles.navButtonTextActive,
            ]}
          >
            Home
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.navButton,
            currentScreen === 'history' && styles.navButtonActive,
          ]}
          onPress={() => setCurrentScreen('history')}
        >
          <Text
            style={[
              styles.navButtonText,
              currentScreen === 'history' && styles.navButtonTextActive,
            ]}
          >
            History
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.navButton,
            currentScreen === 'settings' && styles.navButtonActive,
          ]}
          onPress={() => setCurrentScreen('settings')}
        >
          <Text
            style={[
              styles.navButtonText,
              currentScreen === 'settings' && styles.navButtonTextActive,
            ]}
          >
            Settings
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
  header: {
    backgroundColor: '#1a1a1a',
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#333333',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  content: {
    flex: 1,
  },
  bottomNav: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    borderTopWidth: 1,
    borderTopColor: '#333333',
    paddingVertical: 8,
  },
  navButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  navButtonActive: {
    borderTopWidth: 2,
    borderTopColor: '#ffffff',
  },
  navButtonText: {
    fontSize: 14,
    color: '#666666',
  },
  navButtonTextActive: {
    color: '#ffffff',
    fontWeight: '600',
  },
});