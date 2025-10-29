import sqlite3
import json
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect('chillers.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize the database with the chillers table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chillers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manufacturer TEXT,
                model TEXT NOT NULL,
                capacity_tons REAL,
                ambient_f INTEGER,
                ewt_c REAL,
                lwt_c REAL,
                efficiency_kw_per_ton REAL,
                iplv_kw_per_ton REAL,
                waterflow_usgpm REAL,
                unit_kw REAL,
                compressor_kw REAL,
                fan_kw REAL,
                pressure_drop_psi REAL,
                pressure_drop_ftwg REAL,
                mca_amps REAL,
                length_in REAL,
                width_in REAL,
                height_in REAL,
                refrigerant TEXT,
                notes TEXT,
                extras_json TEXT,
                folder_name TEXT,
                model_prefix TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add new columns if they don't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE chillers ADD COLUMN folder_name TEXT')
        except:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE chillers ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        except:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE chillers ADD COLUMN model_prefix TEXT')
        except:
            pass  # Column already exists
        
        conn.commit()

def insert_chiller(chiller_data: Dict[str, Any]) -> int:
    """Insert a single chiller record and return the ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Convert extras_json dict to string if it exists
        if 'extras_json' in chiller_data and isinstance(chiller_data['extras_json'], dict):
            chiller_data['extras_json'] = json.dumps(chiller_data['extras_json'])
        
        columns = list(chiller_data.keys())
        placeholders = ', '.join(['?' for _ in columns])
        values = [chiller_data[col] for col in columns]
        
        cursor.execute(f'''
            INSERT INTO chillers ({', '.join(columns)})
            VALUES ({placeholders})
        ''', values)
        
        conn.commit()
        return cursor.lastrowid

def batch_insert_chillers(chillers_data: List[Dict[str, Any]]) -> List[int]:
    """Insert multiple chiller records and return their IDs."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        ids = []
        
        for chiller_data in chillers_data:
            # Convert extras_json dict to string if it exists
            if 'extras_json' in chiller_data and isinstance(chiller_data['extras_json'], dict):
                chiller_data['extras_json'] = json.dumps(chiller_data['extras_json'])
            
            columns = list(chiller_data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = [chiller_data[col] for col in columns]
            
            cursor.execute(f'''
                INSERT INTO chillers ({', '.join(columns)})
                VALUES ({placeholders})
            ''', values)
            ids.append(cursor.lastrowid)
        
        conn.commit()
        return ids

def get_chillers_by_criteria(capacity_tons: float, ambient_f: int, 
                           ewt_c: Optional[float] = None, lwt_c: Optional[float] = None,
                           capacity_tolerance: float = 0.1) -> List[Dict[str, Any]]:
    """Get chillers matching the specified criteria."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cap_min = capacity_tons * (1 - capacity_tolerance)
        cap_max = capacity_tons * (1 + capacity_tolerance)
        
        query = '''
            SELECT * FROM chillers 
            WHERE ambient_f = ? 
            AND capacity_tons >= ? 
            AND capacity_tons <= ?
        '''
        params = [ambient_f, cap_min, cap_max]
        
        # Add EWT and LWT filters if provided
        if ewt_c is not None:
            query += ' AND ewt_c = ?'
            params.append(ewt_c)
        
        if lwt_c is not None:
            query += ' AND lwt_c = ?'
            params.append(lwt_c)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        return [dict(row) for row in rows]

def get_available_ambients() -> List[int]:
    """Get list of available ambient temperatures in the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT ambient_f FROM chillers WHERE ambient_f IS NOT NULL ORDER BY ambient_f')
        return [row[0] for row in cursor.fetchall()]

def get_chiller_by_id(chiller_id: int) -> Optional[Dict[str, Any]]:
    """Get a single chiller by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM chillers WHERE id = ?', (chiller_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_chillers() -> List[Dict[str, Any]]:
    """Get all chillers in the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM chillers ORDER BY model')
        return [dict(row) for row in cursor.fetchall()]

def delete_chiller(chiller_id: int) -> bool:
    """Delete a chiller by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM chillers WHERE id = ?', (chiller_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_database_stats() -> Dict[str, Any]:
    """Get database statistics."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM chillers')
        total_chillers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT manufacturer) FROM chillers WHERE manufacturer IS NOT NULL')
        manufacturers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT ambient_f) FROM chillers WHERE ambient_f IS NOT NULL')
        ambients = cursor.fetchone()[0]
        
        return {
            'total_chillers': total_chillers,
            'manufacturers': manufacturers,
            'ambients': ambients
        }

def get_organized_data() -> Dict[str, Any]:
    """Get data organized by model_prefix and folder."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get all data grouped by model_prefix and folder_name
        cursor.execute('''
            SELECT model_prefix, folder_name, manufacturer,
                   COUNT(*) as count,
                   GROUP_CONCAT(DISTINCT model) as models
            FROM chillers 
            WHERE model_prefix IS NOT NULL AND folder_name IS NOT NULL
            GROUP BY model_prefix, folder_name, manufacturer
            ORDER BY model_prefix, folder_name
        ''')
        
        rows = cursor.fetchall()
        
        organized = {}
        for row in rows:
            model_prefix, folder_name, manufacturer, count, models = row
            if model_prefix not in organized:
                organized[model_prefix] = {
                    'manufacturer': manufacturer,
                    'folders': {}
                }
            organized[model_prefix]['folders'][folder_name] = {
                'count': count,
                'models': models.split(',') if models else []
            }
        
        return organized

def get_chillers_by_folder(model_prefix: str, folder_name: str) -> List[Dict[str, Any]]:
    """Get chillers from a specific model prefix and folder."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM chillers 
            WHERE model_prefix = ? AND folder_name = ?
            ORDER BY model
        ''', (model_prefix, folder_name))
        return [dict(row) for row in cursor.fetchall()]

def get_all_folders() -> List[Dict[str, Any]]:
    """Get all folders with their details."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT model_prefix, folder_name, manufacturer,
                   COUNT(*) as count,
                   MIN(ambient_f) as ambient_f,
                   MIN(ewt_c) as ewt_c,
                   MIN(lwt_c) as lwt_c
            FROM chillers 
            WHERE model_prefix IS NOT NULL AND folder_name IS NOT NULL
            GROUP BY model_prefix, folder_name, manufacturer
            ORDER BY model_prefix, folder_name
        ''')
        return [dict(row) for row in cursor.fetchall()]

def update_folder_name(model_prefix: str, old_folder_name: str, new_folder_name: str) -> bool:
    """Update folder name for all records in a folder."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE chillers 
            SET folder_name = ?
            WHERE model_prefix = ? AND folder_name = ?
        ''', (new_folder_name, model_prefix, old_folder_name))
        conn.commit()
        return cursor.rowcount > 0

def delete_folder(model_prefix: str, folder_name: str) -> int:
    """Delete all records in a folder. Returns count of deleted records."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM chillers 
            WHERE model_prefix = ? AND folder_name = ?
        ''', (model_prefix, folder_name))
        conn.commit()
        return cursor.rowcount

def get_chillers_by_manufacturer(manufacturer: str) -> List[Dict[str, Any]]:
    """Get all chillers for a specific manufacturer."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM chillers 
            WHERE manufacturer = ?
            ORDER BY folder_name, model
        ''', (manufacturer,))
        return [dict(row) for row in cursor.fetchall()]
