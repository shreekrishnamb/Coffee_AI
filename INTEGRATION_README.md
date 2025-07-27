# Coffee AI - Backend-Frontend Integration

This document explains the complete integration between the RAG-powered backend (`chatbot_rag-main`) and the React frontend application.

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐
│   React Frontend │ ◄─────────────► │  FastAPI Backend │
│   (Port 5173)    │                 │   (Port 8000)    │
└─────────────────┘                 └─────────────────┘
         │                                    │
         │                                    │
         ▼                                    ▼
┌─────────────────┐                 ┌─────────────────┐
│   UI Components  │                 │   RAG System    │
│   - Chatbot      │                 │   - Vector DB   │
│   - Product Cards│                 │   - LLM Service │
│   - Cart         │                 │   - Product Data│
└─────────────────┘                 └─────────────────┘
```

## 🔧 Backend Integration (chatbot_rag-main)

### New API Endpoints Added

The backend now includes all the endpoints that the frontend expects:

#### Chat Endpoints
- `POST /chat` - Main RAG chat endpoint with full response structure
- `POST /api/chatbot` - Legacy endpoint for frontend compatibility

#### Product Endpoints
- `GET /api/v1/products/` - Get products with filtering and pagination
  - Query params: `skip`, `limit`, `category_id`, `is_popular`, `is_active`, `search`

#### Cart Endpoints
- `POST /api/v1/cart/` - Add item to cart
- `GET /api/v1/cart/` - Get cart items with totals

#### Session & Auth Endpoints
- `GET /api/v1/session-id/` - Generate new session ID
- `POST /api/v1/login` - Simple login endpoint (demo)

#### Order Endpoints
- `POST /api/v1/orders/` - Create new order
- `GET /api/v1/orders/` - Get all orders
- `GET /api/v1/orders/{order_id}` - Get specific order

### Data Integration

- **Product Data**: Loaded from `product.csv` file
- **Chat Sessions**: In-memory storage with session management
- **Cart Items**: In-memory storage per session
- **Orders**: In-memory storage for demo purposes

## 🎨 Frontend Integration

### Updated Components

#### Chatbot Component (`src/components/Chatbot.tsx`)
- ✅ Updated to use correct backend endpoint (`http://localhost:8000/api/chatbot`)
- ✅ Proper session management with localStorage
- ✅ Handles backend response format (`data.reply`)
- ✅ Error handling for network issues

#### API Service (`src/services/api.ts`)
- ✅ Configured to use `http://localhost:8000/api/v1`
- ✅ All endpoints match backend implementation
- ✅ Proper TypeScript interfaces for all data types

### Integration Points

1. **Product Display**: Frontend fetches products from backend API
2. **Chatbot**: Real-time chat with RAG-powered responses
3. **Cart Management**: Add/remove items with session persistence
4. **Order Processing**: Complete checkout flow
5. **User Authentication**: Simple login system

## 🚀 Quick Start

### Option 1: Integrated Startup Scripts

#### Windows
```bash
start_integrated.bat
```

#### Linux/Mac
```bash
chmod +x start_integrated.sh
./start_integrated.sh
```

### Option 2: Manual Startup

#### 1. Start Backend
```bash
cd chatbot_rag-main
python main.py --port 8000
```

#### 2. Start Frontend (in new terminal)
```bash
npm run dev
```

### 3. Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔍 Testing the Integration

### 1. Test Chatbot
1. Open http://localhost:5173
2. Click the chat icon in the bottom right
3. Ask questions like:
   - "What coffee do you recommend?"
   - "Tell me about your products"
   - "How do I place an order?"

### 2. Test Product API
```bash
curl http://localhost:8000/api/v1/products/
```

### 3. Test Cart API
```bash
curl -X POST http://localhost:8000/api/v1/cart/ \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test123","product_id":1,"quantity":2}'
```

## 📊 Data Flow

### Chat Flow
```
User Input → Frontend → Backend (/api/chatbot) → RAG System → LLM → Response → Frontend → Display
```

### Product Flow
```
Frontend Request → Backend (/api/v1/products/) → CSV Data → JSON Response → Frontend Display
```

### Cart Flow
```
Add to Cart → Frontend → Backend (/api/v1/cart/) → In-Memory Storage → Response → Frontend Update
```

## 🛠️ Configuration

### Backend Configuration
- **Port**: 8000 (configurable in `main.py`)
- **CORS**: Enabled for all origins (update for production)
- **LLM Provider**: Gemini (configurable in RAG system)

### Frontend Configuration
- **API Base URL**: `http://localhost:8000/api/v1`
- **Chatbot URL**: `http://localhost:8000/api/chatbot`
- **Port**: 5173 (Vite default)

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -ano | findstr :8000  # Windows
   lsof -i :8000                 # Linux/Mac
   ```

2. **Backend Not Starting**
   - Check Python dependencies: `poetry install`
   - Check if `product.csv` exists in `chatbot_rag-main/`

3. **Frontend Can't Connect to Backend**
   - Verify backend is running on port 8000
   - Check CORS settings in backend
   - Verify network connectivity

4. **Chatbot Not Responding**
   - Check browser console for errors
   - Verify backend `/api/chatbot` endpoint is working
   - Check RAG system initialization

### Debug Mode

#### Backend Debug
```bash
cd chatbot_rag-main
python main.py --port 8000 --host 0.0.0.0
```

#### Frontend Debug
```bash
npm run dev -- --debug
```

## 📝 API Documentation

### Chat Endpoint
```typescript
POST /api/chatbot
{
  "message": "string",
  "session_id": "string (optional)"
}

Response:
{
  "reply": "string",
  "session_id": "string",
  "intent": "string"
}
```

### Products Endpoint
```typescript
GET /api/v1/products/?skip=0&limit=20&category_id=1&search=espresso

Response:
{
  "products": Product[],
  "total": number,
  "page": number,
  "per_page": number
}
```

### Cart Endpoint
```typescript
POST /api/v1/cart/
{
  "session_id": "string",
  "product_id": number,
  "quantity": number,
  "selected_size": "string (optional)",
  "customizations": "object (optional)"
}
```

## 🔮 Future Enhancements

1. **Database Integration**: Replace in-memory storage with PostgreSQL
2. **Authentication**: Implement proper JWT authentication
3. **Real-time Chat**: Add WebSocket support for real-time messaging
4. **Payment Integration**: Add Stripe or PayPal integration
5. **Admin Panel**: Create admin interface for product management
6. **Analytics**: Add user behavior tracking and analytics

## 📞 Support

For issues or questions about the integration:
1. Check the troubleshooting section above
2. Review the API documentation at http://localhost:8000/docs
3. Check browser console and backend logs for error messages

---

**Note**: This is a development setup. For production deployment, ensure proper security measures, database setup, and environment configuration. 