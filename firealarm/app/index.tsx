import { useRouter } from 'expo-router';
import { StyleSheet, Text, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function HomeScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <Text style={styles.title}>AlarmCast</Text>

      <TouchableOpacity
        style={styles.loginBtn}
        onPress={() => router.push('/login')}
      >
        <Text style={styles.loginText}>Login</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.registerBtn}
        onPress={() => router.push('/register')}
      >
        <Text style={styles.registerText}>Register</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000ff',
    paddingHorizontal: 25,
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#11daabff',
    marginBottom: 50,
    textAlign: 'center',
  },
  loginBtn: {
    backgroundColor: '#11daabff',
    paddingVertical: 15,
    paddingHorizontal: 70,
    borderRadius: 10,
    marginBottom: 20,
  },
  loginText: {
    color: '#000',
    fontSize: 18,
    fontWeight: '600',
  },
  registerBtn: {
    borderColor: '#11daabff',
    borderWidth: 2,
    paddingVertical: 15,
    paddingHorizontal: 65,
    borderRadius: 10,
  },
  registerText: {
    color: '#11daabff',
    fontSize: 18,
    fontWeight: '600',
  },
});
