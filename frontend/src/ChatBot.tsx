import React, { useState, useRef, useEffect, type ChangeEvent, type FormEvent, type DragEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./ChatBot.css";

type Message = {
  sender: "user" | "agent";
  text: string;
};

function isPdfMsg(text: string) {
  return text.startsWith("Uploaded file:") || text.match(/\.pdf\*\*/i);
}

const ChatBot: React.FC = () => {
  const [chatInput, setChatInput] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "agent",
      text: "Hi! How can I help you today? I am a chatbot specifically designed to assist you with reviews, design document questions, and warranty/refund inquiries."
    }
  ]);
  const [status, setStatus] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const preventDefault = (e: Event) => {
      e.preventDefault();
      e.stopPropagation();
    };

    window.addEventListener("dragover", preventDefault);
    window.addEventListener("drop", preventDefault);

    return () => {
      window.removeEventListener("dragover", preventDefault);
      window.removeEventListener("drop", preventDefault);
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Add upload message whenever pdfFile changes
  useEffect(() => {
    if (pdfFile) {
      setMessages((prev) => {
        const withoutUpload = prev.filter(m => m.text !== `📄 Uploaded file: **${pdfFile.name}**`);
        return [...withoutUpload, { sender: "user", text: `📄 Uploaded file: **${pdfFile.name}**` }];
      });
    } else {
      setMessages((prev) => prev.filter(m => !isPdfMsg(m.text)));
    }
  }, [pdfFile]);

  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => setChatInput(e.target.value);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (file.type === "application/pdf") {
        setPdfFile(file);
        setStatus("");
      } else {
        setStatus("Only PDF files are allowed.");
        setTimeout(() => setStatus(""), 3000);
      }
    } else {
      setPdfFile(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf") {
        setPdfFile(file);
        setStatus("");
      } else {
        setStatus("Only PDF files can be dropped.");
        setTimeout(() => setStatus(""), 3000);
      }
      e.dataTransfer.clearData();
    }
  };


  // Remove uploaded file and related message
  const removeUpload = () => {
    setPdfFile(null);
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
          {messages.map((msg, idx) => {
            const isFileMsg = isPdfMsg(msg.text);
            return (
              <div key={idx} style={{ textAlign: msg.sender === "user" ? "right" : "left", position: 'relative' }}>
                <div className={isFileMsg ? "chatbot-bubble file" : `chatbot-bubble ${msg.sender}`}>
                  {msg.sender === "agent" ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                  ) : (
                    <span>{msg.text}</span>
                  )}
                </div>
                {isFileMsg && msg.sender === "user" && (
                  <button
                    onClick={removeUpload}
                    aria-label="Remove uploaded file"
                    title="Remove uploaded file"
                    className={`bubble-remove-btn ${msg.sender === "user" ? "right" : "left"}`}
                  >
                    ×
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="chatbot-dropzone"
          aria-label="Drag and drop a PDF file here or click to select"
          onClick={() => {
            document.getElementById("file-input")?.click();
          }}
        >
          Drag & drop PDF file here, or click to select a file.
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
              id="file-input"
              type="file"
              accept=".pdf"
              style={{ display: "none" }}
              onChange={handleFileChange}
              disabled={status === "Sending..."}
            />
            <button
              type="submit"
              className="chatbot-send-btn"
              disabled={status === "Sending..."}
            >
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
