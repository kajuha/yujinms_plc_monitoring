#!/bin/bash

# 경로 인자를 받음
# 이렇게 변경한 이유는 aliencontrol에서 source 및 python을 실행할 경우
# ros 경로 에러가 발생함
# 그래서 쉘스크립트로 python 변수영역이 분리될 것으로 생각함

cd $1
if [ ! -d "venv" ]
then
    echo "venv not exist."
    # 초기에는 3.6 정상사용, 3.8 테스트결과 이상없음
    virtualenv --python=python3 venv &&\
    source venv/bin/activate &&\
    pip install -r requirements.txt &&\
    deactivate
fi
source venv/bin/activate && python app.py
