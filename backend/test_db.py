from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.models import get_session, init_database, Order
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/test-db")
def test_db():
    try:
        db_path = os.path.join('..', 'data', 'digikala_sales.db')
        engine = init_database(db_path)
        session = get_session(engine)
        
        count = session.query(Order).count()
        orders = session.query(Order).limit(5).all()
        
        result = {
            "total_orders": count,
            "sample": [
                {
                    "id": o.id,
                    "order_code": o.order_code,
                    "customer_name": o.customer_name
                }
                for o in orders
            ]
        }
        
        session.close()
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)