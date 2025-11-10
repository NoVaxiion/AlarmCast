import { useState } from 'react';
import {
  Alert,
  Modal,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';

interface Contact {
  id: string;
  name: string;
  phone: string;
}

export default function Settings() {
  const router = useRouter();
  const [notifications, setNotifications] = useState(true);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');

  const addContact = () => {
    if (!name || !phone) {
      Alert.alert('Error', 'Enter name and phone');
      return;
    }
    setContacts([...contacts, { id: Date.now().toString(), name, phone }]);
    setName('');
    setPhone('');
    setShowModal(false);
  };

  const deleteContact = (id: string) => {
    setContacts(contacts.filter((c) => c.id !== id));
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notifications</Text>
          <View style={styles.row}>
            <Text style={styles.label}>Enable Alerts</Text>
            <Switch
              value={notifications}
              onValueChange={setNotifications}
              trackColor={{ false: '#333', true: '#11daabff' }}
              thumbColor={notifications ? '#fff' : '#999'}
            />
          </View>
        </View>

        <View style={styles.section}>
          <View style={styles.header}>
            <Text style={styles.sectionTitle}>Emergency Contacts</Text>
            <TouchableOpacity onPress={() => setShowModal(true)}>
              <Text style={styles.addButton}>Add</Text>
            </TouchableOpacity>
          </View>

          {contacts.map((contact) => (
            <View key={contact.id} style={styles.contactCard}>
              <View>
                <Text style={styles.contactName}>{contact.name}</Text>
                <Text style={styles.contactPhone}>{contact.phone}</Text>
              </View>
              <TouchableOpacity onPress={() => deleteContact(contact.id)}>
                <Text style={styles.deleteText}>Delete</Text>
              </TouchableOpacity>
            </View>
          ))}

          {contacts.length === 0 && (
            <Text style={styles.emptyText}>No contacts added</Text>
          )}
        </View>

        {/* New Section for User Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account</Text>
          <TouchableOpacity
            style={styles.userInfoButton}
            onPress={() => router.push('/userInfo')}
          >
            <Text style={styles.userInfoText}>User Information</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* Add Contact Modal */}
      <Modal
        visible={showModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modal}>
            <Text style={styles.modalTitle}>Add Contact</Text>

            <TextInput
              style={styles.input}
              placeholder="Name"
              placeholderTextColor="#888"
              value={name}
              onChangeText={setName}
            />

            <TextInput
              style={styles.input}
              placeholder="Phone"
              placeholderTextColor="#888"
              keyboardType="phone-pad"
              value={phone}
              onChangeText={setPhone}
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, { backgroundColor: '#071d50ff' }]}
                onPress={() => setShowModal(false)}
              >
                <Text style={styles.buttonText}>Cancel</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.modalButton, { backgroundColor: '#11daabff' }]}
                onPress={addContact}
              >
                <Text style={[styles.buttonText, { color: '#000' }]}>Add</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#000000ff' },
  scrollContent: { flexGrow: 1, padding: 20 },
  section: {
    backgroundColor: '#071d50ff',
    padding: 20,
    marginBottom: 20,
    borderRadius: 8,
    borderColor: '#11daabff',
    borderWidth: 1,
  },
  sectionTitle: {
    fontSize: 18,
    color: '#11daabff',
    fontWeight: 'bold',
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  label: { fontSize: 15, color: '#fff' },
  addButton: { fontSize: 14, color: '#11daabff', textDecorationLine: 'underline' },
  contactCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#000',
    padding: 12,
    marginBottom: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#11daabff',
  },
  contactName: { fontSize: 15, color: '#fff', marginBottom: 4 },
  contactPhone: { fontSize: 13, color: '#aaa' },
  deleteText: { fontSize: 13, color: '#11daabff' },
  emptyText: { fontSize: 13, color: '#888', textAlign: 'center', paddingVertical: 20 },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.9)',
    justifyContent: 'center',
    padding: 20,
  },
  modal: {
    backgroundColor: '#071d50ff',
    padding: 20,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#11daabff',
  },
  modalTitle: {
    fontSize: 20,
    color: '#11daabff',
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
  },
  input: {
    backgroundColor: '#000000ff',
    borderWidth: 1,
    borderColor: '#11daabff',
    padding: 12,
    marginBottom: 12,
    fontSize: 14,
    color: '#fff',
    borderRadius: 8,
  },
  modalButtons: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 12 },
  modalButton: {
    flex: 1,
    padding: 12,
    alignItems: 'center',
    borderRadius: 8,
    marginHorizontal: 5,
  },
  buttonText: { color: '#fff', fontSize: 15, fontWeight: '600' },
  userInfoButton: {
    backgroundColor: '#000',
    padding: 15,
    borderRadius: 8,
    borderColor: '#11daabff',
    borderWidth: 1,
    alignItems: 'center',
  },
  userInfoText: { color: '#11daabff', fontSize: 16, fontWeight: '600' },
});
