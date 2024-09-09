function IChatBox(options) {
    const { token, username } = options;
    document.addEventListener('DOMContentLoaded', () => {
        // Tạo và chèn cấu trúc HTML cho IChatBox vào trang
        const chatContainer = document.createElement('div');
        chatContainer.id = 'ichatbox-container';
        chatContainer.innerHTML = `
        <div id="ichatbox-header">IChatBox</div>
        <div id="ichatbox-messages"></div>
        <input id="ichatbox-input" type="text" placeholder="Type a message...">
        <button id="ichatbox-send">Send</button>
    `;
        document.body.appendChild(chatContainer);

        // Tạo và chèn cấu trúc HTML cho nút điều khiển hiển thị ẩn chatbox
        const toggleButton = document.createElement('div');
        toggleButton.id = 'ichatbox-toggle';
        toggleButton.innerHTML = `
        <div id="ichatbox-toggle-icon">+</div>
    `;
        document.body.appendChild(toggleButton);

        // CSS để định vị IChatBox ở góc dưới bên phải màn hình và thêm nút điều khiển
        const styles = `
        #ichatbox-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 300px;
            background-color: #f1f1f1;
            border: 1px solid #ccc;
            padding: 10px;
            box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            display: none; /* Ẩn chatbox ban đầu */
        }
        #ichatbox-header {
            background-color: #007bff;
            color: white;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            border-bottom: 1px solid #ccc;
            cursor: pointer;
        }
        #ichatbox-messages {
            height: 200px;
            overflow-y: auto;
            margin-bottom: 10px;
            border: 1px solid #ccc;
            background-color: #fff;
            padding: 5px;
        }
        #ichatbox-input {
            width: 70%;
            padding: 5px;
        }
        #ichatbox-send {
            width: 25%;
            padding: 5px;
            background-color: #007bff;
            color: white;
            border: none;
            cursor: pointer;
        }
        #ichatbox-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: #007bff;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
            cursor: pointer;
            z-index: 1001;
        }
        #ichatbox-toggle-icon {
            font-size: 24px;
            font-weight: bold;
        }
    `;
        const styleSheet = document.createElement('style');
        styleSheet.type = 'text/css';
        styleSheet.innerText = styles;
        document.head.appendChild(styleSheet);

        // Hiển thị hoặc ẩn chatbox khi nhấp vào nút điều khiển
        const chatContainerElem = document.getElementById('ichatbox-container');
        const toggleButtonElem = document.getElementById('ichatbox-toggle');
        const toggleIconElem = document.getElementById('ichatbox-toggle-icon');

        toggleButtonElem.addEventListener('click', () => {
            if (chatContainerElem.style.display === 'none') {
                chatContainerElem.style.display = 'block';
                toggleIconElem.textContent = '-'; // Đổi thành dấu trừ khi chatbox hiển thị
            } else {
                chatContainerElem.style.display = 'none';
                toggleIconElem.textContent = '+'; // Đổi thành dấu cộng khi chatbox ẩn
            }
        });

        // JavaScript để kết nối với WebSocket và xử lý sự kiện gửi tin nhắn
        const chatSocket = new WebSocket(
            `ws://127.0.0.1:8002/ws/user/chat/?token=${token}&username=${username}`
        );

        chatSocket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            const messages = document.querySelector('#ichatbox-messages');
            messages.innerHTML += '<div>' + data.message + '</div>';
            messages.scrollTop = messages.scrollHeight;
        };

        document.querySelector('#ichatbox-send').onclick = function () {
            const input = document.querySelector('#ichatbox-input');
            const message = input.value;
            chatSocket.send(JSON.stringify({ 'message': message }));
            input.value = '';
        };
    })
}
