import auth
from database import Base, engine
from fastapi import FastAPI

# MySQL mein tables generate karne ke liye
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API")

# Authentication Endpoints Include Kar Rahe Hain
app.include_router(auth.router)


@app.get("/")
def read_root():
    return {"message": "Expense Tracker API is running successfully!"}