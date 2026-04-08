import { router } from 'expo-router';
import { useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { setupPushForLoggedInUser } from '../services/notifications';
import { API_BASE } from '../constants/api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);




if (!API_BASE) {
  Alert.alert('Error', 'API base URL is missing');
  setLoading(false);
  return;
}

  const handleLogin = async () => {
    setLoading(true);

    if (email === '0' && password === '0') {
      Alert.alert('Developer Login', 'Bypassed login — going to dashboard.');
      router.replace('/(tabs)');
      setLoading(false);
      return;
    }

    try {
      const username = email.trim();
      const passwordValue = password.trim();

      console.log('LOGIN API_BASE:', API_BASE);
      console.log('LOGIN USERNAME:', username);
      console.log('LOGIN PASSWORD LENGTH:', passwordValue.length);

      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password: passwordValue }),
      });

      const rawText = await response.text();
      console.log('LOGIN STATUS:', response.status);
      console.log('LOGIN RAW RESPONSE:', rawText);

      const data = rawText ? JSON.parse(rawText) : {};

      if (response.ok) {
        console.log('LOGIN OK, user_id:', data.user_id);

        try {
          console.log('STARTING PUSH SETUP');
          const token = await setupPushForLoggedInUser(API_BASE, data.user_id);
          console.log('PUSH SETUP RESULT TOKEN:', token);
        } catch (pushError: any) {
          console.log('PUSH SETUP FAILED:', pushError?.message ?? pushError);
        }

        Alert.alert('Success', 'Login successful!');
        router.replace('/(tabs)');
      } else {
        Alert.alert('Error', data.error || 'Invalid credentials');
      }
    } catch (err: any) {
      console.log('LOGIN FETCH ERROR:', err);
      Alert.alert('Network error', String(err?.message ?? err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.title}>Login</Text>

        <TextInput
          placeholder="Email"
          placeholderTextColor="#aaa"
          value={email}
          onChangeText={setEmail}
          style={styles.input}
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
        />

        <TextInput
          placeholder="Password"
          placeholderTextColor="#aaa"
          value={password}
          onChangeText={setPassword}
          style={styles.input}
          secureTextEntry
          autoCapitalize="none"
          autoCorrect={false}
        />

        <TouchableOpacity style={styles.btn} onPress={handleLogin} disabled={loading}>
          <Text style={styles.btnText}>{loading ? 'Logging in...' : 'Login'}</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => router.push('/register')}>
          <Text style={styles.link}>Don’t have an account? Register</Text>
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
    fontSize: 28,
    color: '#fff',
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 30,
  },
  input: {
    borderWidth: 1,
    borderColor: '#11daabff',
    borderRadius: 8,
    padding: 12,
    marginBottom: 15,
    color: '#fff',
  },
  btn: {
    backgroundColor: '#0d1764ff',
    padding: 15,
    borderRadius: 8,
  },
  btnText: {
    color: '#fff',
    fontWeight: '600',
    textAlign: 'center',
  },
  link: {
    color: '#fff',
    textAlign: 'center',
    marginTop: 20,
  },
});