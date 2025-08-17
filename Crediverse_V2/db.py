# db.py
from sqlalchemy import create_engine
import streamlit as st

# .streamlit/secrets.toml must contain:
# [mysql]
# host = "localhost"
# user = "crediverse"
# password = "YourStrongPass!23"
# db = "cv"

cfg = st.secrets["mysql"]

engine = create_engine(
    f"mysql+pymysql://{cfg['user']}:{cfg['password']}@{cfg['host']}/{cfg['db']}",
    pool_pre_ping=True,          # survives idle disconnects
    pool_recycle=1800,           # optional, refresh idle conns
    future=True                  # SQLAlchemy 2.0 style
)
