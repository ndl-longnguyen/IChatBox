function IChatBox(options) {
    const { token, username } = options || {};
    if (!token) {
        console.warn('IChatBox: Missing token (license key).');
        return;
    }

    const bootstrap = () => {
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

        // Tạo cấu trúc HTML cho IChatBox (chỉ append vào DOM sau khi token hợp lệ)
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
                        <span id="ichatbox-substatus" style="font-size: 11px; opacity: 0.85; font-weight: 400;">Đang hoạt động</span>
                    </div>
                </div>
                <button id="ichatbox-close" title="Thu nhỏ">&times;</button>
            </div>
            <div id="ichatbox-conn-status" style="display: none; background: #fef3c7; color: #92400e; font-size: 11px; padding: 5px 12px; text-align: center; font-weight: 500; border-bottom: 1px solid #fde68a;">
                ⚠️ Mất kết nối. Đang tự động kết nối lại...
            </div>
            <div id="ichatbox-history-controls"></div>
            <div id="ichatbox-messages"></div>
            <div id="ichatbox-typing" class="ichatbox-typing-wrapper" style="display: none;">
                <div class="ichatbox-typing-bubble">
                    <span class="ichatbox-dot"></span>
                    <span class="ichatbox-dot"></span>
                    <span class="ichatbox-dot"></span>
                </div>
                <span class="ichatbox-typing-text">Đang phản hồi...</span>
            </div>
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

        // Tạo và chèn cấu trúc HTML cho nút điều khiển hiển thị ẩn chatbox và badge thông báo
        const toggleButton = document.createElement('div');
        toggleButton.id = 'ichatbox-toggle';
        toggleButton.innerHTML = `
            <div id="ichatbox-toggle-icon">💬</div>
            <span id="ichatbox-badge" style="display: none; position: absolute; top: -3px; right: -3px; background: #ef4444; color: white; border-radius: 999px; font-size: 11px; font-weight: 700; min-width: 20px; height: 20px; align-items: center; justify-content: center; padding: 0 4px; border: 2px solid white; box-shadow: 0 3px 8px rgba(0,0,0,0.25);">0</span>
        `;

        // Tạo teaser preview popup nổi khi có tin nhắn mới mà widget đang đóng
        const teaserPopup = document.createElement('div');
        teaserPopup.id = 'ichatbox-teaser';
        teaserPopup.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 11px; font-weight: 700; color: #4338ca; text-transform: uppercase; letter-spacing: 0.5px;">💬 Hỗ trợ viên</span>
                <button id="ichatbox-teaser-close" type="button" style="background: none; border: none; font-size: 18px; line-height: 1; cursor: pointer; color: #94a3b8; padding: 0 2px;">&times;</button>
            </div>
            <div id="ichatbox-teaser-body" style="font-size: 13px; color: #1e293b; line-height: 1.4; word-break: break-word; max-height: 48px; overflow: hidden; text-overflow: ellipsis;"></div>
        `;

        const contactBar = document.createElement('div');
        contactBar.id = 'ichatbox-contact-bar';

        const applyWidgetPosition = (position) => {
            const normalized = position || 'bottom-right';
            const isTop = normalized.startsWith('top');
            const isLeft = normalized.endsWith('left');
            const isRight = normalized.endsWith('right');
            const chatTop = isTop ? '190px' : '';
            const chatBottom = isTop ? '' : '95px';
            const toggleTop = isTop ? '20px' : '';
            const toggleBottom = isTop ? '' : '20px';
            const contactBarTop = isTop ? '96px' : '';
            const contactBarBottom = isTop ? '' : '96px';
            const teaserTop = isTop ? '90px' : '';
            const teaserBottom = isTop ? '' : '90px';

            chatContainer.style.top = chatTop;
            chatContainer.style.bottom = chatBottom;
            chatContainer.style.left = isLeft ? '24px' : '';
            chatContainer.style.right = isRight ? '24px' : '';

            toggleButton.style.top = toggleTop;
            toggleButton.style.bottom = toggleBottom;
            toggleButton.style.left = isLeft ? '24px' : '';
            toggleButton.style.right = isRight ? '24px' : '';

            contactBar.style.top = contactBarTop;
            contactBar.style.bottom = contactBarBottom;
            contactBar.style.left = isLeft ? '24px' : '';
            contactBar.style.right = isRight ? '24px' : '';

            teaserPopup.style.top = teaserTop;
            teaserPopup.style.bottom = teaserBottom;
            teaserPopup.style.left = isLeft ? '24px' : '';
            teaserPopup.style.right = isRight ? '24px' : '';
        };

        let historyCursor = null;
        let historyHasMore = false;
        let historyLoading = false;

        const updateHistoryControls = () => {
            const controls = document.getElementById('ichatbox-history-controls');
            if (!controls) {
                return;
            }
            controls.innerHTML = '';
            if (historyHasMore) {
                const button = document.createElement('button');
                button.id = 'ichatbox-load-more';
                button.type = 'button';
                button.textContent = 'Xem tin nhắn cũ hơn';
                button.style.cssText = 'border: none; background: #eef2ff; color: #3730a3; padding: 10px 14px; border-radius: 999px; cursor: pointer; font-weight: 600; font-size: 12px; box-shadow: 0 6px 16px rgba(99, 102, 241, 0.12);';
                button.disabled = historyLoading;
                button.addEventListener('click', () => {
                    if (!historyLoading && historyCursor) {
                        loadChatHistory(50, null, historyCursor);
                    }
                });
                controls.appendChild(button);
            }
        };

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
            @keyframes ichatbox-pulse {
                0%, 100% { box-shadow: 0 4px 20px rgba(79, 70, 229, 0.35); }
                50% { box-shadow: 0 8px 32px rgba(79, 70, 229, 0.25); transform: translateY(-1px); }
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
                animation: ichatbox-pulse 3.5s ease-in-out infinite;
            }
            #ichatbox-toggle:hover {
                transform: scale(1.1) rotate(5deg);
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
            #ichatbox-contact-bar {
                position: fixed;
                bottom: 96px;
                right: 24px;
                display: flex;
                flex-direction: column;
                gap: 12px;
                z-index: 9998;
                opacity: 0;
                transform: translateY(10px);
                transition: opacity 0.3s ease, transform 0.3s ease;
            }
            #ichatbox-contact-bar.active {
                opacity: 1;
                transform: translateY(0);
            }
            #ichatbox-contact-bar a {
                width: 52px;
                height: 52px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                border-radius: 16px;
                color: white;
                text-decoration: none;
                box-shadow: 0 14px 30px rgba(0, 0, 0, 0.15);
                transition: transform 0.22s ease, box-shadow 0.22s ease, filter 0.22s ease;
                position: relative;
                overflow: hidden;
            }
            #ichatbox-contact-bar a::before {
                content: '';
                position: absolute;
                inset: 0;
                background: rgba(255, 255, 255, 0.08);
                opacity: 0;
                transition: opacity 0.25s ease;
            }
            #ichatbox-contact-bar a:hover::before {
                opacity: 1;
            }
            #ichatbox-contact-bar a:hover {
                transform: translateX(-2px) scale(1.05);
                box-shadow: 0 18px 34px rgba(0, 0, 0, 0.18);
                filter: brightness(1.05);
            }
            #ichatbox-contact-bar a .ichatbox-contact-icon {
                width: 22px;
                height: 22px;
                display: block;
                fill: currentColor;
                transition: transform 0.22s ease;
            }
            #ichatbox-contact-bar a:hover .ichatbox-contact-icon {
                transform: rotate(-6deg) scale(1.08);
            }
            #ichatbox-contact-bar a:active .ichatbox-contact-icon {
                transform: rotate(0deg) scale(0.96);
            }
            @keyframes ichatbox-contact-glow {
                0%, 100% { box-shadow: 0 12px 28px rgba(0, 0, 0, 0.16); }
                50% { box-shadow: 0 18px 36px rgba(0, 0, 0, 0.26); transform: translateX(-1px); }
            }
            #ichatbox-contact-bar.active a {
                animation: ichatbox-contact-glow 4s ease-in-out infinite;
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

            /* Styles for contact form when visitor info is required */
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

            /* Teaser preview popup */
            #ichatbox-teaser {
                position: fixed;
                bottom: 92px;
                right: 24px;
                max-width: 280px;
                background: #ffffff;
                padding: 12px 14px;
                border-radius: 14px;
                box-shadow: 0 10px 28px rgba(0, 0, 0, 0.14), 0 2px 8px rgba(0, 0, 0, 0.06);
                border: 1px solid #e2e8f0;
                z-index: 10001;
                display: none;
                cursor: pointer;
                animation: ichatbox-fade-in 0.3s ease;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                transition: transform 0.2s ease;
            }
            #ichatbox-teaser:hover {
                transform: translateY(-2px);
                box-shadow: 0 14px 34px rgba(0, 0, 0, 0.18);
            }

            /* Typing indicator bubble */
            .ichatbox-typing-wrapper {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 4px 16px;
                animation: ichatbox-fade-in 0.2s ease;
                align-self: flex-start;
            }
            .ichatbox-typing-bubble {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                padding: 8px 12px;
                display: flex;
                align-items: center;
                gap: 5px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            }
            .ichatbox-dot {
                width: 6px;
                height: 6px;
                background: #6366f1;
                border-radius: 50%;
                animation: ichatbox-bounce 1.3s infinite ease-in-out;
            }
            .ichatbox-dot:nth-child(1) { animation-delay: -0.32s; }
            .ichatbox-dot:nth-child(2) { animation-delay: -0.16s; }
            @keyframes ichatbox-bounce {
                0%, 80%, 100% { transform: scale(0.4); opacity: 0.4; }
                40% { transform: scale(1); opacity: 1; }
            }
            .ichatbox-typing-text {
                font-size: 11px;
                color: #94a3b8;
                font-weight: 500;
            }

            /* FAQ Chips */
            .ichatbox-faq-chip:hover {
                background: #eef2ff !important;
                border-color: #6366f1 !important;
                color: #4f46e5 !important;
                transform: translateY(-1px);
            }
        `;
        const styleSheet = document.createElement('style');
        styleSheet.type = 'text/css';
        styleSheet.innerText = styles;
        document.head.appendChild(styleSheet);

        // Responsive CSS overrides for mobile and tablet
        const responsiveStyles = `
            @media (max-width: 600px) {
                #ichatbox-container {
                    position: fixed !important;
                    width: 100vw !important;
                    height: 100dvh !important;
                    max-height: 100dvh !important;
                    right: 0 !important;
                    left: 0 !important;
                    bottom: 0 !important;
                    top: 0 !important;
                    border-radius: 0 !important;
                    transform: translateY(100%) !important;
                    transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1) !important;
                    z-index: 100000 !important;
                }
                #ichatbox-container.active {
                    transform: translateY(0) !important;
                }
                #ichatbox-header {
                    padding: 14px 16px !important;
                    border-radius: 0 !important;
                }
                #ichatbox-close {
                    width: 36px !important;
                    height: 36px !important;
                    font-size: 28px !important;
                }
                #ichatbox-teaser {
                    right: 12px !important;
                    bottom: 78px !important;
                    max-width: calc(100vw - 24px) !important;
                }
                #ichatbox-toggle {
                    right: 14px !important;
                    bottom: 14px !important;
                    width: 56px !important;
                    height: 56px !important;
                }
                #ichatbox-contact-bar {
                    right: 14px !important;
                    bottom: 80px !important;
                    gap: 10px !important;
                }
                #ichatbox-contact-bar a {
                    width: 46px !important;
                    height: 46px !important;
                    border-radius: 12px !important;
                }
                #ichatbox-messages { padding: 14px 12px !important; }
                #ichatbox-input { padding: 12px 14px !important; font-size: 15px !important; }
            }

            @media (min-width: 601px) and (max-width: 1024px) {
                #ichatbox-container {
                    width: 330px !important;
                    height: 490px !important;
                    right: 20px !important;
                    bottom: 90px !important;
                }
                #ichatbox-toggle { right: 20px !important; bottom: 18px !important; }
                #ichatbox-contact-bar { right: 20px !important; bottom: 86px !important; }
                #ichatbox-teaser { right: 20px !important; bottom: 86px !important; }
            }
        `;
        const respSheet = document.createElement('style');
        respSheet.type = 'text/css';
        respSheet.innerText = responsiveStyles;
        document.head.appendChild(respSheet);

        // Hiển thị hoặc ẩn chatbox khi nhấp vào nút điều khiển.
        // Lưu ý: widget DOM chỉ được append khi token hợp lệ, nên wiring event phải chạy sau đó.
        const toggleIconElem = toggleButton.querySelector('#ichatbox-toggle-icon');
        let unreadCount = 0;
        let teaserTimer = null;

        const updateUnreadBadge = (count) => {
            unreadCount = Math.max(0, count);
            const badge = document.getElementById('ichatbox-badge');
            if (!badge) return;
            if (unreadCount > 0) {
                badge.textContent = unreadCount > 99 ? '99+' : String(unreadCount);
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        };

        const showTeaser = (text) => {
            const teaserBody = document.getElementById('ichatbox-teaser-body');
            if (!teaserBody || !teaserPopup) return;
            teaserBody.textContent = text || 'Bạn có tin nhắn mới';
            teaserPopup.style.display = 'block';
            clearTimeout(teaserTimer);
            teaserTimer = setTimeout(() => {
                hideTeaser();
            }, 7000);
        };

        const hideTeaser = () => {
            if (teaserPopup) teaserPopup.style.display = 'none';
            clearTimeout(teaserTimer);
        };

        const playChime = () => {
            try {
                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                if (!AudioCtx) return;
                const ctx = new AudioCtx();
                if (ctx.state === 'suspended') ctx.resume();
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(587.33, now); // D5
                osc.frequency.setValueAtTime(880, now + 0.08); // A5
                gain.gain.setValueAtTime(0.08, now);
                gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now);
                osc.stop(now + 0.35);
            } catch (e) {
                // AudioContext blocked
            }
        };

        const showTyping = (text) => {
            const typingElem = document.getElementById('ichatbox-typing');
            if (!typingElem) return;
            const textElem = typingElem.querySelector('.ichatbox-typing-text');
            if (textElem && text) textElem.textContent = text;
            typingElem.style.display = 'flex';
            const messagesDiv = document.getElementById('ichatbox-messages');
            if (messagesDiv) messagesDiv.scrollTop = messagesDiv.scrollHeight;
        };

        const hideTyping = () => {
            const typingElem = document.getElementById('ichatbox-typing');
            if (typingElem) typingElem.style.display = 'none';
        };

        const escapeHtml = (text) => {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        };

        const formatMessageContent = (raw) => {
            let safe = escapeHtml(raw);
            safe = safe.replace(/\n/g, '<br>');
            safe = safe.replace(
                /(https?:\/\/[^\s<]+)/g,
                '<a href="$1" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: underline; font-weight: 500;">$1</a>'
            );
            return safe;
        };

        const openChatbox = () => {
            chatContainer.classList.add('active');
            updateUnreadBadge(0);
            hideTeaser();
            if (toggleIconElem) {
                toggleIconElem.style.transform = 'scale(0) rotate(90deg)';
                setTimeout(() => {
                    toggleIconElem.textContent = '×';
                    toggleIconElem.style.transform = 'scale(1.2) rotate(0deg)';
                    toggleIconElem.style.fontSize = '32px';
                }, 150);
            }
            const input = document.getElementById('ichatbox-input');
            if (input) setTimeout(() => input.focus(), 250);
            const messages = document.getElementById('ichatbox-messages');
            if (messages) messages.scrollTop = messages.scrollHeight;
        };

        const closeChatbox = () => {
            chatContainer.classList.remove('active');
            if (toggleIconElem) {
                toggleIconElem.style.transform = 'scale(0) rotate(-90deg)';
                setTimeout(() => {
                    toggleIconElem.textContent = '💬';
                    toggleIconElem.style.transform = 'scale(1) rotate(0deg)';
                    toggleIconElem.style.fontSize = '26px';
                }, 150);
            }
        };

        const wireShellEvents = () => {
            toggleButton.addEventListener('click', () => {
                if (chatContainer.classList.contains('active')) {
                    closeChatbox();
                } else {
                    openChatbox();
                }
            });
            if (closeButtonElem) {
                closeButtonElem.addEventListener('click', closeChatbox);
            }
            if (teaserPopup) {
                teaserPopup.addEventListener('click', () => {
                    hideTeaser();
                    openChatbox();
                });
                const teaserClose = document.getElementById('ichatbox-teaser-close');
                if (teaserClose) {
                    teaserClose.addEventListener('click', (e) => {
                        e.stopPropagation();
                        hideTeaser();
                    });
                }
            }
        };

        // Tạo hoặc lấy ID duy nhất cho visitor từ localStorage
        let visitorId = localStorage.getItem('ichatbox_visitor_id');
        if (!visitorId) {
            visitorId = 'visitor_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
            localStorage.setItem('ichatbox_visitor_id', visitorId);
        }

        const visitorInfoStorageKey = token ? `ichatbox_visitor_info_${token}` : 'ichatbox_visitor_info';
        const legacyVisitorInfoStorageKey = 'ichatbox_visitor_info';

        const loadVisitorInfo = () => {
            try {
                const rawInfo =
                    localStorage.getItem(visitorInfoStorageKey) ||
                    localStorage.getItem(legacyVisitorInfoStorageKey);

                if (!rawInfo) {
                    return {};
                }

                const parsedInfo = JSON.parse(rawInfo);
                return {
                    name: typeof parsedInfo.name === 'string' ? parsedInfo.name.trim() : '',
                    contact: typeof parsedInfo.contact === 'string' ? parsedInfo.contact.trim() : '',
                };
            } catch (error) {
                console.warn('IChatBox: Failed to parse visitor info from localStorage.', error);
                return {};
            }
        };

        const hasCompleteVisitorInfo = (info) =>
            Boolean(info && info.name && info.contact);

        const saveVisitorInfo = (name, contact) => {
            localStorage.setItem(
                visitorInfoStorageKey,
                JSON.stringify({
                    name: name.trim(),
                    contact: contact.trim(),
                })
            );
        };

        const normalizeSocialLink = (value, prefix) => {
            if (!value) return null;
            const trimmed = String(value).trim();
            if (!trimmed) return null;
            if (/^https?:\/\//i.test(trimmed)) {
                return trimmed;
            }
            return `${prefix}${trimmed.replace(/^\/+/, '')}`;
        };

            const iconSvgs = {
                facebook: `
                    <svg class="ichatbox-contact-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                        <path d="M12 2C6.477 2 2 6.145 2 11.243c0 2.908 1.438 5.504 3.688 7.203V22l3.405-1.867c.91.252 1.873.388 2.907.388 5.523 0 10-4.145 10-9.243S17.523 2 12 2zm.994 12.442l-2.545-2.716-4.97 2.716 5.467-5.804 2.609 2.716 4.906-2.716-5.467 5.804z"></path>
                    </svg>
                `,
                zalo: `
                    <svg class="ichatbox-contact-icon" viewBox="0 0 48 48" aria-hidden="true" focusable="false">
                        <path fill="#2962ff" d="M15,36V6.827l-1.211-0.811C8.64,8.083,5,13.112,5,19v10c0,7.732,6.268,14,14,14h10 c4.722,0,8.883-2.348,11.417-5.931V36H15z"></path>
                        <path fill="#eee" d="M29,5H19c-1.845,0-3.601,0.366-5.214,1.014C10.453,9.25,8,14.528,8,19 c0,6.771,0.936,10.735,3.712,14.607c0.216,0.301,0.357,0.653,0.376,1.022c0.043,0.835-0.129,2.365-1.634,3.742 c-0.162,0.148-0.059,0.419,0.16,0.428c0.942,0.041,2.843-0.014,4.797-0.877c0.557-0.246,1.191-0.203,1.729,0.083 C20.453,39.764,24.333,40,28,40c4.676,0,9.339-1.04,12.417-2.916C42.038,34.799,43,32.014,43,29V19C43,11.268,36.732,5,29,5z"></path>
                        <path fill="#2962ff" d="M36.75,27C34.683,27,33,25.317,33,23.25s1.683-3.75,3.75-3.75s3.75,1.683,3.75,3.75 S38.817,27,36.75,27z M36.75,21c-1.24,0-2.25,1.01-2.25,2.25s1.01,2.25,2.25,2.25S39,24.49,39,23.25S37.99,21,36.75,21z"></path>
                        <path fill="#2962ff" d="M31.5,27h-1c-0.276,0-0.5-0.224-0.5-0.5V18h1.5V27z"></path>
                        <path fill="#2962ff" d="M27,19.75v0.519c-0.629-0.476-1.403-0.769-2.25-0.769c-2.067,0-3.75,1.683-3.75,3.75 S22.683,27,24.75,27c0.847,0,1.621-0.293,2.25-0.769V26.5c0,0.276,0.224,0.5,0.5,0.5h1v-7.25H27z M24.75,25.5 c-1.24,0-2.25-1.01-2.25-2.25S23.51,21,24.75,21S27,22.01,27,23.25S25.99,25.5,24.75,25.5z"></path>
                        <path fill="#2962ff" d="M21.25,18h-8v1.5h5.321L13,26h0.026c-0.163,0.211-0.276,0.463-0.276,0.75V27h7.5 c0.276,0,0.5-0.224,0.5-0.5v-1h-5.321L21,19h-0.026c0.163-0.211,0.276-0.463,0.276-0.75V18z"></path>
                    </svg>
                `,
                phone: `
                    <svg class="ichatbox-contact-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
                        <path d="M13.832 16.568a1 1 0 0 0 1.213-.303l.355-.465A2 2 0 0 1 17 15h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2A18 18 0 0 1 2 4a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v3a2 2 0 0 1-.8 1.6l-.468.351a1 1 0 0 0-.292 1.233 14 14 0 0 0 6.392 6.384"></path>
                    </svg>
                `,
            };

            const buildSocialContacts = (config) => {
                if (!config || !config.show_social_links) {
                    return [];
                }

            const contacts = [];
            if (config.social_facebook) {
                const url = normalizeSocialLink(config.social_facebook, 'https://facebook.com/');
                if (url) {
                    contacts.push({ iconHtml: iconSvgs.facebook, label: 'Facebook', url, bg: '#1877f2', shadow: 'rgba(24, 119, 242, 0.35)' });
                }
            }
            if (config.social_zalo) {
                const value = String(config.social_zalo).trim();
                let url = null;
                if (/^https?:\/\//i.test(value)) {
                    url = value;
                } else {
                    const normalized = value.replace(/^\+?/, '');
                    url = `https://zalo.me/${normalized}`;
                }
                contacts.push({ iconHtml: iconSvgs.zalo, label: 'Zalo', url, bg: '#0068ff', shadow: 'rgba(0, 104, 255, 0.35)' });
            }
            if (config.social_phone) {
                const phone = String(config.social_phone).trim();
                if (phone) {
                    const normalized = phone.replace(/[^0-9+]/g, '');
                    contacts.push({ iconHtml: iconSvgs.phone, label: 'Call', url: `tel:${normalized}`, bg: '#10b981', shadow: 'rgba(16, 185, 129, 0.35)' });
                }
            }
            return contacts;
        };

        const renderSocialContactBar = (config) => {
            const contactBarElem = document.getElementById('ichatbox-contact-bar');
            const contacts = buildSocialContacts(config);
            if (!contactBarElem) {
                return;
            }
            if (!contacts.length) {
                contactBarElem.classList.remove('active');
                contactBarElem.innerHTML = '';
                return;
            }
            contactBarElem.innerHTML = contacts
                .map(
                    (item) => `
                        <a href="${item.url}" target="_blank" rel="noopener noreferrer" title="${item.label}" style="background: ${item.bg}; box-shadow: 0 12px 24px ${item.shadow};">
                            ${item.iconHtml || ''}
                        </a>
                    `
                )
                .join('');
            setTimeout(() => contactBarElem.classList.add('active'), 10);
        };

        // Tải cấu hình từ Backend API (token hợp lệ mới render widget)
        fetch(`${baseUrl}/admin/widget-config/?token=${token}`)
            .then(res => res.json())
            .then(config => {
                if (config && config.error) {
                    throw new Error(config.error);
                }

                // Token hợp lệ: bây giờ mới append widget vào DOM
                document.body.appendChild(chatContainer);
                document.body.appendChild(toggleButton);
                document.body.appendChild(contactBar);
                document.body.appendChild(teaserPopup);

                wireShellEvents();
                renderSocialContactBar(config);
                applyWidgetPosition(config.widget_position);

                const allowAnonymous = config.allow_anonymous !== false; // Mặc định là true
                const historyLimit = (config && typeof config.history_limit === 'number')
                    ? Math.max(1, Math.min(200, config.history_limit))
                    : 50;
                const savedInfo = loadVisitorInfo();

                if (!allowAnonymous && !hasCompleteVisitorInfo(savedInfo)) {
                    renderContactForm(savedInfo);
                } else {
                    const activeName = savedInfo.name || username || 'Guest';
                    const activeContact = savedInfo.contact || '';
                    loadChatHistory(historyLimit, () => connectWebSocket(activeName, activeContact));
                }
            })
            .catch(err => {
                // Token sai/inactive hoặc lỗi config: không hiển thị widget
                console.warn('IChatBox: Widget disabled (invalid token or config error).', err);
            });

        function renderFaqChips() {
            const messagesDiv = document.getElementById('ichatbox-messages');
            if (!messagesDiv || messagesDiv.querySelector('.ichatbox-msg-wrapper')) return;
            if (document.getElementById('ichatbox-faq-chips')) return;

            const chipsDiv = document.createElement('div');
            chipsDiv.id = 'ichatbox-faq-chips';
            chipsDiv.style.cssText = 'display: flex; flex-direction: column; gap: 8px; margin-top: 10px; margin-bottom: 8px; animation: ichatbox-fade-in 0.3s ease;';

            const welcomeHeader = document.createElement('div');
            welcomeHeader.style.cssText = 'font-size: 12px; color: #64748b; font-weight: 500; margin-bottom: 2px;';
            welcomeHeader.textContent = 'Gợi ý câu hỏi nhanh:';
            chipsDiv.appendChild(welcomeHeader);

            const chipContainer = document.createElement('div');
            chipContainer.style.cssText = 'display: flex; flex-wrap: wrap; gap: 6px;';

            const faqs = ['Báo giá dịch vụ', 'Tư vấn sản phẩm', 'Thời gian làm việc', 'Gặp tư vấn viên'];
            faqs.forEach(q => {
                const chip = document.createElement('button');
                chip.type = 'button';
                chip.className = 'ichatbox-faq-chip';
                chip.style.cssText = 'background: #ffffff; border: 1px solid #cbd5e1; color: #4338ca; border-radius: 999px; padding: 6px 12px; font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 6px rgba(0,0,0,0.03); outline: none;';
                chip.textContent = q;
                chip.addEventListener('click', () => {
                    const input = document.querySelector('#ichatbox-input');
                    if (input) {
                        input.value = q;
                        document.querySelector('#ichatbox-send').click();
                    }
                    chipsDiv.remove();
                });
                chipContainer.appendChild(chip);
            });
            chipsDiv.appendChild(chipContainer);
            messagesDiv.appendChild(chipsDiv);
        }

        function appendMessageToUI(senderType, message, createdAtIso) {
            hideTyping();
            const messages = document.querySelector('#ichatbox-messages');
            if (!messages) return;

            const faqChips = document.getElementById('ichatbox-faq-chips');
            if (faqChips) faqChips.remove();

            const isMe = senderType === 'PARTICIPANT';
            const alignSelf = isMe ? 'flex-end' : 'flex-start';
            const alignText = isMe ? 'text-align: right;' : 'text-align: left;';
            const label = isMe ? 'Bạn' : 'Hỗ trợ viên';
            const time = createdAtIso ? new Date(createdAtIso) : new Date();
            const timeString = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            const bgStyle = isMe
                ? 'background: linear-gradient(135deg, #4f46e5, #6366f1); color: white; border-radius: 18px 18px 2px 18px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);'
                : 'background: #ffffff; color: #1e293b; border-radius: 18px 18px 18px 2px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);';

            const safeContent = formatMessageContent(message);

            const msgDiv = document.createElement('div');
            msgDiv.className = 'ichatbox-msg-wrapper';
            msgDiv.style.alignSelf = alignSelf;
            msgDiv.innerHTML = `
                <span style="display: inline-block; padding: 10px 16px; max-width: 100%; word-wrap: break-word; font-size: 14px; line-height: 1.45; ${bgStyle}">
                    ${safeContent}
                </span>
                <span style="font-size: 9px; color: #94a3b8; margin-top: 4px; padding: 0 4px; ${alignText}">
                    ${label} • ${timeString}
                </span>
            `;
            messages.appendChild(msgDiv);
            messages.scrollTop = messages.scrollHeight;
        }

        function loadChatHistory(limit, onDone, before) {
            historyLoading = true;
            updateHistoryControls();

            const clampedLimit = Math.max(1, Math.min(200, Number(limit) || 50));
            let url = `${baseUrl}/admin/widget-history/?token=${token}&device=${encodeURIComponent(visitorId)}&limit=${clampedLimit}`;
            if (before) {
                url += `&before=${encodeURIComponent(before)}`;
            }

            fetch(url)
                .then(res => res.json())
                .then(payload => {
                    const messagesDiv = document.getElementById('ichatbox-messages');
                    const footerDiv = document.getElementById('ichatbox-footer');
                    if (!messagesDiv) return;

                    if (payload && Array.isArray(payload.messages)) {
                        if (!before && footerDiv.style.display !== 'none') {
                            messagesDiv.innerHTML = '';
                        }

                        if (payload.messages.length) {
                            if (before) {
                                const currentScroll = messagesDiv.scrollTop;
                                payload.messages.forEach((msg) => {
                                    prependMessageToUI(msg.sender_type, msg.message, msg.created_at);
                                });
                                messagesDiv.scrollTop = currentScroll + 120 * payload.messages.length;
                            } else {
                                payload.messages.forEach((msg) => {
                                    appendMessageToUI(msg.sender_type, msg.message, msg.created_at);
                                });
                            }
                        } else if (!before) {
                            renderFaqChips();
                        }

                        historyHasMore = Boolean(payload.has_more);
                        historyCursor = payload.next_cursor || null;
                        updateHistoryControls();
                    }
                })
                .catch(err => {
                    console.warn('IChatBox: Failed to load chat history.', err);
                })
                .finally(() => {
                    historyLoading = false;
                    updateHistoryControls();
                    if (typeof onDone === 'function') onDone();
                });
        }

        function prependMessageToUI(senderType, message, createdAtIso) {
            const messages = document.querySelector('#ichatbox-messages');
            if (!messages) return;
            const isMe = senderType === 'PARTICIPANT';
            const alignSelf = isMe ? 'flex-end' : 'flex-start';
            const alignText = isMe ? 'text-align: right;' : 'text-align: left;';
            const label = isMe ? 'Bạn' : 'Hỗ trợ viên';
            const time = createdAtIso ? new Date(createdAtIso) : new Date();
            const timeString = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const bgStyle = isMe
                ? 'background: linear-gradient(135deg, #4f46e5, #6366f1); color: white; border-radius: 18px 18px 2px 18px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);'
                : 'background: #ffffff; color: #1e293b; border-radius: 18px 18px 18px 2px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);';

            const safeContent = formatMessageContent(message);
            const html = `
                <div class="ichatbox-msg-wrapper" style="align-self: ${alignSelf};">
                    <span style="display: inline-block; padding: 10px 16px; max-width: 100%; word-wrap: break-word; font-size: 14px; line-height: 1.45; ${bgStyle}">
                        ${safeContent}
                    </span>
                    <span style="font-size: 9px; color: #94a3b8; margin-top: 4px; padding: 0 4px; ${alignText}">
                        ${label} • ${timeString}
                    </span>
                </div>
            `;
            messages.insertAdjacentHTML('afterbegin', html);
        }

        // Hàm render biểu mẫu thu thập thông tin
        function renderContactForm(prefilledInfo = {}, helperMessage = '') {
            const messagesDiv = document.getElementById('ichatbox-messages');
            const footerDiv = document.getElementById('ichatbox-footer');

            // Ẩn thanh gửi tin nhắn
            footerDiv.style.display = 'none';

            messagesDiv.innerHTML = `
                <div id="ichatbox-form-container" style="display: flex; flex-direction: column; gap: 16px; padding: 16px 8px; font-family: 'Inter', sans-serif;">
                    <div style="text-align: center; margin-bottom: 8px;">
                        <h5 style="font-weight: 700; color: #1e293b; margin: 0 0 6px 0; font-size: 16px;">Bắt đầu trò chuyện</h5>
                        <p style="font-size: 13px; color: #64748b; margin: 0; line-height: 1.45;">${helperMessage || 'Vui lòng cung cấp thông tin liên hệ của bạn để chúng tôi hỗ trợ kịp thời nhé.'}</p>
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

            const nameInput = document.getElementById('ichatbox-form-name');
            const contactInput = document.getElementById('ichatbox-form-contact');
            const errorDiv = document.getElementById('ichatbox-form-error');

            nameInput.value = prefilledInfo.name || '';
            contactInput.value = prefilledInfo.contact || '';

            // Xử lý sự kiện nhấn submit
            document.getElementById('ichatbox-form-submit').addEventListener('click', () => {
                const name = nameInput.value.trim();
                const contact = contactInput.value.trim();

                if (!name || !contact) {
                    errorDiv.style.display = 'flex';
                    if (!name) nameInput.style.borderColor = '#ef4444';
                    if (!contact) contactInput.style.borderColor = '#ef4444';
                    return;
                }

                // Lưu thông tin
                saveVisitorInfo(name, contact);
                errorDiv.style.display = 'none';

                // Hiện lại thanh nhắn tin và xóa sạch form
                footerDiv.style.display = 'flex';
                messagesDiv.innerHTML = '';

                // Bắt đầu kết nối chat thật sự
                loadChatHistory(50, () => connectWebSocket(name, contact));
            });

            // Gỡ bỏ viền đỏ khi gõ chữ lại
            nameInput.addEventListener('input', (e) => {
                e.target.style.borderColor = '#e2e8f0';
                errorDiv.style.display = 'none';
            });
            contactInput.addEventListener('input', (e) => {
                e.target.style.borderColor = '#e2e8f0';
                errorDiv.style.display = 'none';
            });
        }

        // Quản lý kết nối WebSocket chat & Tự động kết nối lại
        let chatSocket = null;
        let reconnectAttempts = 0;
        let reconnectTimeout = null;
        let isManualClose = false;
        const messageQueue = [];

        function connectWebSocket(activeName, activeContact) {
            if (chatSocket && (chatSocket.readyState === WebSocket.OPEN || chatSocket.readyState === WebSocket.CONNECTING)) {
                return;
            }

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

            const connStatus = document.getElementById('ichatbox-conn-status');
            const substatus = document.getElementById('ichatbox-substatus');

            try {
                chatSocket = new WebSocket(
                    `${wsProtocol}//${wsHost}/ws/user/chat/?token=${token}&username=${encodeURIComponent(activeName)}&device=${visitorId}${phoneParam}${emailParam}`
                );
            } catch (err) {
                console.warn('IChatBox: WebSocket instantiation failed.', err);
                return;
            }

            chatSocket.onopen = function () {
                reconnectAttempts = 0;
                if (connStatus) connStatus.style.display = 'none';
                if (substatus) substatus.textContent = 'Đang hoạt động';

                // Gửi hết các tin nhắn tồn đọng trong hàng đợi nếu có
                while (messageQueue.length > 0) {
                    const pendingMsg = messageQueue.shift();
                    chatSocket.send(JSON.stringify({ 'message': pendingMsg }));
                }
            };

            chatSocket.onmessage = function (e) {
                try {
                    const data = JSON.parse(e.data);
                    if (data.type === 'typing') {
                        if (data.is_typing) {
                            showTyping('Hỗ trợ viên đang nhập...');
                        } else {
                            hideTyping();
                        }
                        return;
                    }
                    if (data.type === 'chat_message' || data.sender_type) {
                        hideTyping();
                        appendMessageToUI(data.sender_type, data.message);
                        if (data.sender_type !== 'PARTICIPANT') {
                            playChime();
                            if (!chatContainer.classList.contains('active')) {
                                updateUnreadBadge(unreadCount + 1);
                                showTeaser(data.message);
                            }
                        }
                    }
                } catch (err) {
                    console.error('IChatBox: parse message error', err);
                }
            };

            chatSocket.onclose = function (e) {
                if (e.code === 4403) {
                    if (substatus) substatus.textContent = 'Chưa xác thực';
                    return;
                }
                if (!isManualClose) {
                    if (connStatus) connStatus.style.display = 'block';
                    if (substatus) substatus.textContent = 'Đang kết nối lại...';
                    reconnectAttempts++;
                    const delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts), 12000);
                    clearTimeout(reconnectTimeout);
                    reconnectTimeout = setTimeout(() => {
                        connectWebSocket(activeName, activeContact);
                    }, delay);
                }
            };

            chatSocket.onerror = function () {
                if (chatSocket) chatSocket.close();
            };

            const sendMessage = () => {
                const input = document.querySelector('#ichatbox-input');
                const message = (input.value || '').trim();
                if (!message) return;

                if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
                    chatSocket.send(JSON.stringify({ 'message': message }));
                } else {
                    messageQueue.push(message);
                    appendMessageToUI('PARTICIPANT', message);
                }
                input.value = '';
                showTyping('Đang phản hồi...');
            };

            document.querySelector('#ichatbox-send').onclick = sendMessage;

            document.querySelector('#ichatbox-input').onkeypress = function (e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            };
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootstrap);
    } else {
        bootstrap();
    }
}

// Backwards compatible global + auto-init via <script data-api-key="...">.
// Example:
// <script src="https://yourdomain.com/static/ichatbox.js" data-api-key="UUID" defer></script>
(function autoInitIChatBox() {
    if (typeof window === 'undefined') return;
    window.IChatBox = window.IChatBox || IChatBox;

    const findBootstrapScript = () => {
        const scripts = document.getElementsByTagName('script');
        for (let i = scripts.length - 1; i >= 0; i--) {
            const s = scripts[i];
            if (!s || !s.src) continue;
            if (s.src.includes('ichatbox.js') || s.src.includes('chatbox.js')) {
                return s;
            }
        }
        return null;
    };

    const script = findBootstrapScript();
    if (!script) return;

    // Prevent double-init if user called IChatBox(...) manually.
    if (script.dataset && script.dataset.ichatboxInit === '1') return;

    const token =
        (script.getAttribute('data-widget-key') || '').trim() ||
        (script.getAttribute('data-license-key') || '').trim() ||
        (script.getAttribute('data-api-key') || '').trim();

    if (!token) return;

    script.dataset.ichatboxInit = '1';

    const username =
        (script.getAttribute('data-username') || '').trim() ||
        `Guest_${Math.floor(Math.random() * 1000)}`;

    // Optional: allow overriding the contact bar / anonymous behavior later via config API.
    window.IChatBox({ token, username });
})();
