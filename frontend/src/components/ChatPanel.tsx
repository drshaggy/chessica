import { useState, useRef, useEffect } from 'react'
import { api } from '../api'

interface Message {
  role: 'user' | 'ai'
  content: string
}

interface Props {
  gameId: string
  disabled?: boolean
}

export default function ChatPanel({ gameId, disabled }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', content: "Ask me anything about the position — plans, tactics, opening theory, or what I'm thinking." }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || loading || disabled) return

    setInput('')
    setMessages(m => [...m, { role: 'user', content: text }])
    setLoading(true)

    try {
      const res = await api.chat(gameId, text)
      setMessages(m => [...m, { role: 'ai', content: res.response }])
    } catch (e) {
      setMessages(m => [...m, { role: 'ai', content: 'Sorry, something went wrong. Try again.' }])
    } finally {
      setLoading(false)
    }
  }

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col p-3 gap-3">
      <div className="flex-1 min-h-0 overflow-y-auto space-y-3 pr-1">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.role === 'ai' && (
              <div className="w-6 h-6 rounded-full bg-amber-500 flex items-center justify-center text-xs text-gray-900 font-bold shrink-0 mt-0.5">
                AI
              </div>
            )}
            <div className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
              m.role === 'user'
                ? 'bg-gray-700 text-gray-100'
                : 'bg-gray-800 text-gray-200 border border-gray-700'
            }`}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2 justify-start">
            <div className="w-6 h-6 rounded-full bg-amber-500 flex items-center justify-center text-xs text-gray-900 font-bold shrink-0">
              AI
            </div>
            <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2">
              <span className="text-amber-400 text-sm animate-pulse">Thinking…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="shrink-0 flex gap-2">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder="Ask about the position…"
          disabled={disabled || loading}
          rows={2}
          className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-amber-500 resize-none disabled:opacity-50"
        />
        <button
          onClick={send}
          disabled={!input.trim() || loading || disabled}
          className="px-3 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed text-gray-900 font-semibold rounded text-sm self-end"
        >
          Send
        </button>
      </div>
    </div>
  )
}
