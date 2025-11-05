from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from ai_service import CustomAIService
import os
import time
import threading
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 初始化 AI 服务
ai_service = CustomAIService()

# 存储对话历史
conversations = {}


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """获取对话列表"""
    return jsonify({
        'conversations': list(conversations.keys())
    })


@app.route('/api/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """删除对话"""
    if conversation_id in conversations:
        del conversations[conversation_id]
    return jsonify({'success': True})


# WebSocket 事件处理
@socketio.on('connect')
def handle_connect():
    """客户端连接事件"""
    print(f'客户端 {request.sid} 已连接')
    emit('connected', {'message': '连接成功', 'status': 'online'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开事件"""
    print(f'客户端 {request.sid} 已断开')


@socketio.on('clear_conversation')
def handle_clear_conversation(data):
    """清空对话"""
    conversation_id = data.get('conversation_id', 'default')
    if conversation_id in conversations:
        conversations[conversation_id] = []


@socketio.on('chat_message')
def handle_chat_message(data):
    print("""处理聊天消息""")
    message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id', 'default')
    collection_name = data.get('collection_name', 'test')

    if not message:
        emit('error', {'message': '消息不能为空'})
        return

    # 保存用户消息
    if conversation_id not in conversations:
        conversations[conversation_id] = []

    user_message = {
        'role': 'user',
        'content': message
    }
    #conversations[conversation_id].append(user_message)

    # 发送用户消息到前端
    emit('message', user_message)

    try:
        # 获取当前连接的sid
        sid = request.sid
        def stream_response(sid):  # 添加sid参数
            full_response = ""
            print(f"处理流式响应sid={sid}")
            for chunk in ai_service.chat_stream(message, conversations[conversation_id], collection_name):
                full_response += chunk
                socketio.emit('stream_chunk', {
                    'chunk': chunk,
                    'conversation_id': conversation_id
                }, room=sid)  # 使用传入的sid
                time.sleep(0.01)  # 控制流式输出速度

            # 保存完整的 AI 回复
            ai_message = {
                'role': 'assistant',
                'content': full_response
            }
            conversations[conversation_id].append(ai_message)

            # 发送完整消息事件
            print(f"完整响应: {full_response}")
            socketio.emit('message_complete', {
                'conversation_id': conversation_id,
                'full_message': full_response
            }, room=sid)  # 使用传入的sid

        # 在后台线程中处理流式响应，传递sid
        thread = threading.Thread(target=stream_response, args=(sid, ))
        thread.daemon = True
        thread.start()

    except Exception as e:
        error_msg = f"AI 服务错误: {str(e)}"
        emit('error', {'message': error_msg})


# 获取 AI 回复（流式）
@socketio.on('new_conversation')
def handle_new_conversation():
    """创建新对话"""
    conversation_id = f"conv_{int(time.time())}"
    conversations[conversation_id] = []
    #ai_service.clear_conversation(conversation_id)
    emit('conversation_created', {
        'conversation_id': conversation_id,
        'title': f'对话 {len(conversations)}'
    })


@socketio.on('get_conversation_history')
def handle_get_history(data):
    """获取对话历史"""
    conversation_id = data.get('conversation_id', 'default')
    history = conversations.get(conversation_id, [])
    emit('conversation_history', {
        'conversation_id': conversation_id,
        'history': history
    })


@socketio.on('get_conversation_collection')
def handle_get_collection():
    """获取数据库列表"""
    collection_name = ai_service.collections[0]
    collections = ai_service.get_collection()
    emit('conversation_collection', {
        'collection_name': collection_name,
        'collections': collections
    })

if __name__ == '__main__':
    socketio.run(app,
                 debug=True,
                 host='0.0.0.0',
                 port=5000,
                 use_reloader=False,
                 allow_unsafe_werkzeug=True)