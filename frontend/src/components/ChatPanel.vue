<template>
  <div class="ai-chat-panel">
    <h3>Chatbot AI</h3>
    
    <div class="chat-messages" ref="chatHistoryRef">
      <div v-for="(msg, index) in messages" :key="index" 
           :class="['message', msg.isBot ? 'ai-message' : 'user-message']">
        <span style="white-space: pre-wrap;" v-html="formatMessage(msg.text)"></span>
      </div>

      <div v-if="isTyping" class="message ai-message typing-indicator">
        <span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
      </div>
    </div>
    
    <div class="chat-input-area">
      <input type="text" v-model="userInput" @keyup.enter="sendMessage" placeholder="Napisz wiadomość..." :disabled="isTyping" id="chat-input">
      <button id="btn-send-chat" @click="sendMessage" :disabled="isTyping" :class="{ 'btn-disabled': isTyping }">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="white"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path></svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const messages = ref([
  { text: 'Cześć, jestem Chatbotem Geoportalu Zagrożenia Powodziowego😊. W czym mogę Ci pomóc?', isBot: true }
])
const userInput = ref('')
const chatHistoryRef = ref(null)
const isTyping = ref(false) 

const scrollToBottom = async () => {
  await nextTick()
  if (chatHistoryRef.value) {
    chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
  }
}

// Bezpieczne formatowanie tekstu z Markdown (zastępuje \n na <br>)
const formatMessage = (text) => text.replace(/\n/g, '<br>')

const sendMessage = async () => {
  const text = userInput.value.trim()
  if (!text || isTyping.value) return 

  messages.value.push({ text: text, isBot: false })
  userInput.value = ''
  isTyping.value = true 
  await scrollToBottom()

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }) 
    })

    if (!response.ok) throw new Error(`Błąd HTTP: ${response.status}`)
    const data = await response.json()

    if (data.status === 'success') {
      messages.value.push({ text: data.response, isBot: true })
    } else {
      messages.value.push({ text: `Błąd analizy: ${data.message}`, isBot: true })
    }

  } catch (error) {
    console.error("Błąd połączenia API:", error)
    messages.value.push({ text: `Błąd komunikacji z serwerem. Upewnij się, że kontenery działają. (${error.message})`, isBot: true })
  } finally {
    isTyping.value = false 
    await scrollToBottom()
  }
}
</script>

<style scoped>
.btn-disabled {
  background-color: #8bb4e6 !important;
  cursor: not-allowed !important;
}

.typing-indicator {
  font-size: 20px;
  line-height: 1;
  padding: 8px 12px;
  width: fit-content;
}
.dot {
  animation: blink 1.4s infinite both;
  font-weight: bold;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0% { opacity: 0.2; }
  20% { opacity: 1; }
  100% { opacity: 0.2; }
}

/* Nadpisanie domyślnego inputa, by wyglądał jak na Twoim oryginalnym designie */
#chat-input {
  flex: 1;
  height: 40px;
  padding: 0 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-family: inherit;
  font-size: 13px;
  outline: none;
}
#btn-send-chat {
  margin-left: 10px;
  background-color: #004d26;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 40px;
  height: 40px;
}
</style>