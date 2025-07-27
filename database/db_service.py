#!/usr/bin/env python3
"""
Database Service Module
Handles all database operations for the coffee shop application
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_path: str = "database/coffee_shop.db"):
        self.db_path = db_path
        self.conn = None
        
    def get_connection(self):
        """Get database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        return self.conn
        
    def close_connection(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a SELECT query and return results as list of dicts"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise
            
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Database update error: {e}")
            conn.rollback()
            raise
            
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute multiple INSERT/UPDATE/DELETE queries"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Database batch update error: {e}")
            conn.rollback()
            raise
            
    def get_last_insert_id(self) -> int:
        """Get the last inserted row ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error getting last insert ID: {e}")
            raise

class ProductService(DatabaseService):
    """Service for product-related database operations"""
    
    def get_products(self, 
                    skip: int = 0, 
                    limit: int = 20, 
                    category_id: Optional[int] = None,
                    is_popular: Optional[bool] = None,
                    is_active: Optional[bool] = None,
                    search: Optional[str] = None) -> Dict[str, Any]:
        """Get products with filtering and pagination"""
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if category_id is not None:
            where_conditions.append("p.category_id = ?")
            params.append(category_id)
            
        if is_popular is not None:
            where_conditions.append("p.is_popular = ?")
            params.append(is_popular)
            
        if is_active is not None:
            where_conditions.append("p.is_active = ?")
            params.append(is_active)
            
        if search:
            where_conditions.append("(p.name LIKE ? OR p.description LIKE ?)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
            
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM products p
            WHERE {where_clause}
        """
        count_result = self.execute_query(count_query, params)
        total = count_result[0]['total'] if count_result else 0
        
        # Get products with pagination
        query = f"""
            SELECT 
                p.*,
                c.name as category_name,
                c.description as category_description,
                pt.name as product_type_name,
                pg.name as product_group_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN product_types pt ON p.product_type_id = pt.id
            LEFT JOIN product_groups pg ON p.product_group_id = pg.id
            WHERE {where_clause}
            ORDER BY p.is_popular DESC, p.retail_price DESC
            LIMIT ? OFFSET ?
        """
        
        params.extend([limit, skip])
        products = self.execute_query(query, params)
        
        # Process products
        for product in products:
            # Parse JSON fields
            if product.get('nutrition_info'):
                try:
                    product['nutrition_info'] = json.loads(product['nutrition_info'])
                except:
                    product['nutrition_info'] = {}
                    
            # Add category object
            product['category'] = {
                'id': product['category_id'],
                'name': product['category_name'],
                'description': product['category_description']
            }
            
            # Remove redundant fields
            for field in ['category_name', 'category_description', 'product_type_name', 'product_group_name']:
                product.pop(field, None)
                
        return {
            'products': products,
            'total': total,
            'page': (skip // limit) + 1,
            'per_page': limit
        }
        
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get a single product by ID"""
        query = """
            SELECT 
                p.*,
                c.name as category_name,
                c.description as category_description,
                pt.name as product_type_name,
                pg.name as product_group_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN product_types pt ON p.product_type_id = pt.id
            LEFT JOIN product_groups pg ON p.product_group_id = pg.id
            WHERE p.id = ? OR p.product_id = ?
        """
        
        results = self.execute_query(query, (product_id, product_id))
        if not results:
            return None
            
        product = results[0]
        
        # Parse JSON fields
        if product.get('nutrition_info'):
            try:
                product['nutrition_info'] = json.loads(product['nutrition_info'])
            except:
                product['nutrition_info'] = {}
                
        # Add category object
        product['category'] = {
            'id': product['category_id'],
            'name': product['category_name'],
            'description': product['category_description']
        }
        
        # Remove redundant fields
        for field in ['category_name', 'category_description', 'product_type_name', 'product_group_name']:
            product.pop(field, None)
            
        return product
        
    def get_categories(self) -> List[Dict]:
        """Get all categories"""
        query = """
            SELECT id, name, description, parent_id, created_at, updated_at
            FROM categories
            ORDER BY name
        """
        return self.execute_query(query)

class CartService(DatabaseService):
    """Service for cart-related database operations"""
    
    def add_to_cart(self, session_id: str, product_id: int, quantity: int, 
                   user_id: Optional[int] = None, selected_size: Optional[str] = None,
                   customizations: Optional[Dict] = None) -> Dict:
        """Add item to cart (update quantity if already exists, by user_id only)"""
        # Get product details
        product_service = ProductService(self.db_path)
        product = product_service.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        unit_price = float(product['retail_price'])
        total_price = unit_price * quantity
        customizations_json = json.dumps(customizations) if customizations else None
        # Check if item already exists in cart (same user, product, size, customizations)
        query_check = """
            SELECT id, quantity FROM cart_items
            WHERE user_id = ? AND product_id = ?
                  AND (selected_size IS ? OR selected_size = ?)
                  AND (customizations IS ? OR customizations = ?)
        """
        params_check = [user_id, product_id, selected_size, selected_size, customizations_json, customizations_json]
        existing = self.execute_query(query_check, tuple(params_check))
        if existing:
            cart_item_id = existing[0]['id']
            new_quantity = existing[0]['quantity'] + quantity
            update_query = """
                UPDATE cart_items
                SET quantity = ?, total_price = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            self.execute_update(update_query, (new_quantity, unit_price * new_quantity, cart_item_id))
            return self.get_cart_item_by_user_and_product(user_id, product_id)
        else:
            query = """
                INSERT INTO cart_items (
                    user_id, product_id, quantity, selected_size, 
                    customizations, unit_price, total_price, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            self.execute_update(query, (
                user_id, product_id, quantity, selected_size,
                customizations_json, unit_price, total_price
            ))
            return self.get_cart_item_by_user_and_product(user_id, product_id)

    def get_cart(self, session_id: str = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get cart items for a user only (ignore session_id)"""
        if not user_id:
            return {'items': [], 'total_items': 0, 'total_amount': 0}
        query = """
            SELECT 
                ci.*,
                p.name as product_name,
                p.description as product_description,
                p.image_url as product_image,
                p.retail_price as product_price,
                c.name as category_name
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE ci.user_id = ?
            ORDER BY ci.created_at DESC
        """
        params = [user_id]
        items = self.execute_query(query, params)
        for item in items:
            if item.get('customizations'):
                try:
                    item['customizations'] = json.loads(item['customizations'])
                except:
                    item['customizations'] = {}
            item['product'] = {
                'id': item['product_id'],
                'name': item['product_name'],
                'description': item['product_description'],
                'image': item['product_image'],
                'price': item['product_price'],
                'category': {
                    'name': item['category_name']
                }
            }
            for field in ['product_name', 'product_description', 'product_image', 'product_price', 'category_name']:
                item.pop(field, None)
        total_items = sum(item['quantity'] for item in items)
        total_amount = sum(item['total_price'] for item in items)
        return {
            'items': items,
            'total_items': total_items,
            'total_amount': total_amount
        }

    def get_cart_item_by_user_and_product(self, user_id: int, product_id: int) -> Optional[Dict]:
        """Get a specific cart item by user and product"""
        query = """
            SELECT 
                ci.*,
                p.name as product_name,
                p.description as product_description,
                p.image_url as product_image,
                p.retail_price as product_price
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = ? AND ci.product_id = ?
        """
        results = self.execute_query(query, (user_id, product_id))
        if not results:
            return None
        item = results[0]
        if item.get('customizations'):
            try:
                item['customizations'] = json.loads(item['customizations'])
            except:
                item['customizations'] = {}
        item['product'] = {
            'id': item['product_id'],
            'name': item['product_name'],
            'description': item['product_description'],
            'image': item['product_image'],
            'price': item['product_price']
        }
        for field in ['product_name', 'product_description', 'product_image', 'product_price']:
            item.pop(field, None)
        return item
        
    def update_cart_item_quantity(self, cart_item_id: int, quantity: int) -> bool:
        """Update cart item quantity"""
        # Get current item
        query = "SELECT * FROM cart_items WHERE id = ?"
        results = self.execute_query(query, (cart_item_id,))
        if not results:
            return False
            
        item = results[0]
        unit_price = item['unit_price']
        total_price = unit_price * quantity
        
        # Update quantity and total price
        update_query = """
            UPDATE cart_items 
            SET quantity = ?, total_price = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        
        self.execute_update(update_query, (quantity, total_price, cart_item_id))
        return True
        
    def remove_from_cart(self, cart_item_id: int) -> bool:
        """Remove item from cart"""
        query = "DELETE FROM cart_items WHERE id = ?"
        affected_rows = self.execute_update(query, (cart_item_id,))
        return affected_rows > 0
        
    def clear_cart(self, session_id: str, user_id: Optional[int] = None) -> bool:
        """Clear all items from cart"""
        query = "DELETE FROM cart_items WHERE user_id = ?"
        params = [user_id]
        
        affected_rows = self.execute_update(query, params)
        return affected_rows > 0

class OrderService(DatabaseService):
    """Service for order-related database operations"""
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict:
        """Create a new order"""
        
        # Generate order number
        order_number = self.generate_order_number()
        
        # Insert order
        order_query = """
            INSERT INTO orders (
                order_number, user_id, session_id, status, total_amount,
                tax_amount, discount_amount, final_amount, payment_status,
                payment_method, shipping_address, billing_address, notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                     CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        
        self.execute_update(order_query, (
            order_number,
            order_data.get('user_id'),
            order_data.get('session_id'),
            order_data.get('status', 'pending'),
            order_data.get('total_amount', 0),
            order_data.get('tax_amount', 0),
            order_data.get('discount_amount', 0),
            order_data.get('final_amount', 0),
            order_data.get('payment_status', 'pending'),
            order_data.get('payment_method'),
            json.dumps(order_data.get('shipping_address', {})),
            json.dumps(order_data.get('billing_address', {})),
            order_data.get('notes')
        ))
        
        # Get the created order ID
        order_id = self.get_last_insert_id()
        
        # Add order items
        if order_data.get('order_items'):
            self.add_order_items(order_id, order_data['order_items'])
            
        return self.get_order_by_id(order_id)
        
    def generate_order_number(self) -> str:
        """Generate unique order number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ORD-{timestamp}"
        
    def get_last_insert_id(self) -> int:
        """Get the last inserted row ID"""
        result = self.execute_query("SELECT last_insert_rowid() as id")
        return result[0]['id'] if result else 0
        
    def add_order_items(self, order_id: int, items: List[Dict]) -> None:
        """Add items to an order"""
        query = """
            INSERT INTO order_items (
                order_id, product_id, quantity, unit_price, total_price,
                selected_size, customizations, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        
        for item in items:
            self.execute_update(query, (
                order_id,
                item['product_id'],
                item['quantity'],
                item['unit_price'],
                item['total_price'],
                item.get('selected_size'),
                json.dumps(item.get('customizations', {})),
                item.get('notes')
            ))
            
    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """Get order by ID with items"""
        # Get order
        order_query = """
            SELECT * FROM orders WHERE id = ?
        """
        orders = self.execute_query(order_query, (order_id,))
        if not orders:
            return None
            
        order = orders[0]
        
        # Get order items
        items_query = """
            SELECT 
                oi.*,
                p.name as product_name,
                p.description as product_description,
                p.image_url as product_image
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """
        
        items = self.execute_query(items_query, (order_id,))
        
        # Process items
        for item in items:
            if item.get('customizations'):
                try:
                    item['customizations'] = json.loads(item['customizations'])
                except:
                    item['customizations'] = {}
                    
            # Add product object
            item['product'] = {
                'id': item['product_id'],
                'name': item['product_name'],
                'description': item['product_description'],
                'image': item['product_image']
            }
            
            # Remove redundant fields
            for field in ['product_name', 'product_description', 'product_image']:
                item.pop(field, None)
                
        # Process order
        if order.get('shipping_address'):
            try:
                order['shipping_address'] = json.loads(order['shipping_address'])
            except:
                order['shipping_address'] = {}
                
        if order.get('billing_address'):
            try:
                order['billing_address'] = json.loads(order['billing_address'])
            except:
                order['billing_address'] = {}
                
        order['order_items'] = items
        return order
        
    def get_orders(self, user_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """Get orders with optional user filter"""
        query = """
            SELECT * FROM orders
        """
        params = []
        
        if user_id:
            query += " WHERE user_id = ?"
            params.append(user_id)
            
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        orders = self.execute_query(query, params)
        
        # Process orders
        for order in orders:
            if order.get('shipping_address'):
                try:
                    order['shipping_address'] = json.loads(order['shipping_address'])
                except:
                    order['shipping_address'] = {}
                    
            if order.get('billing_address'):
                try:
                    order['billing_address'] = json.loads(order['billing_address'])
                except:
                    order['billing_address'] = {}
                    
        return orders

class ChatService(DatabaseService):
    """Service for chat-related database operations"""
    
    def create_chat_session(self, session_id: str, user_id: Optional[int] = None) -> Dict:
        """Create a new chat session"""
        query = """
            INSERT OR IGNORE INTO chat_sessions (session_id, user_id, created_at, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        self.execute_update(query, (session_id, user_id))
        
        # Get the session
        return self.get_chat_session(session_id)
        
    def get_chat_session(self, session_id: str) -> Optional[Dict]:
        """Get chat session by session ID"""
        query = """
            SELECT * FROM chat_sessions WHERE session_id = ?
        """
        results = self.execute_query(query, (session_id,))
        return results[0] if results else None
        
    def add_chat_message(self, session_id: str, role: str, content: str, 
                        intent: Optional[str] = None, agent: Optional[str] = None) -> Dict:
        """Add a message to chat session"""
        query = """
            INSERT INTO chat_messages (
                session_id, role, content, intent, agent, created_at
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        
        self.execute_update(query, (session_id, role, content, intent, agent))
        
        # Get the inserted message
        message_id = self.get_last_insert_id()
        return self.get_chat_message(message_id)
        
    def get_chat_message(self, message_id: int) -> Optional[Dict]:
        """Get chat message by ID"""
        query = """
            SELECT * FROM chat_messages WHERE id = ?
        """
        results = self.execute_query(query, (message_id,))
        return results[0] if results else None
        
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get chat history for a session"""
        query = """
            SELECT * FROM chat_messages 
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """
        
        return self.execute_query(query, (session_id, limit))
        
    def update_session_timestamp(self, session_id: str) -> None:
        """Update session timestamp"""
        query = """
            UPDATE chat_sessions 
            SET updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
        """
        self.execute_update(query, (session_id,))

class UserService(DatabaseService):
    """Service for user-related database operations"""
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict:
        """Create a new user"""
        try:
            # Extract name and split into first_name and last_name
            name = user_data.get('name', '')
            name_parts = name.split(' ', 1)
            first_name = name_parts[0] if name_parts else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            query = """
                INSERT INTO users (
                    email, password_hash, first_name, last_name, phone,
                    is_active, is_admin, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            self.execute_update(query, (
                user_data['email'], 
                user_data['password_hash'], 
                first_name, 
                last_name, 
                user_data.get('phone'), 
                user_data.get('is_active', True), 
                user_data.get('is_admin', False)
            ))
            
            user_id = self.get_last_insert_id()
            user = self.get_user_by_id(user_id)
            
            if user is None:
                # If we can't get the user by ID, try to get it by email
                user = self.get_user_by_email(user_data['email'])
                
            if user is None:
                raise Exception(f"Failed to create user with email {user_data['email']}")
                
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
        
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = """
            SELECT id, email, first_name, last_name, phone, is_active, is_admin,
                   created_at, updated_at
            FROM users WHERE id = ?
        """
        results = self.execute_query(query, (user_id,))
        return results[0] if results else None
        
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        query = """
            SELECT id, email, password_hash, first_name, last_name, phone,
                   is_active, is_admin, created_at, updated_at
            FROM users WHERE email = ?
        """
        results = self.execute_query(query, (email,))
        return results[0] if results else None
        
    def authenticate_user(self, email: str, password_hash: str) -> Optional[Dict]:
        """Authenticate user with email and password"""
        query = """
            SELECT id, email, first_name, last_name, phone, is_active, is_admin
            FROM users 
            WHERE email = ? AND password_hash = ? AND is_active = 1
        """
        results = self.execute_query(query, (email, password_hash))
        return results[0] if results else None 