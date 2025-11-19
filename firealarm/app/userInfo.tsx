import { SafeAreaView } from 'react-native-safe-area-context';
import { StyleSheet, Text, View } from 'react-native';

export default function UserInfo() {
  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <View style={styles.container}>
        <Text style={styles.title}>User Information</Text>

        <View style={styles.infoBox}>
          <Text style={styles.label}>Name:</Text>
          <Text style={styles.value}>John cl</Text>

          <Text style={styles.label}>Email:</Text>
          <Text style={styles.value}>ss@gmail.com</Text>

          <Text style={styles.label}>Phone:</Text>
          <Text style={styles.value}>+1 (860) 567-8901</Text>

          <Text style={styles.label}>Member/Owner</Text>
          <Text style={styles.value}>Owner</Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#000000ff' },
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  title: { color: '#11daabff', fontSize: 24, fontWeight: 'bold', marginBottom: 30 },
  infoBox: {
    backgroundColor: '#071d50ff',
    borderWidth: 1,
    borderColor: '#11daabff',
    borderRadius: 10,
    padding: 20,
    width: '100%',
  },
  label: { color: '#11daabff', fontSize: 16, marginTop: 10 },
  value: { color: '#fff', fontSize: 16, marginTop: 4 },
});
