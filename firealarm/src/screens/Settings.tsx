import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Switch,
  Alert,
  TextInput,
  Modal,
} from 'react-native';

interface Contact {
  id: string;
  name: string;
  phone: string;
}

export default function Settings() {
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
    setContacts(contacts.filter(c => c.id !== id));
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        
        {/* Notifications */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notifications</Text>
          
          <View style={styles.row}>
            <Text style={styles.label}>Enable Alerts</Text>
            <Switch
              value={notifications}
              onValueChange={setNotifications}
              trackColor={{ false: '#333333', true: '#666666' }}
              thumbColor={notifications ? '#ffffff' : '#999999'}
            />
          </View>
        </View>

        {/* Emergency Contacts */}
        <View style={styles.section}>
          <View style={styles.header}>
            <Text style={styles.sectionTitle}>Emergency Contacts</Text>
            <TouchableOpacity onPress={() => setShowModal(true)}>
              <Text style={styles.addButton}>Add</Text>
            </TouchableOpacity>
          </View>

          {contacts.map(contact => (
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

      </View>

      {/* Add Modal */}
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
              placeholderTextColor="#666666"
              value={name}
              onChangeText={setName}
            />
            
            <TextInput
              style={styles.input}
              placeholder="Phone"
              placeholderTextColor="#666666"
              keyboardType="phone-pad"
              value={phone}
              onChangeText={setPhone}
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={styles.modalButton}
                onPress={() => setShowModal(false)}
              >
                <Text style={styles.buttonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.modalButton}
                onPress={addContact}
              >
                <Text style={styles.buttonText}>Add</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
  section: {
    backgroundColor: '#1a1a1a',
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#333333',
  },
  sectionTitle: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: 'bold',
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    fontSize: 14,
    color: '#ffffff',
  },
  addButton: {
    fontSize: 14,
    color: '#ffffff',
    textDecorationLine: 'underline',
  },
  contactCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#000000',
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#333333',
  },
  contactName: {
    fontSize: 14,
    color: '#ffffff',
    marginBottom: 4,
  },
  contactPhone: {
    fontSize: 12,
    color: '#999999',
  },
  deleteText: {
    fontSize: 12,
    color: '#999999',
  },
  emptyText: {
    fontSize: 12,
    color: '#666666',
    textAlign: 'center',
    paddingVertical: 20,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    justifyContent: 'center',
    padding: 20,
  },
  modal: {
    backgroundColor: '#1a1a1a',
    padding: 20,
    borderWidth: 1,
    borderColor: '#333333',
  },
  modalTitle: {
    fontSize: 18,
    color: '#ffffff',
    fontWeight: 'bold',
    marginBottom: 20,
  },
  input: {
    backgroundColor: '#000000',
    borderWidth: 1,
    borderColor: '#333333',
    padding: 12,
    marginBottom: 12,
    fontSize: 14,
    color: '#ffffff',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 12,
  },
  modalButton: {
    flex: 1,
    backgroundColor: '#000000',
    padding: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333333',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 14,
  },
});