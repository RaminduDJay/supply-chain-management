"""
Supply Chain Management System - Database Connection Manager
This module handles database connections, connection pooling, and database operations.
"""

import mysql.connector
from mysql.connector import pooling, Error
import os
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Database connection manager with connection pooling and error handling
    """
    
    def __init__(self):
        self.pool = None
        self.config = self._load_config()
        self._create_pool()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from environment variables"""
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'database': os.getenv('DB_NAME', 'supply_chain_db'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': False,
            'time_zone': '+00:00'
        }
        return config
    
    def _create_pool(self):
        """Create connection pool"""
        try:
            pool_config = self.config.copy()
            pool_config.update({
                'pool_name': 'supply_chain_pool',
                'pool_size': 10,
                'pool_reset_session': True,
                'pool_pre_ping': True
            })
            
            self.pool = pooling.MySQLConnectionPool(**pool_config)
            logger.info("Database connection pool created successfully")
            
        except Error as e:
            logger.error(f"Error creating connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        Automatically handles connection lifecycle
        """
        connection = None
        try:
            connection = self.pool.get_connection()
            yield connection
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    @contextmanager
    def get_cursor(self, dictionary=True):
        """
        Context manager for database cursors
        """
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=dictionary)
            try:
                yield cursor, connection
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: Tuple = None, fetch_one: bool = False, 
                     fetch_all: bool = True) -> Optional[List[Dict]]:
        """
        Execute a SELECT query and return results
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch_one: Return only first result
            fetch_all: Return all results
            
        Returns:
            Query results as list of dictionaries or single dictionary
        """
        try:
            with self.get_cursor() as (cursor, connection):
                cursor.execute(query, params or ())
                
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    return None
                    
        except Error as e:
            logger.error(f"Query execution error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def execute_update(self, query: str, params: Tuple = None) -> int:
        """
        Execute INSERT, UPDATE, or DELETE query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            with self.get_cursor() as (cursor, connection):
                cursor.execute(query, params or ())
                connection.commit()
                return cursor.rowcount
                
        except Error as e:
            logger.error(f"Update execution error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Execute query with multiple parameter sets
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            Number of affected rows
        """
        try:
            with self.get_cursor() as (cursor, connection):
                cursor.executemany(query, params_list)
                connection.commit()
                return cursor.rowcount
                
        except Error as e:
            logger.error(f"Batch execution error: {e}")
            logger.error(f"Query: {query}")
            raise
    
    def call_procedure(self, proc_name: str, args: Tuple = None) -> List[Dict]:
        """
        Call a stored procedure
        
        Args:
            proc_name: Stored procedure name
            args: Procedure arguments
            
        Returns:
            Procedure results
        """
        try:
            with self.get_cursor() as (cursor, connection):
                cursor.callproc(proc_name, args or ())
                
                # Get all result sets
                results = []
                for result in cursor.stored_results():
                    results.extend(result.fetchall())
                
                connection.commit()
                return results
                
        except Error as e:
            logger.error(f"Procedure call error: {e}")
            logger.error(f"Procedure: {proc_name}")
            logger.error(f"Args: {args}")
            raise
    
    def call_function(self, func_name: str, args: Tuple = None) -> Any:
        """
        Call a stored function
        
        Args:
            func_name: Function name
            args: Function arguments
            
        Returns:
            Function result
        """
        try:
            # Build function call query
            placeholders = ', '.join(['%s'] * len(args)) if args else ''
            query = f"SELECT {func_name}({placeholders}) as result"
            
            result = self.execute_query(query, args, fetch_one=True)
            return result['result'] if result else None
            
        except Error as e:
            logger.error(f"Function call error: {e}")
            logger.error(f"Function: {func_name}")
            logger.error(f"Args: {args}")
            raise
    
    def begin_transaction(self):
        """Begin a database transaction"""
        return self.get_connection()
    
    def test_connection(self) -> bool:
        """
        Test database connectivity
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as connection:
                if connection.is_connected():
                    logger.info("Database connection test successful")
                    return True
                else:
                    logger.error("Database connection test failed")
                    return False
        except Error as e:
            logger.error(f"Database connection test error: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """
        Get table schema information
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table column information
        """
        query = """
        SELECT 
            COLUMN_NAME as column_name,
            DATA_TYPE as data_type,
            IS_NULLABLE as is_nullable,
            COLUMN_DEFAULT as column_default,
            EXTRA as extra
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        return self.execute_query(query, (self.config['database'], table_name))
    
    def get_foreign_keys(self, table_name: str) -> List[Dict]:
        """
        Get foreign key information for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Foreign key information
        """
        query = """
        SELECT 
            COLUMN_NAME as column_name,
            REFERENCED_TABLE_NAME as referenced_table,
            REFERENCED_COLUMN_NAME as referenced_column
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = %s 
        AND REFERENCED_TABLE_NAME IS NOT NULL
        """
        return self.execute_query(query, (self.config['database'], table_name))
    
    def log_audit_entry(self, table_name: str, operation: str, record_id: str, 
                       old_values: Dict = None, new_values: Dict = None, 
                       user_name: str = None, ip_address: str = None):
        """
        Log an audit entry
        
        Args:
            table_name: Name of affected table
            operation: Type of operation (INSERT, UPDATE, DELETE)
            record_id: ID of affected record
            old_values: Previous values
            new_values: New values
            user_name: User who performed the operation
            ip_address: IP address of the user
        """
        try:
            query = """
            INSERT INTO audit_log 
            (table_name, operation, record_id, old_values, new_values, user_name, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                table_name,
                operation,
                str(record_id),
                json.dumps(old_values) if old_values else None,
                json.dumps(new_values) if new_values else None,
                user_name,
                ip_address
            )
            
            self.execute_update(query, params)
            
        except Error as e:
            logger.error(f"Audit logging error: {e}")
            # Don't raise the error to avoid breaking the main operation
    
    def record_performance_metric(self, metric_name: str, metric_value: float, 
                                 metric_unit: str = None, category: str = None):
        """
        Record a performance metric
        
        Args:
            metric_name: Name of the metric
            metric_value: Metric value
            metric_unit: Unit of measurement
            category: Metric category
        """
        try:
            query = """
            INSERT INTO performance_metrics 
            (metric_name, metric_value, metric_unit, category, recorded_date, recorded_time)
            VALUES (%s, %s, %s, %s, CURDATE(), CURTIME())
            """
            
            params = (metric_name, metric_value, metric_unit, category)
            self.execute_update(query, params)
            
        except Error as e:
            logger.error(f"Performance metric recording error: {e}")
    
    def cleanup_old_logs(self, days_to_keep: int = 90):
        """
        Clean up old audit logs
        
        Args:
            days_to_keep: Number of days to retain logs
        """
        try:
            deleted_count = self.call_procedure('sp_cleanup_audit_logs', (days_to_keep,))
            logger.info(f"Cleaned up {deleted_count} old audit log entries")
            
        except Error as e:
            logger.error(f"Log cleanup error: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary containing database statistics
        """
        try:
            stats = {}
            
            # Table counts
            tables = [
                'users', 'customers', 'items', 'inventory', 'order_table', 
                'train', 'truck', 'driver', 'driver_assistant'
            ]
            
            for table in tables:
                count_query = f"SELECT COUNT(*) as count FROM {table}"
                result = self.execute_query(count_query, fetch_one=True)
                stats[f"{table}_count"] = result['count'] if result else 0
            
            # Storage statistics
            storage_query = """
            SELECT 
                ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
            FROM information_schema.tables 
            WHERE table_schema = %s
            """
            result = self.execute_query(storage_query, (self.config['database'],), fetch_one=True)
            stats['database_size_mb'] = result['size_mb'] if result else 0
            
            return stats
            
        except Error as e:
            logger.error(f"Database stats error: {e}")
            return {}
    
    def close_pool(self):
        """Close the connection pool"""
        if self.pool:
            # Note: mysql.connector doesn't have a direct pool close method
            # The pool will be cleaned up when the object is destroyed
            logger.info("Database connection pool closed")

# Global database instance
db = DatabaseConnection()

# Convenience functions for common operations
def get_db():
    """Get database instance"""
    return db

def execute_query(query: str, params: Tuple = None, **kwargs):
    """Execute query using global database instance"""
    return db.execute_query(query, params, **kwargs)

def execute_update(query: str, params: Tuple = None):
    """Execute update using global database instance"""
    return db.execute_update(query, params)

def call_procedure(proc_name: str, args: Tuple = None):
    """Call procedure using global database instance"""
    return db.call_procedure(proc_name, args)

def call_function(func_name: str, args: Tuple = None):
    """Call function using global database instance"""
    return db.call_function(func_name, args)

# Initialize database connection on module import
if __name__ == "__main__":
    # Test the database connection
    if db.test_connection():
        print("✅ Database connection successful!")
        
        # Display database statistics
        stats = db.get_database_stats()
        print("\n📊 Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Database connection failed!")