import React, { useState, useRef, useEffect, type ChangeEvent, type FormEvent } from "react";

type Message = {
  sender: "user" | "agent";
  text: string;
};

const ChatBox: React.FC = () => {
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState("");

  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on messages update
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setChatInput(e.target.value);
  };

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    setStatus("Sending...");
    // Display user message immediately
    setMessages((prev) => [...prev, { sender: "user", text: chatInput }]);
    const userMessage = chatInput;
    setChatInput("");

    // can pass in thread id here 
    try {
      const res = await fetch("http://127.0.0.1:5000/submit-ticket", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.statusText}`);
      }

      const data = await res.json();
      // Assume response format is { response: string }
      setMessages((prev) => [...prev, { sender: "agent", text: data.response }]);
      setStatus("");
    } catch (error) {
      setStatus("Error sending message");
    }
  };

  return (
    <div style={{ width: 400, margin: "auto" }}>
      <div
        ref={scrollRef}
        style={{
          height: 350,
          overflowY: "auto",
          border: "1px solid #ccc",
          padding: 10,
          marginBottom: 10,
          borderRadius: 5,
          backgroundColor: "#f9f9f9",
          fontFamily: "Arial, sans-serif"
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              textAlign: msg.sender === "user" ? "right" : "left",
              marginBottom: "8px"
            }}
          >
            <span
              style={{
                display: "inline-block",
                padding: "8px 12px",
                borderRadius: 16,
                backgroundColor: msg.sender === "user" ? "#007bff" : "#e5e5ea",
                color: msg.sender === "user" ? "white" : "black",
                maxWidth: "75%",
                wordWrap: "break-word"
              }}
            >
              {msg.text}
            </span>
          </div>
        ))}
      </div>

      <form onSubmit={handleSend}>
        <textarea
          rows={3}
          style={{ width: "100%", padding: 8, fontSize: 14, boxSizing: "border-box" }}
          placeholder="Type your message..."
          value={chatInput}
          onChange={handleInputChange}
          disabled={status === "Sending..."}
        />
        <button type="submit" style={{ marginTop: 8, width: "100%", padding: 10, fontSize: 16 }}>
          Send
        </button>
      </form>

      {status && <div style={{ marginTop: 10, textAlign: "center", color: "red" }}>{status}</div>}
    </div>
  );
};

export default ChatBox;

