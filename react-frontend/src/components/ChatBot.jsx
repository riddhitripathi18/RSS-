import React, { useState, useRef, useEffect } from 'react';

export default function ChatBot({ activeArticle }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi there! I am DigestBot. Ask me anything about the news.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isOpen]);

  // If the active article changes, optionally notify the user
  useEffect(() => {
    if (activeArticle && isOpen) {
      setMessages(prev => [
        ...prev, 
        { role: 'system_notification', content: `Context switched to: ${activeArticle.title}` }
      ]);
    }
  }, [activeArticle, isOpen]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      // Build history (ignoring system_notification)
      const history = messages.filter(m => m.role === 'user' || m.role === 'assistant');
      
      const payload = {
        topic: activeArticle ? activeArticle.title : "Recent News",
        question: userMsg.content,
        history: history,
        article_id: activeArticle ? activeArticle.id : null
      };

      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer || "Sorry, I couldn't process that." }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'assistant', content: "An error occurred while connecting to the AI." }]);
    } finally {
      setLoading(false);
    }
  };

  const formatText = (text) => {
    if (!text) return { __html: "" };
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    return { __html: formatted };
  };

  return (
    <>
      {/* Floating Action Button */}
      {!isOpen && (
        <button 
          onClick={() => setIsOpen(true)}
          style={{
            position: 'fixed', bottom: '30px', right: '30px',
            width: '60px', height: '60px', borderRadius: '30px',
            backgroundColor: 'var(--primary)', color: 'white',
            border: 'none', boxShadow: 'var(--shadow-hover)',
            cursor: 'pointer', fontSize: '1.5rem',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 1000, transition: 'var(--transition)'
          }}
        >
          💬
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div style={{
          position: 'fixed', bottom: '20px', right: '20px',
          width: '380px', height: '600px',
          backgroundColor: 'var(--surface)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-hover)',
          display: 'flex', flexDirection: 'column',
          zIndex: 1000, border: '1px solid var(--border)',
          overflow: 'hidden'
        }}>
          {/* Header */}
          <div style={{
            padding: '16px', backgroundColor: 'var(--primary)', color: 'white',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <div style={{ fontWeight: '600' }}>
              🤖 DigestBot
              <div style={{ fontSize: '0.75rem', opacity: 0.8, marginTop: '4px' }}>
                {activeArticle ? "Chatting about article" : "Global news context"}
              </div>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '1.25rem' }}
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1, padding: '16px', overflowY: 'auto', backgroundColor: 'var(--bg-color)'
          }}>
            {messages.map((msg, i) => {
              if (msg.role === 'system_notification') {
                return (
                  <div key={i} style={{ textAlign: 'center', margin: '10px 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {msg.content}
                  </div>
                );
              }
              const isUser = msg.role === 'user';
              return (
                <div key={i} style={{
                  display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start',
                  marginBottom: '12px'
                }}>
                  <div style={{
                    maxWidth: '85%', padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: isUser ? 'var(--primary)' : 'var(--surface)',
                    color: isUser ? 'white' : 'var(--text-main)',
                    border: isUser ? 'none' : '1px solid var(--border)',
                    borderBottomRightRadius: isUser ? '4px' : 'var(--radius-md)',
                    borderBottomLeftRadius: isUser ? 'var(--radius-md)' : '4px',
                    fontSize: '0.95rem', lineHeight: '1.5'
                  }}>
                    <div dangerouslySetInnerHTML={formatText(msg.content)} className="formatted-content" />
                  </div>
                </div>
              );
            })}
            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '12px' }}>
                <div style={{
                  padding: '10px 14px', borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--surface)', border: '1px solid var(--border)'
                }}>
                  <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <form onSubmit={handleSend} style={{
            display: 'flex', padding: '12px', borderTop: '1px solid var(--border)', backgroundColor: 'var(--surface)'
          }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask a question..."
              style={{
                flex: 1, padding: '10px', borderRadius: '999px',
                border: '1px solid var(--border)', outline: 'none',
                fontFamily: 'inherit'
              }}
            />
            <button type="submit" disabled={!input.trim() || loading} style={{
              marginLeft: '8px', padding: '10px 16px', borderRadius: '999px',
              backgroundColor: input.trim() && !loading ? 'var(--primary)' : 'var(--border)',
              color: 'white', border: 'none', cursor: input.trim() && !loading ? 'pointer' : 'default',
              transition: 'var(--transition)'
            }}>
              Send
            </button>
          </form>
        </div>
      )}
    </>
  );
}
