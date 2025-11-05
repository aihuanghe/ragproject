class AIChatApp {
    constructor() {
        this.socket = null;
        this.currentConversationId = 'default' + Date.now();
        this.isConnected = false;
        this.isTyping = false;
        this.selectedCollection = "test"
        this.initializeApp();
    }

    initializeApp() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.loadConversationHistory();
        this.loadConversationCollection()
        this.setdefaultConertionDataId();
    }

    setdefaultConertionDataId() {
        // 检查是否已存在默认对话项
        const list = document.querySelector('.conversation-list');
        const existingDefault = list.querySelector('.conversation-item[data-id="default"]');
        if (existingDefault) {
            // 更新现有默认项而不是创建新项
            existingDefault.setAttribute('data-id', this.currentConversationId);
        }
    }

    connectWebSocket() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('已连接到服务器');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('与服务器断开连接');
            this.updateConnectionStatus(false);
        });

        this.socket.on('connected', (data) => {
            this.showNotification(data.message, 'success');
        });

        this.socket.on('message', (data) => {
            console.log('收到消息message-----------');
            console.log(data);
            console.log('-----------');
            this.addMessage(data.content, 'user');
        });

        this.socket.on('stream_chunk', (data) => {
            console.log('收到消息stream_chunk-----------');
            console.log(data);
            console.log('-----------');
            this.handleStreamChunk(data.chunk, data.conversation_id);
        });

        this.socket.on('message_complete', (data) => {
            this.completeMessage(data.conversation_id, data.full_message);
        });

        this.socket.on('conversation_created', (data) => {
            this.addConversationToList(data.conversation_id, data.title);
        });

        this.socket.on('conversation_history', (data) => {
            this.displayConversationHistory(data.history);
        });

        this.socket.on('error', (data) => {
            this.showNotification(data.message, 'error');
        });

        this.socket.on('conversation_collection', (data) => {
            this.updateConversationCollection(data.collection_name, data.collections);
        })
    }

    setupEventListeners() {
        // 发送消息
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');

        messageInput.addEventListener('input', this.handleInputChange.bind(this));
        messageInput.addEventListener('keydown', this.handleKeyDown.bind(this));
        sendButton.addEventListener('click', this.sendMessage.bind(this));

        // 新对话按钮
        document.getElementById('new-chat-btn').addEventListener('click', () => {
            this.createNewConversation();
        });

        // 清空对话
        document.getElementById('clear-chat').addEventListener('click', () => {
            this.clearCurrentConversation();
        });

        // 建议提示点击
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', (e) => {
                const prompt = e.target.getAttribute('data-prompt');
                this.setInputValue(prompt);
            });
        });

        // 对话列表点击
        document.addEventListener('click', (e) => {
            if (e.target.closest('.conversation-item')) {
                const item = e.target.closest('.conversation-item');
                const conversationId = item.getAttribute('data-id');
                this.switchConversation(conversationId);
            }

            if (e.target.closest('.delete-conv-btn')) {
                e.stopPropagation();
                const item = e.target.closest('.conversation-item');
                const conversationId = item.getAttribute('data-id');
                this.deleteConversation(conversationId);
            }
        });

        document.getElementById('collection-select').addEventListener('change', (event) => {
            const selectedCollection = event.target.value;
            this.changeCollection(selectedCollection)
        });
    }



    handleInputChange() {
        const input = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const charCount = document.querySelector('.char-count');

        // 自动调整高度
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 200) + 'px';

        // 更新字符计数
        const length = input.value.length;
        charCount.textContent = `${length}/2000`;

        // 启用/禁用发送按钮
        sendButton.disabled = length === 0 || length > 2000;
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    sendMessage() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();

        if (!message || this.isTyping) return;

        // 清空输入框
        input.value = '';
        this.handleInputChange();

        // 发送消息
        this.socket.emit('chat_message', {
            message: message,
            conversation_id: this.currentConversationId,
            collection_name: this.selectedCollection
        });

        // 隐藏欢迎消息
        this.hideWelcomeMessage();
    }

    setInputValue(text) {
        const input = document.getElementById('message-input');
        input.value = text;
        this.handleInputChange();
        input.focus();
    }

    createNewConversation() {
        this.socket.emit('new_conversation');
    }

    switchConversation(conversationId) {
        if (conversationId === this.currentConversationId) return;

        // 更新当前对话
        this.currentConversationId = conversationId;

        // 更新UI
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-id="${conversationId}"]`).classList.add('active');

        // 更新标题
        document.getElementById('current-conversation-title').textContent =
            document.querySelector(`[data-id="${conversationId}"] .conversation-title`).textContent;

        // 加载对话历史
        this.loadConversationHistory();
    }

    loadConversationHistory() {
        this.socket.emit('get_conversation_history', {
            conversation_id: this.currentConversationId
        });
    }

    loadConversationCollection() {
        this.socket.emit('get_conversation_collection');
    }

    displayConversationHistory(history) {
        const container = document.getElementById('messages-container');
        container.innerHTML = '';

        if (history.length === 0) {
            this.showWelcomeMessage();
            return;
        }

        history.forEach(message => {
            this.addMessage(message.content, message.type, message.timestamp, false);
        });

        this.scrollToBottom();
    }

    updateConversationCollection(collection_name, collections) {
        // colletion 为List[str]结构
        // 更新collection-select下的列表,并选中collection_name的数据
        document.getElementById('collection-select').innerHTML = collections.map(collection => {
            return `<option value="${collection}">${collection}</option>`;
        })
        document.getElementById('collection-select').value = collection_name;
        this.selectedCollection = collection_name;

    }

    addMessage(content, type, scroll = true) {
        const container = document.getElementById('messages-container');

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const header = document.createElement('div');
        header.className = 'message-header';
        header.textContent = type === 'user' ? '你' : 'AI助手';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        messageDiv.appendChild(header);
        messageDiv.appendChild(contentDiv);

        container.appendChild(messageDiv);

        if (scroll) {
            this.scrollToBottom();
        }
    }

    handleStreamChunk(chunk, conversationId) {
        console.log('Received stream chunk:', chunk, conversationId);
        if (conversationId !== this.currentConversationId) return;

        const container = document.getElementById('messages-container');
        let lastMessage = container.lastElementChild;

        // 如果是新的AI回复，创建新消息
        if (!lastMessage || !lastMessage.classList.contains('assistant-message') ||
            !lastMessage.classList.contains('message-streaming')) {

            lastMessage = document.createElement('div');
            lastMessage.className = 'message assistant-message message-streaming';

            const header = document.createElement('div');
            header.className = 'message-header';
            header.textContent = 'AI助手';

            const content = document.createElement('div');
            content.className = 'message-content';

            lastMessage.appendChild(header);
            lastMessage.appendChild(content);
            container.appendChild(lastMessage);

            this.hideWelcomeMessage();
        }

        // 添加内容
        const contentDiv = lastMessage.querySelector('.message-content');
        contentDiv.textContent += chunk;

        this.scrollToBottom();
        this.isTyping = true;
    }

    completeMessage(conversationId, fullMessage) {
        if (conversationId === this.currentConversationId) {
            const container = document.getElementById('messages-container');
            const lastMessage = container.lastElementChild;

            if (lastMessage && lastMessage.classList.contains('message-streaming')) {
                lastMessage.classList.remove('message-streaming');
            }

            this.isTyping = false;
        }
    }

    addConversationToList(conversationId, title) {
        const list = document.querySelector('.conversation-list');
        const activeItem = list.querySelector('.conversation-item.active');
        if (activeItem) {
            activeItem.classList.remove('active');
        }

        const item = document.createElement('div');
        item.className = 'conversation-item active';
        item.setAttribute('data-id', conversationId);

        item.innerHTML = `
            <div class="conversation-title">${title}</div>
            <button class="delete-conv-btn">×</button>
        `;

        list.insertBefore(item, list.firstChild);

        // 切换到新对话
        this.switchConversation(conversationId);
    }

    deleteConversation(conversationId) {
        if (conversationId === 'default') {
            this.showNotification('默认对话不能删除', 'error');
            return;
        }

        if (confirm('确定要删除这个对话吗？')) {
            fetch(`/api/conversation/${conversationId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const item = document.querySelector(`[data-id="${conversationId}"]`);
                    if (item) {
                        item.remove();
                    }

                    // 如果删除的是当前对话，切换到默认对话
                    if (conversationId === this.currentConversationId) {
                        this.switchConversation('default');
                    }

                    this.showNotification('对话已删除', 'success');
                }
            });
        }
    }

    clearCurrentConversation() {
        const container = document.getElementById('messages-container');
        container.innerHTML = '';
        this.showWelcomeMessage();

        // 通知服务器清空当前对话历史
        this.socket.emit('clear_conversation', {
            conversation_id: this.currentConversationId
        });
    }


    changeCollection(collectionName) {
        this.selectedCollection = collectionName;
        this.socket.emit('clear_conversation', {
                conversation_id: this.currentConversationId
            });
        console.log('Selected collection:', collectionName);
    }

    hideWelcomeMessage() {
        const welcome = document.querySelector('.welcome-message');
        if (welcome) {
            welcome.style.display = 'none';
        }
    }

    showWelcomeMessage() {
        const container = document.getElementById('messages-container');
        const welcome = container.querySelector('.welcome-message');
        if (!welcome) {
            container.innerHTML = `
                <div class="welcome-message">
                    <h2>欢迎使用 AI 对话助手</h2>
                    <p>我可以帮助你回答问题、提供信息、进行对话等</p>
                    <div class="suggestions">
                        <div class="suggestion-chip" data-prompt="招标文件规范">招标文件规范</div>
                        <div class="suggestion-chip" data-prompt="总则">总则</div>
                    </div>
                </div>
            `;

            // 重新绑定建议点击事件
            document.querySelectorAll('.suggestion-chip').forEach(chip => {
                chip.addEventListener('click', (e) => {
                    const prompt = e.target.getAttribute('data-prompt');
                    this.setInputValue(prompt);
                });
            });
        } else {
            welcome.style.display = 'block';
        }
    }

    updateConnectionStatus(connected) {
        this.isConnected = connected;

        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');

        if (connected) {
            statusDot.className = 'status-dot online';
            statusText.textContent = '在线';
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = '离线';
        }
    }

    showNotification(message, type = 'info') {
        // 简单的通知实现
        console.log(`${type}: ${message}`);

        // 可以在这里添加更复杂的通知UI
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
            color: white;
            border-radius: 8px;
            z-index: 1000;
            font-size: 14px;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    scrollToBottom() {
        const container = document.getElementById('messages-container');
        container.scrollTop = container.scrollHeight;
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new AIChatApp();
});