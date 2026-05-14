<template>
  <div class="ai-chat-panel" :class="{ 'is-collapsed': !isChatOpen }">
    <h3>
      <span>Chatbot AI</span>
    </h3>
    
    <div :style="robotStyle" class="robot-container" @click="toggleChat" title="Zwiń/Rozwiń czat">
      <Vue3Lottie :animationData="robotAnimation" :height="80" :width="80" />
      
      <transition name="pop">
        <div v-if="showHint" class="robot-hint-bubble">
          Kliknij we mnie, aby zadać pytanie.
        </div>
      </transition>
    </div>
    
    <div class="chat-content-wrapper">
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

  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted, onUnmounted, watch } from 'vue'
import robotAnimation from '@/assets/robot.json'

const isChatOpen = ref(false) 
const messages = ref([
  { text: 'Witaj! W czym mogę pomóc?', isBot: true }
])
const userInput = ref('')
const chatHistoryRef = ref(null)
const isTyping = ref(false) 

// --- LOGIKA DYMKA PODPOWIEDZI (HINT BUBBLE) ---
const showHint = ref(false)
let hintInterval = null
let hintTimeout = null

const triggerHint = () => {
  if (isChatOpen.value) return 
  showHint.value = true
  
  hintTimeout = setTimeout(() => {
    showHint.value = false
  }, 7000) 
}

const startHintCycle = () => {
  hintInterval = setInterval(() => {
    triggerHint()
  }, 12000) 
}

const stopHintCycle = () => {
  clearInterval(hintInterval)
  clearTimeout(hintTimeout)
  showHint.value = false
}

watch(isChatOpen, (newVal) => {
  if (newVal) {
    stopHintCycle() 
  } else {
    startHintCycle() 
  }
})

onMounted(() => {
  if (!isChatOpen.value) {
    startHintCycle()
  }
})

onUnmounted(() => {
  stopHintCycle()
})
// ----------------------------------------------

const toggleChat = () => {
  isChatOpen.value = !isChatOpen.value
  if (isChatOpen.value) {
    scrollToBottom() 
  }
}

const robotStyle = computed(() => {
  const robotWidth = 80;

  const openGapLeft = 20; 
  const openGapBottom = 10; 

  const closedLeft = 240; 
  const closedGapBottom = 15; 

  if (isChatOpen.value) {
    return {
      position: 'absolute',
      left: `-${robotWidth + openGapLeft}px`,
      bottom: `${openGapBottom}px`,
      zIndex: 1500,
      cursor: 'pointer',
      transition: 'all 0.5s cubic-bezier(0.25, 1, 0.5, 1)' 
    }
  } else {
    return {
      position: 'absolute',
      left: `${closedLeft}px`,
      bottom: `${closedGapBottom}px`,
      zIndex: 1500,
      cursor: 'pointer',
      transition: 'all 0.5s cubic-bezier(0.25, 1, 0.5, 1)'
    }
  }
})

const scrollToBottom = async () => {
  await nextTick()
  if (chatHistoryRef.value) {
    chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
  }
}

const formatMessage = (text) => text.replace(/\n/g, '<br>')

const sendMessage = async () => {
  const text = userInput.value.trim()
  if (!text || isTyping.value) return 

  messages.value.push({ text: text, isBot: false })
  userInput.value = ''
  isTyping.value = true 
  
  if (!isChatOpen.value) isChatOpen.value = true
  
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
.ai-chat-panel {
  position: relative; 
  overflow: visible !important; 
  transition: flex 0.4s cubic-bezier(0.25, 1, 0.5, 1), min-height 0.4s cubic-bezier(0.25, 1, 0.5, 1);
}

.is-collapsed {
  flex: 0 0 0px !important; 
  min-height: 0px !important;
}

.chat-header {
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;
  transition: background-color 0.2s ease;
}

.chat-header:hover {
  background-color: #006b35; 
}

.robot-container {
  transition: transform 0.2s ease;
}

.robot-container:hover {
  transform: scale(1.1); 
}

.robot-container:active {
  transform: scale(0.95);
}

/* --- PROFESJONALNY DYMEK Z PODPOWIEDZIĄ --- */
.robot-hint-bubble {
  position: absolute;
  /* Pozycjonowanie: Lewy-górny róg względem robota */
  bottom: 85px; 
  right: 55px; 
  background-color: #e3f2fd; /* Jasnoniebieski */
  color: #0d47a1; /* Ciemnoniebieski tekst dla kontrastu */
  padding: 10px 14px;
  border-radius: 8px; /* Mniejsze zaokrąglenie wygląda bardziej technicznie/nowocześnie */
  border: 1px solid #bbdefb;
  font-size: 13px;
  white-space: nowrap;
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
  pointer-events: none;
  /* Punkt zaczepienia animacji na ogonku dymka */
  transform-origin: bottom right; 
}

/* Ogon (trójkąt) dymka skierowany w prawy-dół (w stronę robota) */
.robot-hint-bubble::after {
  content: '';
  position: absolute;
  top: 100%;
  right: 15px; /* Odsunięcie od prawej krawędzi dymka */
  border-top: 10px solid #e3f2fd;
  border-left: 10px solid transparent;
}

/* Obramowanie ogonka (zgrane z borderem dymka) */
.robot-hint-bubble::before {
  content: '';
  position: absolute;
  top: 100%;
  right: 14px; /* Przesunięcie o 1px dla stworzenia cienkiej obwódki */
  border-top: 11px solid #bbdefb;
  border-left: 11px solid transparent;
  z-index: -1;
}

/* Animacja (Transition) - dymek "wyrasta" z prawej strony od dołu */
.pop-enter-active,
.pop-leave-active {
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: scale(0.5) translate(10px, 10px);
}
/* --------------------------------------------- */

.chat-content-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden; 
  opacity: 1;
  transition: opacity 0.3s ease;
}

.is-collapsed .chat-content-wrapper {
  opacity: 0;
  pointer-events: none;
}

.btn-disabled {
  background-color: #6e6e6e !important;
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

.chat-input-area {
  display: flex;
  padding: 10px;
  background-color: #eee;
  border-top: 1px solid #ccc;
  align-items: center; 
}

#chat-input {
  flex: 1;
  height: 40px;
  padding: 0 16px; 
  border: 1px solid #ccc;
  border-radius: 20px; 
  font-family: inherit;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s ease;
}

#chat-input:focus {
  border-color: #004d26; 
}

#btn-send-chat {
  margin-left: 10px;
  background-color: #004d26;
  border: none;
  border-radius: 50%; 
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0; 
  transition: background-color 0.2s ease, transform 0.1s ease;
}

#btn-send-chat:hover:not(.btn-disabled) {
  background-color: #006b35; 
}

#btn-send-chat:active:not(.btn-disabled) {
  transform: scale(0.95); 
}

#btn-send-chat svg {
  margin-left: 2px; 
}
</style>