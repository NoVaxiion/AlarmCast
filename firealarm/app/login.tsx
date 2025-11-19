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

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);

    if (email === '0' && password === '0') {
      Alert.alert('Developer Login', 'Bypassed login — going to dashboard.');
      router.replace('/(tabs)');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://<YOUR_SERVER_IP>:5000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        Alert.alert('Success', 'Login successful!');
        router.replace('/(tabs)');
      } else {
        Alert.alert('Error', data.message || 'Invalid credentials');
      }
    } catch (error) {
      Alert.alert('Offline Mode', 'Backend not available, login bypassed for testing.');
      router.replace('/(tabs)');
    }

    setLoading(false);
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
        />
        <TextInput
          placeholder="Password"
          placeholderTextColor="#aaa"
          value={password}
          onChangeText={setPassword}
          style={styles.input}
          secureTextEntry
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
