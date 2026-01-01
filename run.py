import os
import sys
from app import app, socketio, db
from config import Config
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    try:
        print("=" * 50)
        print("启动班级管理系统...")
        print(f"调试模式: {app.debug}")
        print(f"数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"服务地址: 0.0.0.0:{Config.PORT}")
        print("=" * 50)
        
        # 创建数据库表
        with app.app_context():
            db.create_all()
            print("✓ 数据库表已初始化")
        
        # 检查必要的环境变量
        required_env_vars = ['SECRET_KEY', 'SQLALCHEMY_DATABASE_URI']
        for var in required_env_vars:
            if not app.config.get(var):
                print(f"⚠ 警告: 环境变量 {var} 未设置或为空")
        
        # 启动SocketIO服务器
        print(f"🚀 服务器正在启动，监听端口 {Config.PORT}...")
        print(f"📡 访问地址: http://localhost:{Config.PORT}")
        print("按 Ctrl+C 停止服务器")
        
        socketio.run(
            app,
            host='0.0.0.0',  # 允许所有网络接口访问
            port=Config.PORT,
            debug=app.debug,  # 使用应用的调试设置
            use_reloader=app.debug,  # 调试模式下启用热重载
            allow_unsafe_werkzeug=True,  # 允许在非生产环境使用Werkzeug
            log_output=True  # 启用日志输出
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 服务器已手动停止")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()