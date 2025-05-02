document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatMessages = document.getElementById("chat-messages");

    chatForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const userMessage = chatInput.value.trim();
        if (!userMessage) return;

        // Append user message
        appendMessage("user", userMessage);
        chatInput.value = "";

        // Show bot typing indicator
        const botTyping = appendMessage("bot", "🤖 Bot is typing...", true);

        try {
            const response = await fetch("/chatbot/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.ok) {
                botTyping.innerText = "❌ Error: Failed to get a response.";
                return;
            }

            // Stream response properly
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let botMessage = "";
            let lastChar = ""; // To track spacing

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true }).replace(/\n/g, " ");
                
                // Ensure proper spacing
                if (lastChar !== " " && botMessage.length > 0 && chunk[0] !== " ") {
                    botMessage += " ";
                }

                botMessage += chunk;
                lastChar = chunk[chunk.length - 1]; // Update last character

                botTyping.innerText = botMessage; // Update bot message dynamically
            }

            // Remove "Bot is typing..." when done
            botTyping.innerText = botMessage;

        } catch (error) {
            botTyping.innerText = `❌ Error: ${error.message}`;
        }
    });

    function appendMessage(sender, message, isTyping = false) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender);
        messageElement.innerText = message;

        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll

        return isTyping ? messageElement : null;
    }
});


// document.addEventListener("DOMContentLoaded", function () {
//     const chatBox = document.getElementById("chat-box");
//     const userMessageInput = document.getElementById("user-message");
//     const sendButton = document.getElementById("send-btn");

//     // Function to send message
//     function sendMessage() {
//         let userMessage = userMessageInput.value.trim();
//         if (!userMessage) return;

//         // Display user message
//         chatBox.innerHTML += `<div class="user-message"><strong>You:</strong> ${userMessage}</div>`;
//         userMessageInput.value = "";

//         fetch("/chatbot/", {
//             method: "POST",
//             headers: {
//                 "Content-Type": "application/json",
//                 "X-CSRFToken": getCookie("csrftoken")
//             },
//             body: JSON.stringify({ message: userMessage })
//         })
//         .then(response => response.json())
//         .then(data => {
//             let botResponse = data.response || "Sorry, I couldn't understand.";
//             chatBox.innerHTML += `<div class="bot-message"><strong>Bot:</strong> ${botResponse}</div>`;
//             chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message
//         })
//         .catch(error => console.error("Error:", error));
//     }

//     // Event listener for Send button
//     sendButton.addEventListener("click", sendMessage);

//     // Event listener for Enter key
//     userMessageInput.addEventListener("keypress", function (event) {
//         if (event.key === "Enter") {
//             event.preventDefault();
//             sendMessage();
//         }
//     });

//     // Function to get CSRF token
//     function getCookie(name) {
//         let cookieValue = null;
//         if (document.cookie && document.cookie !== "") {
//             let cookies = document.cookie.split(";");
//             for (let i = 0; i < cookies.length; i++) {
//                 let cookie = cookies[i].trim();
//                 if (cookie.startsWith(name + "=")) {
//                     cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                     break;
//                 }
//             }
//         }
//         return cookieValue;
//     }
// });

