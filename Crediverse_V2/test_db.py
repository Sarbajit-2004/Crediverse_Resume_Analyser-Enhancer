from sqlalchemy import create_engine
import streamlit as st

def mysql_url():
    cfg = st.secrets["mysql"]
    return f"mysql+pymysql://{cfg['user']}:{cfg['password']}@{cfg['host']}/{cfg['db']}"

engine = create_engine(mysql_url(), pool_pre_ping=True)
