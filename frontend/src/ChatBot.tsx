import React, { useState, useRef, useEffect, type ChangeEvent, type FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./ChatBot.css";

type Message = {
  sender: "user" | "agent";
  text: string;
};

function isPdfMsg(text: string) {
  return text.startsWith("📄 Uploaded file:") || text.match(/\.pdf\*\*/i);
}

const ChatBot: React.FC = () => {
  const [chatInput, setChatInput] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => setChatInput(e.target.value);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setPdfFile(e.target.files && e.target.files.length > 0 ? e.target.files[0] : null);
  };

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() && !pdfFile) {
      setStatus("Please enter a message or upload a PDF.");
      return;
    }
    setStatus("Sending...");
    if (chatInput.trim()) {
      setMessages((prev) => [...prev, { sender: "user", text: chatInput }]);
    }
    if (pdfFile) {
      setMessages((prev) => [
        ...prev,
        { sender: "user", text: `📄 Uploaded file: **${pdfFile.name}**` }
      ]);
    }
    const formData = new FormData();
    formData.append("message", chatInput);
    if (pdfFile) formData.append("pdf", pdfFile);
    try {
      const res = await fetch("http://127.0.0.1:5000/submit-ticket", {
        method: "POST",
        body: formData
      });
      if (!res.ok) throw new Error(`Server error: ${res.statusText}`);
      const data = await res.json();
      setMessages((prev) => [...prev, { sender: "agent", text: data.response }]);
      setChatInput("");
      setPdfFile(null);
      setStatus("");
    } catch (error) {
      setStatus("Error sending message");
    }
  };

  return (
    <div className="app-root">
      <div className="chatbot-container">
        <div ref={scrollRef} className="chatbot-messages">
          {messages.map((msg, idx) => (
            <div key={idx} style={{ textAlign: msg.sender === "user" ? "right" : "left" }}>
              <div className={
                isPdfMsg(msg.text)
                  ? "chatbot-bubble file"
                  : `chatbot-bubble ${msg.sender}`
              }>
                {msg.sender === "agent"
                  ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                  : <span>{msg.text}</span>}
              </div>
            </div>
          ))}
        </div>
        <form className="chatbot-form" onSubmit={handleSend}>
          <textarea
            rows={3}
            className="chatbot-textarea"
            placeholder="Type your message here..."
            value={chatInput}
            onChange={handleInputChange}
            disabled={status === "Sending..."}
          />
          <div className="chatbot-controls">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              disabled={status === "Sending..."}
            />
            <button type="submit" className="chatbot-send-btn" disabled={status === "Sending..."}>
              Send
            </button>
          </div>
        </form>
        {status && <div className="chatbot-status">{status}</div>}
      </div>
    </div>
  );
};

export default ChatBot;

