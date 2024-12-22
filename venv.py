# 1. 가상환경 만들기 

# 터미널에서 
# 1. 가상환경 만들기 
# python -m venv stream(원하는 이름)
# 2. 가상환경으로 들어가기 
# .\stream\Scripts\activate

# 2. 설치하기 
# pip install streamlit 
# streamlit hello

import streamlit as st 
import pandas as pd

df=pd.DataFrame({
    'first column':[1,2,3,4],
    'second column' : [10,20,30,40]
})

st.write(df)
