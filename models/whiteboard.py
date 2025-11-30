from extensions import db
from utils.time_utils import get_china_time, format_china_time
import secrets

class Whiteboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    board_id = db.Column(db.String(20), unique=True, nullable=False)
    secret_key = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=get_china_time)
    is_active = db.Column(db.Boolean, default=True)
    subjects = db.Column(db.String(500))
    is_online = db.Column(db.Boolean, default=False)
    last_heartbeat = db.Column(db.DateTime)
    token = db.Column(db.String(100), unique=True)
    token_created_at = db.Column(db.DateTime, default=get_china_time)
    
    # ClassworksKV
    use_classworkskv = db.Column(db.Boolean, default=False)
    classworkskv_namespace = db.Column(db.String(100), nullable=True)
    classworkskv_password = db.Column(db.String(100), nullable=True)
    classworkskv_token = db.Column(db.Text, nullable=True)
    classworkskv_connected = db.Column(db.Boolean, default=False)
    classworkskv_last_sync = db.Column(db.DateTime, nullable=True)
    
    class_obj = db.relationship('Class', backref=db.backref('whiteboards', lazy=True))
    
    def __repr__(self):
        return f'<Whiteboard {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'board_id': self.board_id,
            'class_id': self.class_id,
            'class_name': self.class_obj.name if self.class_obj else None,
            'created_at': format_china_time(self.created_at),
            'is_active': self.is_active,
            'subjects': self.subjects,
            'is_online': self.is_online,
            'last_heartbeat': format_china_time(self.last_heartbeat),
            'token': self.token,
            'token_created_at': format_china_time(self.token_created_at),
            # ClassworksKV 信息
            'use_classworkskv': self.use_classworkskv,
            'classworkskv_connected': self.classworkskv_connected,
            'classworkskv_last_sync': format_china_time(self.classworkskv_last_sync) if self.classworkskv_last_sync else None
        }
    
    def generate_token(self):
        """生成新的token"""
        self.token = secrets.token_urlsafe(32)
        self.token_created_at = get_china_time()
        return self.token

class WhiteboardStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    whiteboard_id = db.Column(db.Integer, db.ForeignKey('whiteboard.id'), nullable=False)
    is_online = db.Column(db.Boolean, default=False)
    recorded_at = db.Column(db.DateTime, default=get_china_time)
    
    whiteboard = db.relationship('Whiteboard', backref=db.backref('status_history', lazy=True))
    
    def __repr__(self):
        return f'<WhiteboardStatusHistory whiteboard:{self.whiteboard_id} online:{self.is_online}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'whiteboard_id': self.whiteboard_id,
            'is_online': self.is_online,
            'recorded_at': format_china_time(self.recorded_at),
            'whiteboard_name': self.whiteboard.name if self.whiteboard else None
        }