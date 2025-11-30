from extensions import db
from utils.time_utils import get_china_time, format_china_time

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    whiteboard_id = db.Column(db.Integer, db.ForeignKey('whiteboard.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=get_china_time)
    updated_at = db.Column(db.DateTime, default=get_china_time, onupdate=get_china_time)
    
    whiteboard = db.relationship('Whiteboard', backref=db.backref('assignments', lazy=True))
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref=db.backref('created_assignments', lazy=True))
    
    def __repr__(self):
        return f'<Assignment {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'subject': self.subject,
            'due_date': format_china_time(self.due_date),
            'whiteboard_id': self.whiteboard_id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.username if self.teacher else None,
            'created_at': format_china_time(self.created_at),
            'updated_at': format_china_time(self.updated_at),
            'whiteboard_name': self.whiteboard.name if self.whiteboard else None,
        }