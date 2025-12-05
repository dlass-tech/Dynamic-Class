from flask import Blueprint, request, jsonify, session
from extensions import db, socketio
from models.user import User
from models.whiteboard import Whiteboard
from models.task import Task
from models.class_models import TeacherClass, ClassSubject
from utils.auth_utils import login_required, teacher_required
from utils.time_utils import parse_datetime_local, format_china_time

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/whiteboards/<int:whiteboard_id>/create_task', methods=['POST'])
@login_required
@teacher_required
def create_task(whiteboard_id):
    whiteboard = Whiteboard.query.get_or_404(whiteboard_id)
    user = db.session.get(User, session['user_id'])
    
    has_permission = False
    assigned_subjects = []
    
    if whiteboard.class_obj.teacher_id == user.id:
        has_permission = True
        class_subjects = ClassSubject.query.filter_by(class_id=whiteboard.class_id).all()
        assigned_subjects = [subject.subject_name for subject in class_subjects]
    else:
        teacher_class = TeacherClass.query.filter_by(
            class_id=whiteboard.class_id, 
            teacher_id=user.id,
            is_approved=True
        ).first()
        
        if teacher_class and teacher_class.assigned_subjects:
            has_permission = True
            assigned_subjects = teacher_class.get_assigned_subjects_list()
    
    if not has_permission:
        return jsonify({'error': '无权限发布任务'}), 403
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    priority = data.get('priority', 1)
    action_id = data.get('action_id', 0)
    subject = data.get('subject')
    due_date_str = data.get('due_date')
    
    if not title:
        return jsonify({'error': '任务标题不能为空'}), 400
    
    if subject and subject not in assigned_subjects:
        return jsonify({'error': f'您没有权限发布{subject}学科的任务'}), 403
    
    due_date = None
    if due_date_str:
        try:
            due_date = parse_datetime_local(due_date_str)
        except ValueError as e:
            return jsonify({'error': f'日期格式无效: {str(e)}'}), 400
    
    task = Task(
        title=title,
        description=description,
        priority=priority,
        action_id=action_id,
        due_date=due_date,
        subject=subject,
        whiteboard_id=whiteboard_id,
        teacher_id=user.id
    )
    
    try:
        db.session.add(task)
        db.session.commit()
        
        socketio.emit('new_task', {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'action_id': task.action_id,
            'subject': task.subject,
            'due_date': format_china_time(task.due_date),
            'created_at': format_china_time(task.created_at),
            'teacher_name': task.teacher.username
        }, room=f"whiteboard_{whiteboard_id}")
        
        return jsonify({'success': True, 'task_id': task.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建任务失败: {str(e)}'}), 500

@tasks_bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    user = db.session.get(User, session['user_id'])
    
    if user.role != 'teacher' or task.whiteboard.class_obj.teacher_id != user.id:
        return jsonify({'error': '无权限'}), 403
    
    try:
        whiteboard_id = task.whiteboard_id
        db.session.delete(task)
        db.session.commit()
        socketio.emit('delete_task', {'task_id': task_id}, room=f"whiteboard_{whiteboard_id}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除任务失败'}), 500

@tasks_bp.route('/whiteboards/<int:whiteboard_id>/tasks')
@login_required
def get_whiteboard_tasks_list(whiteboard_id):
    whiteboard = Whiteboard.query.get_or_404(whiteboard_id)
    user = db.session.get(User, session['user_id'])
    
    # 检查权限：班主任或授课老师
    is_class_teacher = (whiteboard.class_obj.teacher_id == user.id)
    is_teaching_teacher = False
    if not is_class_teacher:
        teacher_class = TeacherClass.query.filter_by(
            class_id=whiteboard.class_id, 
            teacher_id=user.id,
            is_approved=True
        ).first()
        if teacher_class and teacher_class.assigned_subjects:
            is_teaching_teacher = True
    
    if not is_class_teacher and not is_teaching_teacher:
        return jsonify({'error': '无权限'}), 403
    
    try:
        tasks = Task.query.filter_by(whiteboard_id=whiteboard_id).order_by(Task.created_at.desc()).all()
        
        tasks_data = []
        for task in tasks:
            # 计算删除权限：班主任或任务发布者
            can_delete = is_class_teacher or task.teacher_id == user.id
            
            tasks_data.append({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'priority': task.priority,
                'action_id': task.action_id,
                'due_date': format_china_time(task.due_date) if task.due_date else None,
                'is_acknowledged': task.is_acknowledged,
                'is_completed': task.is_completed,
                'created_at': format_china_time(task.created_at),
                'teacher_name': task.teacher.username,
                'teacher_id': task.teacher_id,
                'can_delete': can_delete
            })
        
        return jsonify({'success': True, 'tasks': tasks_data})
    except Exception as e:
        return jsonify({'error': '获取任务列表失败'}), 500