import React, { useState, useRef, useEffect, type ChangeEvent, type FormEvent } from "react";

type Message = {
  sender: "user" | "agent";
  text: string;
};

const ChatBox: React.FC = () => {
  const [chatInput, setChatInput] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
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

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0){
      setPdfFile(e.target.files[0]);
    } else {
      setPdfFile(null);
    }
  }
  

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();

    // Require either message or PDF
    if (!chatInput.trim() && !pdfFile) {
      setStatus("Please enter a message or upload a PDF.");
      return;
    }

    setStatus("Sending...");

    // Show user message immediately if present
    if (chatInput.trim()) {
      setMessages((prev) => [...prev, { sender: "user", text: chatInput }]);
    }
    if (pdfFile) {
      setMessages((prev) => [
        ...prev,
        { sender: "user", text: `📄 Uploaded file: ${pdfFile.name}` }
      ]);
    }

    const formData = new FormData();
    formData.append("message", chatInput);
    if (pdfFile) {
      formData.append("pdf", pdfFile);
    }

    try {
      const res = await fetch("http://127.0.0.1:5000/submit-ticket", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.statusText}`);
      }

      const data = await res.json();
      // Add agent response message
      setMessages((prev) => [...prev, { sender: "agent", text: data.response }]);
      setChatInput("");
      setPdfFile(null);
      setStatus("");
    } catch (error) {
      setStatus("Error sending message");
    }
  };

  return (
    <div style={{ width: 600, margin: "auto" }}>
      <div
        ref={scrollRef}
        style={{
          height: 700,
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
          style={{ width: "100%", height: 150, padding: 8, fontSize: 14, boxSizing: "border-box" }}
          placeholder="Type your message..."
          value={chatInput}
          onChange={handleInputChange}
          disabled={status === "Sending..."}
        />
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          disabled={status === "Sending..."}
          style={{ marginTop: 8 }}
        />
        <button type="submit" style={{ marginTop: 8, width: "100%", padding: 10, fontSize: 16 }}>
          Send
        </button>
      </form>

      {status && (
        <div style={{ marginTop: 10, textAlign: "center", color: "red" }}>
          {status}
        </div>
      )}
    </div>
  );
};

export default ChatBox;

