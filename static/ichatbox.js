function IChatBox(options) {
    const { token, username } = options;
    document.addEventListener('DOMContentLoaded', () => {
        // Chèn Google Fonts Inter vào trang để đảm bảo giao diện hiển thị cao cấp
        const fontLink = document.createElement('link');
        fontLink.rel = 'stylesheet';
        fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap';
        document.head.appendChild(fontLink);

        // Phát hiện Base URL của server từ thẻ script đang nhúng ichatbox.js
        let baseUrl = 'http://127.0.0.1:8002';
        const scripts = document.getElementsByTagName('script');
        for (let i = 0; i < scripts.length; i++) {
            if (scripts[i].src && scripts[i].src.includes('ichatbox.js')) {
                const url = new URL(scripts[i].src);
                baseUrl = `${url.protocol}//${url.host}`;
                break;
            }
        }

        // Tạo và chèn cấu trúc HTML cho IChatBox vào trang
        const chatContainer = document.createElement('div');
        chatContainer.id = 'ichatbox-container';
        chatContainer.innerHTML = `
            <div id="ichatbox-header">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="position: relative; display: flex; align-items: center;">
                        <div style="width: 38px; height: 38px; background: rgba(255, 255, 255, 0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px;">💬</div>
                        <span style="position: absolute; bottom: 0; right: 0; width: 10px; height: 10px; background-color: #10b981; border: 2px solid #6366f1; border-radius: 50%;"></span>
                    </div>
                    <div style="display: flex; flex-direction: column; align-items: flex-start; line-height: 1.2;">
                        <span style="font-weight: 600; font-size: 15px; letter-spacing: -0.2px;">Hỗ trợ trực tuyến</span>
                        <span style="font-size: 11px; opacity: 0.85; font-weight: 400;">Đang hoạt động</span>
                    </div>
                </div>
                <button id="ichatbox-close">&times;</button>
            </div>
            <div id="ichatbox-messages"></div>
            <div style="text-align: center; font-size: 10px; color: #94a3b8; background-color: #f8fafc; padding: 4px 0 0 0; font-weight: 500; font-family: 'Inter', sans-serif;">
                Powered by <span style="font-weight: 700; color: #6366f1;">IChatBox</span>
            </div>
            <div id="ichatbox-footer">
                <input id="ichatbox-input" type="text" placeholder="Nhập tin nhắn của bạn..." autocomplete="off">
                <button id="ichatbox-send" title="Gửi">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="transform: rotate(45deg);"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                </button>
            </div>
        `;
        document.body.appendChild(chatContainer);

        // Tạo và chèn cấu trúc HTML cho nút điều khiển hiển thị ẩn chatbox
        const toggleButton = document.createElement('div');
        toggleButton.id = 'ichatbox-toggle';
        toggleButton.innerHTML = `
            <div id="ichatbox-toggle-icon">💬</div>
        `;
        document.body.appendChild(toggleButton);

        // CSS để định vị và tạo kiểu dáng Premium cho IChatBox
        const styles = `
            #ichatbox-container {
                position: fixed;
                bottom: 95px;
                right: 24px;
                width: 360px;
                height: 520px;
                background-color: #ffffff;
                border-radius: 20px;
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12), 0 4px 12px rgba(0, 0, 0, 0.05);
                z-index: 10000;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                border: 1px solid rgba(226, 232, 240, 0.8);
                opacity: 0;
                transform: translateY(20px) scale(0.95);
                pointer-events: none;
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            }
            #ichatbox-container.active {
                opacity: 1;
                transform: translateY(0) scale(1);
                pointer-events: auto;
            }
            #ichatbox-header {
                background: linear-gradient(135deg, #4f46e5, #6366f1);
                color: white;
                padding: 16px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
                z-index: 1;
            }
            #ichatbox-close {
                background: none;
                border: none;
                color: rgba(255, 255, 255, 0.8);
                font-size: 24px;
                cursor: pointer;
                padding: 0 5px;
                line-height: 1;
                transition: color 0.2s ease, transform 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            #ichatbox-close:hover {
                color: white;
                transform: scale(1.1);
            }
            #ichatbox-messages {
                flex: 1;
                overflow-y: auto;
                background-color: #f8fafc;
                padding: 20px 16px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            /* Custom elegant scrollbar */
            #ichatbox-messages::-webkit-scrollbar {
                width: 5px;
            }
            #ichatbox-messages::-webkit-scrollbar-track {
                background: transparent;
            }
            #ichatbox-messages::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 10px;
            }
            #ichatbox-messages::-webkit-scrollbar-thumb:hover {
                background: #94a3b8;
            }
            #ichatbox-messages::-webkit-scrollbar-thumb:active {
                background: #64748b;
            }
            #ichatbox-footer {
                padding: 12px 16px;
                background: #ffffff;
                border-top: 1px solid #f1f5f9;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            #ichatbox-input {
                flex: 1;
                border: 1px solid #e2e8f0;
                border-radius: 24px;
                padding: 10px 16px;
                font-size: 14px;
                outline: none;
                font-family: inherit;
                transition: all 0.2s ease;
                color: #1e293b;
            }
            #ichatbox-input:focus {
                border-color: #6366f1;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
            }
            #ichatbox-send {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: linear-gradient(135deg, #4f46e5, #6366f1);
                color: white;
                border: none;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                flex-shrink: 0;
                padding: 0;
            }
            #ichatbox-send:hover {
                transform: scale(1.05);
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
            }
            #ichatbox-send:active {
                transform: scale(0.95);
            }
            #ichatbox-toggle {
                position: fixed;
                bottom: 20px;
                right: 24px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #4f46e5, #6366f1);
                box-shadow: 0 4px 20px rgba(79, 70, 229, 0.35);
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                z-index: 9999;
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            }
            #ichatbox-toggle:hover {
                transform: scale(1.08) rotate(5deg);
                box-shadow: 0 6px 24px rgba(79, 70, 229, 0.45);
            }
            #ichatbox-toggle:active {
                transform: scale(0.95);
            }
            #ichatbox-toggle-icon {
                font-size: 26px;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.3s ease;
            }
            .ichatbox-msg-wrapper {
                display: flex;
                flex-direction: column;
                margin: 4px 0;
                max-width: 85%;
                animation: ichatbox-fade-in 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }
            @keyframes ichatbox-fade-in {
                from { opacity: 0; transform: translateY(8px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* Styles for contact form when anonymous is disabled */
            #ichatbox-form-name:focus, #ichatbox-form-contact:focus {
                border-color: #6366f1 !important;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12) !important;
            }
            #ichatbox-form-submit:hover {
                transform: translateY(-1px);
                box-shadow: 0 6px 16px rgba(79, 70, 229, 0.25) !important;
            }
            #ichatbox-form-submit:active {
                transform: translateY(1px);
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
        const closeButtonElem = document.getElementById('ichatbox-close');

        const openChatbox = () => {
            chatContainerElem.classList.add('active');
            toggleIconElem.style.transform = 'scale(0) rotate(90deg)';
            setTimeout(() => {
                toggleIconElem.textContent = '×';
                toggleIconElem.style.transform = 'scale(1.2) rotate(0deg)';
                toggleIconElem.style.fontSize = '32px';
            }, 150);
        };

        const closeChatbox = () => {
            chatContainerElem.classList.remove('active');
            toggleIconElem.style.transform = 'scale(0) rotate(-90deg)';
            setTimeout(() => {
                toggleIconElem.textContent = '💬';
                toggleIconElem.style.transform = 'scale(1) rotate(0deg)';
                toggleIconElem.style.fontSize = '26px';
            }, 150);
        };

        toggleButtonElem.addEventListener('click', () => {
            if (chatContainerElem.classList.contains('active')) {
                closeChatbox();
            } else {
                openChatbox();
            }
        });

        closeButtonElem.addEventListener('click', closeChatbox);

        // Tạo hoặc lấy ID duy nhất cho visitor từ localStorage
        let visitorId = localStorage.getItem('ichatbox_visitor_id');
        if (!visitorId) {
            visitorId = 'visitor_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
            localStorage.setItem('ichatbox_visitor_id', visitorId);
        }

        // Tải cấu hình từ Backend API
        fetch(`${baseUrl}/admin/widget-config/?token=${token}`)
            .then(res => res.json())
            .then(config => {
                const allowAnonymous = config.allow_anonymous !== false; // Mặc định là true
                const savedInfo = localStorage.getItem('ichatbox_visitor_info');

                if (!allowAnonymous && !savedInfo) {
                    // Nếu KHÔNG cho phép ẩn danh và CHƯA nhập thông tin, hiển thị form liên hệ
                    renderContactForm(allowAnonymous);
                } else {
                    // Ngược lại, tiến hành kết nối trực tiếp
                    const parsedInfo = JSON.parse(savedInfo || '{}');
                    const activeName = parsedInfo.name || username || 'Guest';
                    const activeContact = parsedInfo.contact || '';
                    connectWebSocket(activeName, activeContact);
                }
            })
            .catch(err => {
                console.warn('IChatBox: Failed to retrieve widget settings, using fallback configuration.', err);
                connectWebSocket(username || 'Guest', '');
            });

        // Hàm render biểu mẫu thu thập thông tin
        function renderContactForm(allowAnonymous) {
            const messagesDiv = document.getElementById('ichatbox-messages');
            const footerDiv = document.getElementById('ichatbox-footer');

            // Ẩn thanh gửi tin nhắn
            footerDiv.style.display = 'none';

            messagesDiv.innerHTML = `
                <div id="ichatbox-form-container" style="display: flex; flex-direction: column; gap: 16px; padding: 16px 8px; font-family: 'Inter', sans-serif;">
                    <div style="text-align: center; margin-bottom: 8px;">
                        <h5 style="font-weight: 700; color: #1e293b; margin: 0 0 6px 0; font-size: 16px;">Bắt đầu trò chuyện</h5>
                        <p style="font-size: 13px; color: #64748b; margin: 0; line-height: 1.45;">Vui lòng cung cấp thông tin liên hệ của bạn để chúng tôi hỗ trợ kịp thời nhé.</p>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 6px;">
                        <label style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px;">Họ và tên <span style="color: #ef4444;">*</span></label>
                        <input id="ichatbox-form-name" type="text" placeholder="Nhập họ và tên của bạn..." style="padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 10px; font-size: 14px; outline: none; transition: all 0.2s;" required>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 6px;">
                        <label style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px;">Số điện thoại hoặc Email <span style="color: #ef4444;">*</span></label>
                        <input id="ichatbox-form-contact" type="text" placeholder="Nhập SĐT hoặc Email..." style="padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 10px; font-size: 14px; outline: none; transition: all 0.2s;" required>
                    </div>

                    <div id="ichatbox-form-error" style="color: #dc2626; font-size: 12px; display: none; font-weight: 500; align-items: center; gap: 6px;">
                        ⚠️ Vui lòng điền đầy đủ các thông tin bắt buộc.
                    </div>

                    <button id="ichatbox-form-submit" style="background: linear-gradient(135deg, #4f46e5, #6366f1); color: white; border: none; padding: 12px; border-radius: 10px; font-weight: 600; font-size: 14px; cursor: pointer; transition: all 0.2s; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15); display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 8px; outline: none;">
                        Bắt đầu trò chuyện <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                    </button>
                </div>
            `;

            // Xử lý sự kiện nhấn submit
            document.getElementById('ichatbox-form-submit').addEventListener('click', () => {
                const nameInput = document.getElementById('ichatbox-form-name');
                const contactInput = document.getElementById('ichatbox-form-contact');
                const errorDiv = document.getElementById('ichatbox-form-error');

                const name = nameInput.value.trim();
                const contact = contactInput.value.trim();

                if (!name || !contact) {
                    errorDiv.style.display = 'flex';
                    if (!name) nameInput.style.borderColor = '#ef4444';
                    if (!contact) contactInput.style.borderColor = '#ef4444';
                    return;
                }

                // Lưu thông tin
                localStorage.setItem('ichatbox_visitor_info', JSON.stringify({ name, contact }));

                // Hiện lại thanh nhắn tin và xóa sạch form
                footerDiv.style.display = 'flex';
                messagesDiv.innerHTML = '';

                // Bắt đầu kết nối chat thật sự
                connectWebSocket(name, contact);
            });

            // Gỡ bỏ viền đỏ khi gõ chữ lại
            document.getElementById('ichatbox-form-name').addEventListener('input', (e) => {
                e.target.style.borderColor = '#e2e8f0';
            });
            document.getElementById('ichatbox-form-contact').addEventListener('input', (e) => {
                e.target.style.borderColor = '#e2e8f0';
            });
        }

        // Khởi tạo kết nối WebSocket chat
        function connectWebSocket(activeName, activeContact) {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsHost = baseUrl.replace(/^https?:\/\//, '');

            let phoneParam = '';
            let emailParam = '';
            if (activeContact) {
                if (activeContact.includes('@')) {
                    emailParam = `&email=${encodeURIComponent(activeContact)}`;
                } else {
                    phoneParam = `&phone=${encodeURIComponent(activeContact)}`;
                }
            }

            const chatSocket = new WebSocket(
                `${wsProtocol}//${wsHost}/ws/user/chat/?token=${token}&username=${encodeURIComponent(activeName)}&device=${visitorId}${phoneParam}${emailParam}`
            );

            chatSocket.onmessage = function (e) {
                const data = JSON.parse(e.data);
                if (data.type === 'chat_message' || data.sender_type) {
                    const messages = document.querySelector('#ichatbox-messages');
                    const isMe = data.sender_type === 'PARTICIPANT';

                    const alignSelf = isMe ? 'flex-end' : 'flex-start';
                    const alignText = isMe ? 'text-align: right;' : 'text-align: left;';
                    const label = isMe ? 'Bạn' : 'Hỗ trợ viên';
                    const timeString = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                    const bgStyle = isMe
                        ? 'background: linear-gradient(135deg, #4f46e5, #6366f1); color: white; border-radius: 18px 18px 2px 18px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);'
                        : 'background: #ffffff; color: #1e293b; border-radius: 18px 18px 18px 2px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);';

                    messages.innerHTML += `
                        <div class="ichatbox-msg-wrapper" style="align-self: ${alignSelf};">
                            <span style="display: inline-block; padding: 10px 16px; max-width: 100%; word-wrap: break-word; font-size: 14px; line-height: 1.45; ${bgStyle}">
                                ${data.message}
                            </span>
                            <span style="font-size: 9px; color: #94a3b8; margin-top: 4px; padding: 0 4px; ${alignText}">
                                ${label} • ${timeString}
                            </span>
                        </div>
                    `;
                    messages.scrollTop = messages.scrollHeight;
                }
            };

            const sendMessage = () => {
                const input = document.querySelector('#ichatbox-input');
                const message = input.value.trim();
                if (message) {
                    chatSocket.send(JSON.stringify({ 'message': message }));
                    input.value = '';
                }
            };

            document.querySelector('#ichatbox-send').onclick = sendMessage;

            document.querySelector('#ichatbox-input').onkeypress = function (e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            };
        }
    })
}
