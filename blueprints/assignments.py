from flask import Blueprint, request, jsonify, session
from extensions import db, socketio
from models.user import User
from models.whiteboard import Whiteboard
from models.assignment import Assignment
from models.class_models import TeacherClass, ClassSubject
from utils.auth_utils import login_required, teacher_required
from utils.time_utils import parse_china_time, format_china_time, get_china_time
from utils.classworkskv_utils import ClassworksKVClient
from datetime import timedelta
import json

assignments_bp = Blueprint('assignments', __name__)

def save_assignment_to_classworkskv(whiteboard, assignment):
    """保存作业到 ClassworksKV"""
    if not whiteboard.classworkskv_connected:
        return False, "白板未连接到 ClassworksKV"
    
    client = ClassworksKVClient(whiteboard.classworkskv_namespace, whiteboard.classworkskv_password)
    client.token = whiteboard.classworkskv_token
    
    date_str = assignment.due_date.strftime('%Y%m%d')
    
    # 获取现有数据
    success, existing_data = client.get_homework_data(date_str)
    if not success:
        return False, existing_data
    
    # 更新作业数据
    homework_data = existing_data.get('homework', {})
    homework_data[assignment.subject] = {
        "content": assignment.description,
        "title": assignment.title,
        "due_date": assignment.due_date.isoformat()
    }
    
    # 保存更新后的数据
    update_data = {
        "homework": homework_data,
        "attendance": existing_data.get('attendance', {"late": [], "absent": [], "exclude": []})
    }
    
    success, message = client.save_homework_data(date_str, update_data)
    return success, message

def get_assignments_from_classworkskv(whiteboard, date_str=None):
    """从 ClassworksKV 获取作业"""
    if not whiteboard.classworkskv_connected:
        return False, "白板未连接到 ClassworksKV"
    
    client = ClassworksKVClient(whiteboard.classworkskv_namespace, whiteboard.classworkskv_password)
    client.token = whiteboard.classworkskv_token
    
    if not date_str:
        date_str = get_china_time().strftime('%Y%m%d')
    
    success, homework_data = client.get_homework_data(date_str)
    if not success:
        return False, homework_data
    
    assignments = []
    homework_dict = homework_data.get('homework', {})
    for subject, subject_data in homework_dict.items():
        assignments.append({
            'subject': subject,
            'title': subject_data.get('title', ''),
            'description': subject_data.get('content', ''),
            'due_date': parse_china_time(subject_data.get('due_date', '')) if subject_data.get('due_date') else None
        })
    
    return True, assignments

@assignments_bp.route('/whiteboards/<int:whiteboard_id>/create_assignment', methods=['POST'])
@login_required
@teacher_required
def create_assignment(whiteboard_id):
    whiteboard = Whiteboard.query.get_or_404(whiteboard_id)
    user = db.session.get(User, session['user_id'])
    
    # 检查权限：班主任或授课老师
    is_class_teacher = (whiteboard.class_obj.teacher_id == user.id)
    is_teaching_teacher = False
    assigned_subjects = []
    
    if is_class_teacher:
        class_subjects = ClassSubject.query.filter_by(class_id=whiteboard.class_id).all()
        assigned_subjects = [subject.subject_name for subject in class_subjects]
    else:
        teacher_class = TeacherClass.query.filter_by(
            class_id=whiteboard.class_id, 
            teacher_id=user.id,
            is_approved=True
        ).first()
        
        if teacher_class and teacher_class.assigned_subjects:
            is_teaching_teacher = True
            assigned_subjects = teacher_class.get_assigned_subjects_list()
    
    if not is_class_teacher and not is_teaching_teacher:
        return jsonify({'error': '无权限发布作业'}), 403
    
    data = request.get_json()
    assignment_id = data.get('id')
    title = data.get('title')
    description = data.get('description')
    subject = data.get('subject')
    due_date_str = data.get('due_date')
    
    if not all([title, description, subject, due_date_str]):
        return jsonify({'error': '所有字段都必须填写'}), 400
    
    # 检查学科权限
    if subject not in assigned_subjects:
        return jsonify({'error': f'您没有权限发布{subject}学科的作业'}), 403
    
    try:
        due_date = parse_china_time(due_date_str)
    except ValueError:
        return jsonify({'error': '日期格式无效'}), 400
    
    try:
        # 如果使用 ClassworksKV 存储
        if whiteboard.use_classworkskv and whiteboard.classworkskv_connected:
            # 创建Dlass作业记录（仅用于记录）
            assignment = Assignment(
                title=title,
                description=description,
                subject=subject,
                due_date=due_date,
                whiteboard_id=whiteboard_id,
                teacher_id=user.id
            )
            db.session.add(assignment)
            db.session.commit()
            
            # 保存到 ClassworksKV
            success, message = save_assignment_to_classworkskv(whiteboard, assignment)
            if not success:
                # 如果保存到 ClassworksKV 失败，删除Dlass记录
                db.session.delete(assignment)
                db.session.commit()
                return jsonify({'error': f'保存到 ClassworksKV 失败: {message}'}), 500
            
            # 更新白板同步时间
            whiteboard.classworkskv_last_sync = get_china_time().replace(tzinfo=None)
            db.session.commit()
            
            socketio.emit('new_assignment', {
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'subject': assignment.subject,
                'due_date': format_china_time(assignment.due_date),
                'created_at': format_china_time(assignment.created_at),
                'teacher_name': assignment.teacher.username,
                'storage_type': 'classworkskv'
            }, room=f"whiteboard_{whiteboard_id}")
            
            return jsonify({'success': True, 'assignment_id': assignment.id, 'storage_type': 'classworkskv'})
        else:
            # 使用Dlass存储
            today = get_china_time().replace(tzinfo=None)
            start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            existing_assignment = Assignment.query.filter(
                Assignment.whiteboard_id == whiteboard_id,
                Assignment.subject == subject,
                Assignment.created_at >= start_of_day,
                Assignment.created_at < end_of_day
            ).first()
            
            if existing_assignment:
                # 检查更新权限：班主任或作业发布者
                if existing_assignment.teacher_id != user.id and not is_class_teacher:
                    return jsonify({'error': '无权限更新此作业'}), 403
                    
                existing_assignment.title = title
                existing_assignment.description = description
                existing_assignment.due_date = due_date
                existing_assignment.updated_at = get_china_time().replace(tzinfo=None)
                db.session.commit()
                
                socketio.emit('update_assignment', {
                    'id': existing_assignment.id,
                    'title': existing_assignment.title,
                    'description': existing_assignment.description,
                    'subject': existing_assignment.subject,
                    'due_date': format_china_time(existing_assignment.due_date),
                    'updated_at': format_china_time(existing_assignment.updated_at),
                    'teacher_name': existing_assignment.teacher.username,
                    'storage_type': 'local'
                }, room=f"whiteboard_{whiteboard_id}")
                
                return jsonify({'success': True, 'assignment_id': existing_assignment.id, 'is_update': True, 'storage_type': 'local'})
            else:
                assignment = Assignment(
                    title=title,
                    description=description,
                    subject=subject,
                    due_date=due_date,
                    whiteboard_id=whiteboard_id,
                    teacher_id=user.id
                )
                db.session.add(assignment)
                db.session.commit()
                
                socketio.emit('new_assignment', {
                    'id': assignment.id,
                    'title': assignment.title,
                    'description': assignment.description,
                    'subject': assignment.subject,
                    'due_date': format_china_time(assignment.due_date),
                    'created_at': format_china_time(assignment.created_at),
                    'teacher_name': assignment.teacher.username,
                    'storage_type': 'local'
                }, room=f"whiteboard_{whiteboard_id}")
                
                return jsonify({'success': True, 'assignment_id': assignment.id, 'storage_type': 'local'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '操作失败'}), 500

@assignments_bp.route('/whiteboards/<int:whiteboard_id>/check_assignment', methods=['GET'])
@login_required
@teacher_required
def check_assignment(whiteboard_id):
    whiteboard = Whiteboard.query.get_or_404(whiteboard_id)
    user = db.session.get(User, session['user_id'])
    
    # 检查权限：班主任或授课老师
    is_class_teacher = (whiteboard.class_obj.teacher_id == user.id)
    is_teaching_teacher = False
    assigned_subjects = []
    
    if not is_class_teacher:
        teacher_class = TeacherClass.query.filter_by(
            class_id=whiteboard.class_id, 
            teacher_id=user.id,
            is_approved=True
        ).first()
        if teacher_class and teacher_class.assigned_subjects:
            is_teaching_teacher = True
            assigned_subjects = teacher_class.get_assigned_subjects_list()
    
    if not is_class_teacher and not is_teaching_teacher:
        return jsonify({'error': '无权限'}), 403
    
    subject = request.args.get('subject')
    
    if not subject:
        return jsonify({'error': '缺少科目参数'}), 400
    
    # 如果是授课老师，检查是否有该学科的权限
    if is_teaching_teacher and subject not in assigned_subjects:
        return jsonify({'error': f'您没有权限查看{subject}学科的作业'}), 403
    
    # 如果使用 ClassworksKV，从云端获取
    if whiteboard.use_classworkskv and whiteboard.classworkskv_connected:
        date_str = get_china_time().strftime('%Y%m%d')
        success, assignments = get_assignments_from_classworkskv(whiteboard, date_str)
        if success:
            for assignment in assignments:
                if assignment['subject'] == subject:
                    return jsonify({
                        'assignment': {
                            'id': 'classworkskv',  # 特殊标识
                            'title': assignment['title'],
                            'description': assignment['description'],
                            'subject': assignment['subject'],
                            'due_date': format_china_time(assignment['due_date']) if assignment['due_date'] else None
                        }
                    })
        return jsonify({})
    else:
        # 本地存储逻辑
        assignment = Assignment.query.filter_by(
            whiteboard_id=whiteboard_id,
            subject=subject
        ).order_by(Assignment.created_at.desc()).first()
        
        if assignment:
            return jsonify({
                'assignment': {
                    'id': assignment.id,
                    'title': assignment.title,
                    'description': assignment.description,
                    'subject': assignment.subject,
                    'due_date': format_china_time(assignment.due_date)
                }
            })
        return jsonify({})

@assignments_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    user = db.session.get(User, session['user_id'])
    
    # 检查权限：班主任或作业发布者
    if user.role != 'teacher' or (assignment.whiteboard.class_obj.teacher_id != user.id and assignment.teacher_id != user.id):
        return jsonify({'error': '无权限'}), 403
    
    try:
        whiteboard_id = assignment.whiteboard_id
        
        # 如果使用 ClassworksKV，需要从云端删除
        if assignment.whiteboard.use_classworkskv and assignment.whiteboard.classworkskv_connected:
            client = ClassworksKVClient(
                assignment.whiteboard.classworkskv_namespace, 
                assignment.whiteboard.classworkskv_password
            )
            client.token = assignment.whiteboard.classworkskv_token
            
            date_str = assignment.due_date.strftime('%Y%m%d')
            success, existing_data = client.get_homework_data(date_str)
            
            if success:
                homework_data = existing_data.get('homework', {})
                if assignment.subject in homework_data:
                    del homework_data[assignment.subject]
                    
                    update_data = {
                        "homework": homework_data,
                        "attendance": existing_data.get('attendance', {"late": [], "absent": [], "exclude": []})
                    }
                    
                    client.save_homework_data(date_str, update_data)
        
        db.session.delete(assignment)
        db.session.commit()
        socketio.emit('delete_assignment', {'assignment_id': assignment_id}, room=f"whiteboard_{whiteboard_id}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除作业失败'}), 500

@assignments_bp.route('/whiteboards/<int:whiteboard_id>/assignments')
@login_required
def get_whiteboard_assignments_list(whiteboard_id):
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
        # 如果使用 ClassworksKV，从云端获取
        if whiteboard.use_classworkskv and whiteboard.classworkskv_connected:
            success, assignments_data = get_assignments_from_classworkskv(whiteboard)
            if not success:
                return jsonify({'error': assignments_data}), 500
            
            assignments_list = []
            for assignment_data in assignments_data:
                assignments_list.append({
                    'id': 'classworkskv',  # 特殊标识
                    'title': assignment_data['title'],
                    'description': assignment_data['description'],
                    'subject': assignment_data['subject'],
                    'due_date': format_china_time(assignment_data['due_date']) if assignment_data['due_date'] else None,
                    'created_at': format_china_time(get_china_time()),  # 近似时间
                    'teacher_name': user.username,
                    'teacher_id': user.id,
                    'can_delete': True  # ClassworksKV 作业都可以删除
                })
            
            return jsonify({'success': True, 'assignments': assignments_list})
        else:
            # 本地存储
            assignments = Assignment.query.filter_by(whiteboard_id=whiteboard_id).order_by(Assignment.created_at.desc()).all()
            
            assignments_data = []
            for assignment in assignments:
                # 计算删除权限：班主任或作业发布者
                can_delete = is_class_teacher or assignment.teacher_id == user.id
                
                assignments_data.append({
                    'id': assignment.id,
                    'title': assignment.title,
                    'description': assignment.description,
                    'subject': assignment.subject,
                    'due_date': format_china_time(assignment.due_date),
                    'created_at': format_china_time(assignment.created_at),
                    'teacher_name': assignment.teacher.username,
                    'teacher_id': assignment.teacher_id,
                    'can_delete': can_delete
                })
            
            return jsonify({'success': True, 'assignments': assignments_data})
    except Exception as e:
        return jsonify({'error': '获取作业列表失败'}), 500