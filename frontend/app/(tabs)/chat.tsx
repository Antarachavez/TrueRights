import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, ScrollView, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import Animated, { FadeIn, FadeInUp } from 'react-native-reanimated';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [deviceId, setDeviceId] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [userState, setUserState] = useState<string | null>(null);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    initializeChat();
  }, []);

  const initializeChat = async () => {
    try {
      let storedDeviceId = await AsyncStorage.getItem('device_id');
      if (!storedDeviceId) {
        storedDeviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await AsyncStorage.setItem('device_id', storedDeviceId);
      }
      setDeviceId(storedDeviceId);

      const newSessionId = `session_${Date.now()}`;
      setSessionId(newSessionId);

      const storedState = await AsyncStorage.getItem('user_state');
      setUserState(storedState);

      // Add welcome message
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: `Hi! I'm here to help you understand your rights. Ask me about:\n\n• School searches and policies\n• Workplace rights\n• Housing and tenant issues\n• Police interactions\n• Online privacy\n• Public spaces\n\nRemember: I provide educational info, not legal advice. What's on your mind?`,
        timestamp: new Date(),
      }]);
    } catch (error) {
      console.error('Error initializing chat:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/chat`, {
        device_id: deviceId,
        session_id: sessionId,
        message: userMessage.content,
        user_state: userState,
      });

      const assistantMessage: Message = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: "I'm having trouble connecting right now. Please try again in a moment.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    const newSessionId = `session_${Date.now()}`;
    setSessionId(newSessionId);
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: `Chat cleared! I'm ready to help you understand your rights. What would you like to know?`,
      timestamp: new Date(),
    }]);
  };

  useEffect(() => {
    scrollViewRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  const QuickQuestion = ({ text }: { text: string }) => (
    <TouchableOpacity 
      style={styles.quickQuestion}
      onPress={() => setInputText(text)}
    >
      <Text style={styles.quickQuestionText}>{text}</Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView 
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.headerTitle}>Ask AI</Text>
            <Text style={styles.headerSubtitle}>Rights education assistant</Text>
          </View>
          <TouchableOpacity style={styles.clearButton} onPress={clearChat}>
            <Ionicons name="refresh" size={20} color="#5E6E7D" />
          </TouchableOpacity>
        </View>

        {/* Messages */}
        <ScrollView 
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
        >
          {messages.map((message, index) => (
            <Animated.View 
              key={message.id}
              entering={FadeInUp.duration(300)}
              style={[
                styles.messageBubble,
                message.role === 'user' ? styles.userBubble : styles.assistantBubble
              ]}
            >
              {message.role === 'assistant' && (
                <View style={styles.assistantIcon}>
                  <Ionicons name="shield-checkmark" size={16} color="#E8A5A5" />
                </View>
              )}
              <Text style={[
                styles.messageText,
                message.role === 'user' ? styles.userText : styles.assistantText
              ]}>
                {message.content}
              </Text>
            </Animated.View>
          ))}
          
          {isLoading && (
            <View style={[styles.messageBubble, styles.assistantBubble]}>
              <ActivityIndicator size="small" color="#E8A5A5" />
              <Text style={styles.thinkingText}>Thinking...</Text>
            </View>
          )}

          {messages.length <= 1 && (
            <View style={styles.quickQuestionsContainer}>
              <Text style={styles.quickQuestionsTitle}>Try asking:</Text>
              <QuickQuestion text="Can my school search my phone?" />
              <QuickQuestion text="What do I say if police stop me?" />
              <QuickQuestion text="Can my boss make me work unpaid?" />
              <QuickQuestion text="Can my landlord enter without notice?" />
            </View>
          )}
        </ScrollView>

        {/* Input */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            placeholder="Ask about your rights..."
            placeholderTextColor="#94A3B8"
            value={inputText}
            onChangeText={setInputText}
            multiline
            maxLength={500}
          />
          <TouchableOpacity 
            style={[styles.sendButton, (!inputText.trim() || isLoading) && styles.sendButtonDisabled]}
            onPress={sendMessage}
            disabled={!inputText.trim() || isLoading}
          >
            <Ionicons name="send" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        </View>

        {/* Disclaimer */}
        <View style={styles.disclaimerBar}>
          <Text style={styles.disclaimerText}>Educational info only • Not legal advice</Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F0EB',
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#EDE9E3',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: "#1B2A4A",
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#5E6E7D',
    marginTop: 2,
  },
  clearButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFDF9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 20,
  },
  messageBubble: {
    maxWidth: '85%',
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
  },
  userBubble: {
    backgroundColor: '#E8A5A5',
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#FFFDF9',
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  assistantIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#1B2A4A20',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  userText: {
    color: "#FFFFFF",
  },
  assistantText: {
    color: '#374151',
  },
  thinkingText: {
    color: '#5E6E7D',
    marginLeft: 8,
    fontSize: 14,
  },
  quickQuestionsContainer: {
    marginTop: 20,
  },
  quickQuestionsTitle: {
    fontSize: 14,
    color: '#5E6E7D',
    marginBottom: 12,
  },
  quickQuestion: {
    backgroundColor: '#FFFDF9',
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  quickQuestionText: {
    color: '#374151',
    fontSize: 14,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#EDE9E3',
    backgroundColor: '#F5F0EB',
  },
  textInput: {
    flex: 1,
    backgroundColor: '#FFFDF9',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: '#1B2A4A',
    fontSize: 15,
    maxHeight: 100,
    marginRight: 12,
    borderWidth: 1,
    borderColor: '#EDE9E3',
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#C45C5C',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#E2E8F0',
  },
  disclaimerBar: {
    paddingVertical: 8,
    alignItems: 'center',
    backgroundColor: '#F5F0EB',
  },
  disclaimerText: {
    fontSize: 11,
    color: '#94A3B8',
  },
});
