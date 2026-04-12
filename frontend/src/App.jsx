import { useState, useRef, useEffect } from 'react'

function App() {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hi! I am the AutoStream Assistant. How can I help you today?' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [threadId] = useState(() => Math.random().toString(36).substring(7))
  
  // AI Insights State
  const [intent, setIntent] = useState('—')
  const [missingFields, setMissingFields] = useState(['name', 'email', 'platform'])
  const [leadCaptured, setLeadCaptured] = useState(false)
  const [leadDetails, setLeadDetails] = useState({ name: '', email: '', platform: '' })

  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMsg = input
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }])
    setInput('')
    setIsLoading(true)

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, thread_id: threadId })
      })

      const data = await response.json()
      
      setMessages(prev => [...prev, { sender: 'bot', text: data.message }])
      
      // Update Insights
      setIntent(data.intent)
      setMissingFields(data.missing_fields)
      setLeadCaptured(data.is_lead_captured)
      setLeadDetails({
        name: data.name || '',
        email: data.email || '',
        platform: data.platform || ''
      })

    } catch (error) {
      console.error(error)
      setMessages(prev => [...prev, { sender: 'bot', text: 'Sorry, I am having trouble connecting to the server.' }])
    } finally {
      setIsLoading(false)
    }
  }

  const isFieldCompleted = (field) => !missingFields.includes(field) && (leadCaptured || intent === 'high_intent' || leadDetails[field])

  return (
    <div className="app-container">
      
      {/* Chat Section */}
      <div className="panel chat-section">
        <div className="chat-header">
          <div style={{ fontSize: '1.5rem' }}>✨</div>
          <div>
            <h1>AutoStream Agent</h1>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Powered by LangGraph</div>
          </div>
        </div>
        
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.sender}`}>
              {msg.text}
            </div>
          ))}
          {isLoading && (
            <div className="typing-indicator">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="chat-input-area">
          <form className="chat-form" onSubmit={handleSubmit}>
            <input 
              type="text" 
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about pricing, features, or sign up..."
              disabled={isLoading}
            />
            <button type="submit" className="send-btn" disabled={isLoading || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      </div>

      {/* Insights Section */}
      <div className="panel insights-section">
        <div className="insights-header">
          <h2><span style={{ fontSize: '1.2rem' }}>🧠</span> Live AI Insights</h2>
        </div>
        
        <div className="insights-content">
          <div className="insight-card">
            <h3>Current State & Intent</h3>
            <div className="insight-value">
              <div className="pulse"></div>
              {intent === 'greeting' && 'Casual Conversing'}
              {intent === 'product_query' && 'RAG / Knowledge Retrieval Active'}
              {intent === 'high_intent' && 'Lead Qualification Active'}
              {intent === '—' && 'Waiting for input...'}
            </div>
          </div>

          <div className="insight-card">
            <h3>Lead Qualification Checklist</h3>
            <ul className="checklist">
              <li className={`check-item ${isFieldCompleted('name') ? 'completed' : ''}`}>
                <div className="check-circle">{isFieldCompleted('name') ? '✓' : ''}</div>
                Name {leadDetails.name && `(${leadDetails.name})`}
              </li>
              <li className={`check-item ${isFieldCompleted('email') ? 'completed' : ''}`}>
                <div className="check-circle">{isFieldCompleted('email') ? '✓' : ''}</div>
                Email {leadDetails.email && `(${leadDetails.email})`}
              </li>
              <li className={`check-item ${isFieldCompleted('platform') ? 'completed' : ''}`}>
                <div className="check-circle">{isFieldCompleted('platform') ? '✓' : ''}</div>
                Creator Platform {leadDetails.platform && `(${leadDetails.platform})`}
              </li>
            </ul>
          </div>

          {leadCaptured && (
            <div className="success-banner">
              <h4>🎉 Tool Executed</h4>
              <p>mock_lead_capture() called successfully</p>
            </div>
          )}
        </div>
      </div>

    </div>
  )
}

export default App
