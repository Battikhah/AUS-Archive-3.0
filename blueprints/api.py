from flask import Blueprint, request, jsonify, abort
import logging
import os

# API blueprint for miscellaneous API endpoints
api_bp = Blueprint('api', __name__)

@api_bp.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'AUS Archive API is running'
    })

@api_bp.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all courses"""
    from app import CONNECTION_POOL
    
    try:
        with CONNECTION_POOL.getconn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM courses ORDER BY name')
            courses = [row[0] for row in cursor.fetchall()]
            
        return jsonify({
            'status': 'success',
            'courses': courses
        })
    except Exception as e:
        logging.error(f"Error fetching courses: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/api/professors', methods=['GET'])
def get_professors():
    """Get all professors"""
    from app import CONNECTION_POOL
    
    try:
        with CONNECTION_POOL.getconn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM professors ORDER BY name')
            professors = [row[0] for row in cursor.fetchall()]
            
        return jsonify({
            'status': 'success',
            'professors': professors
        })
    except Exception as e:
        logging.error(f"Error fetching professors: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/api/file-types', methods=['GET'])
def get_file_types():
    """Get all file types"""
    from app import CONNECTION_POOL
    
    try:
        with CONNECTION_POOL.getconn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM file_types ORDER BY name')
            file_types = [row[0] for row in cursor.fetchall()]
            
        return jsonify({
            'status': 'success',
            'file_types': file_types
        })
    except Exception as e:
        logging.error(f"Error fetching file types: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/api/semesters', methods=['GET'])
def get_semesters():
    """Get all semesters"""
    from app import CONNECTION_POOL
    
    try:
        with CONNECTION_POOL.getconn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM semesters ORDER BY name')
            semesters = [row[0] for row in cursor.fetchall()]
            
        return jsonify({
            'status': 'success',
            'semesters': semesters
        })
    except Exception as e:
        logging.error(f"Error fetching semesters: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
