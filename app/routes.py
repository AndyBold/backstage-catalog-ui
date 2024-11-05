from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
from app.models import CatalogEntity
from app.schema import validate_entity, CATALOG_FIELDS
from app.database import db_manager
import yaml
import io
from typing import List, Tuple, Dict, Any
from datetime import datetime, timezone

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html', fields=CATALOG_FIELDS)

@bp.route('/api/entity', methods=['GET'])
def list_entities() -> Tuple[Dict[str, List[Dict[str, Any]]], int]:
    """List all catalog entities"""
    try:
        with db_manager.session_scope() as session:
            stmt = select(CatalogEntity).order_by(CatalogEntity.created_at.desc())
            entities = session.execute(stmt).scalars().all()
            return jsonify({
                'status': 'success',
                'entities': [entity.to_dict() for entity in entities]
            }), 200
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in list_entities: {str(e)}")
        return jsonify({
            'status': 'error',
            'type': 'database_error',
            'message': 'Failed to retrieve entities',
            'details': str(e)
        }), 500

@bp.route('/api/entity', methods=['POST'])
def create_entity() -> Tuple[Dict[str, Any], int]:
    """Create a new catalog entity with enhanced error handling"""
    try:
        # Parse input data
        data = request.json
        try:
            if 'yaml' in data:
                entity_data = yaml.safe_load(data['yaml'])
            else:
                entity_data = data
        except yaml.YAMLError as e:
            current_app.logger.warning(f"YAML parse error: {str(e)}")
            return jsonify({
                'status': 'error',
                'type': 'yaml_parse_error',
                'message': 'Invalid YAML format',
                'details': str(e)
            }), 400

        # Validate entity structure
        validation_errors = validate_entity(entity_data)
        if validation_errors:
            current_app.logger.warning(f"Validation errors: {validation_errors}")
            return jsonify({
                'status': 'error',
                'type': 'validation_error',
                'message': 'Entity validation failed',
                'errors': validation_errors
            }), 400

        metadata = entity_data['metadata']
        
        # Create and save entity using session context manager
        try:
            with db_manager.session_scope() as session:
                entity = CatalogEntity(
                    kind=entity_data['kind'],
                    name=metadata['name'],
                    namespace=metadata['namespace'],
                    title=metadata.get('title'),
                    description=metadata['description'],
                    owner=metadata['owner'],
                    system=entity_data['spec']['system'],
                    lifecycle=entity_data['spec']['lifecycle'],
                    entity_data=yaml.dump(entity_data)
                )
                session.add(entity)
                # Flush to get the ID without committing
                session.flush()
                entity_dict = entity.to_dict()
                
                current_app.logger.info(f"Created entity: {entity.kind}/{entity.name}")
                return jsonify({
                    'status': 'success',
                    'message': 'Entity created successfully',
                    'entity': entity_dict
                }), 201

        except IntegrityError as e:
            current_app.logger.error(f"Database integrity error: {str(e)}")
            return jsonify({
                'status': 'error',
                'type': 'database_integrity_error',
                'message': 'Database constraint violation',
                'details': str(e)
            }), 409

    except Exception as e:
        current_app.logger.error(f"Unexpected error in create_entity: {str(e)}")
        return jsonify({
            'status': 'error',
            'type': 'unexpected_error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@bp.route('/api/entity/<int:entity_id>', methods=['GET'])
def get_entity(entity_id: int) -> Tuple[Dict[str, Any], int]:
    """Get a specific catalog entity"""
    try:
        with db_manager.session_scope() as session:
            stmt = select(CatalogEntity).where(CatalogEntity.id == entity_id)
            entity = session.execute(stmt).scalar_one_or_none()
            
            if not entity:
                return jsonify({
                    'status': 'error',
                    'type': 'not_found',
                    'message': 'Entity not found'
                }), 404
                
            return jsonify({
                'status': 'success',
                'entity': entity.to_dict()
            }), 200
            
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in get_entity: {str(e)}")
        return jsonify({
            'status': 'error',
            'type': 'database_error',
            'message': 'Failed to retrieve entity',
            'details': str(e)
        }), 500

@bp.route('/api/entity/<int:entity_id>', methods=['PUT'])
def update_entity(entity_id: int) -> Tuple[Dict[str, Any], int]:
    """Update an existing catalog entity"""
    try:
        # Parse and validate input data
        data = request.json
        try:
            if 'yaml' in data:
                entity_data = yaml.safe_load(data['yaml'])
            else:
                entity_data = data
        except yaml.YAMLError as e:
            return jsonify({
                'status': 'error',
                'type': 'yaml_parse_error',
                'message': 'Invalid YAML format',
                'details': str(e)
            }), 400

        validation_errors = validate_entity(entity_data)
        if validation_errors:
            return jsonify({
                'status': 'error',
                'type': 'validation_error',
                'message': 'Entity validation failed',
                'errors': validation_errors
            }), 400

        metadata = entity_data['metadata']
        
        # Update entity using session context manager
        with db_manager.session_scope() as session:
            stmt = select(CatalogEntity).where(CatalogEntity.id == entity_id)
            entity = session.execute(stmt).scalar_one_or_none()
            
            if not entity:
                return jsonify({
                    'status': 'error',
                    'type': 'not_found',
                    'message': 'Entity not found'
                }), 404

            # Update entity attributes
            update_data = {
                'kind': entity_data['kind'],
                'name': metadata['name'],
                'namespace': metadata['namespace'],
                'title': metadata.get('title'),
                'description': metadata['description'],
                'owner': metadata['owner'],
                'system': entity_data['spec']['system'],
                'lifecycle': entity_data['spec']['lifecycle'],
                'entity_data': yaml.dump(entity_data)
            }
            
            for key, value in update_data.items():
                setattr(entity, key, value)

            # Flush to ensure all changes are applied
            session.flush()
            entity_dict = entity.to_dict()
            
            current_app.logger.info(f"Updated entity: {entity.kind}/{entity.name}")
            return jsonify({
                'status': 'success',
                'message': 'Entity updated successfully',
                'entity': entity_dict
            }), 200

    except IntegrityError as e:
        current_app.logger.error(f"Database integrity error in update: {str(e)}")
        return jsonify({
            'status': 'error',
            'type': 'database_integrity_error',
            'message': 'Database constraint violation',
            'details': str(e)
        }), 409
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in update_entity: {str(e)}")
        return jsonify({
            'status': 'error',
            'type': 'database_error',
            'message': 'Database error occurred',
            'details': str(e)
        }), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in update_entity: {str(e)}")
        return jsonify({
            'status': 'error',
            'type': 'unexpected_error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }), 500

@bp.route('/api/entity/<int:entity_id>', methods=['DELETE'])
def delete_entity(entity_id: int) -> Tuple[Dict[str, str], int]:
    """Delete a catalog entity"""
    try:
        with db_manager.session_scope() as session:
            stmt = delete(CatalogEntity).where(CatalogEntity.id == entity_id)
            result = session.execute(stmt)
            
            if result.rowcount == 0:
                return jsonify({
                    'status': 'error',
                    'type': 'not_found',
                    'message': 'Entity not found'
                }), 404
            
            current_app.logger.info(f"Deleted entity with ID: {entity_id}")
            return jsonify({
                'status': 'success',
                'message': 'Entity deleted successfully'
            }), 200
            
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in delete_entity: {str(e)}")
        return jsonify({
            'status': 'error',
            'type': 'database_error',
            'message': 'Failed to delete entity',
            'details': str(e)
        }), 500

@bp.route('/api/entity/<int:entity_id>/download')
def download_entity(entity_id: int):
    """Download entity as YAML file"""
    try:
        with db_manager.session_scope() as session:
            stmt = select(CatalogEntity).where(CatalogEntity.id == entity_id)
            entity = session.execute(stmt).scalar_one_or_none()
            
            if not entity:
                return jsonify({
                    'status': 'error',
                    'type': 'not_found',
                    'message': 'Entity not found'
                }), 404
                
            # Parse the YAML data before sending
            yaml_data = yaml.safe_load(entity.entity_data)
            return jsonify({
                'status': 'success',
                'data': yaml_data
            }), 200
            
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in download_entity: {str(e)}")
        return jsonify({
            'status': 'error',
            'type': 'database_error',
            'message': 'Failed to download entity',
            'details': str(e)
        }), 500

@bp.route('/api/upload', methods=['POST'])
def upload_entity() -> Tuple[Dict[str, Any], int]:
    """Upload and validate a YAML entity file"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'type': 'upload_error',
                'message': 'No file uploaded'
            }), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'type': 'upload_error',
                'message': 'No file selected'
            }), 400
            
        if not file.filename.endswith(('.yaml', '.yml')):
            return jsonify({
                'status': 'error',
                'type': 'upload_error',
                'message': 'Invalid file type. Please upload a YAML file'
            }), 400
            
        content = file.read().decode('utf-8')
        try:
            entity_data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return jsonify({
                'status': 'error',
                'type': 'yaml_parse_error',
                'message': 'Invalid YAML format',
                'details': str(e)
            }), 400
        
        errors = validate_entity(entity_data)
        if errors:
            return jsonify({
                'status': 'error',
                'type': 'validation_error',
                'message': 'Entity validation failed',
                'errors': errors
            }), 400
            
        current_app.logger.info(f"Successfully validated uploaded file: {file.filename}")
        return jsonify({
            'status': 'success',
            'message': 'File uploaded and validated successfully',
            'data': entity_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in upload_entity: {str(e)}")
        return jsonify({
            'status': 'error',
            'type': 'unexpected_error',
            'message': 'An unexpected error occurred during upload',
            'details': str(e)
        }), 500
