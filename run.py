import os
import sys
from app import app, socketio, db
from config import Config
import logging
logging.basicConfig(level=logging.DEBUG)

def main():
    try:
        print("启动班级管理系统...")
        print(f"调试模式: {app.debug}")
        print(f"数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        with app.app_context():
            db.create_all()
            print("数据库表已初始化")
        
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        print(f"启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()