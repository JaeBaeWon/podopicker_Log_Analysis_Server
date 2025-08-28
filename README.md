# 📊 MCP CloudFront Log Analysis Collector

## 📌 목차
1. [기획 배경](#1-기획-배경)
2. [프로젝트 개요](#2-프로젝트-개요)
3. [아키텍처 개요](#3-아키텍처-개요)
4. [아키텍처 상세 흐름](#4-아키텍처-상세-흐름)
5. [버전 히스토리](#5-버전-히스토리)
6. [주요 파일 설명](#6-주요-파일-설명)
7. [실행 흐름](#7-실행-흐름)
8. [운영/보안/비용 고려사항](#8-운영보안비용-고려사항)
9. [실험/시뮬레이션 테스트](#9-실험시뮬레이션-테스트)
10. [결과 캡처](#10-결과-캡처)

## 1. 기획 배경

티켓팅 서비스는 특성상 **매크로 및 불법적인 접속 시도**가 빈번하게 발생합니다.

- 자동화된 매크로를 통한 티켓 선점 결제
- 비정상적인 결제 API 호출 시도
- SQL Injection 및 404/403/405 등 비정상 경로 탐색

이러한 활동은 모두 **CloudFront 로그**에 기록되며, 이를 실시간에 가깝게 수집하고 분석할 수 있다면 운영자는 즉각적인 대응이 가능합니다.

본 Collector는 이러한 요구를 충족하기 위하여 설계되었으며,

- CloudFront 로그를 **신속히 수집**하고
- **AI 기반 요약 및 Slack 알림**을 통해 운영자가 빠르게 이상 접속을 파악하고 대응할 수 있도록 지원합니다.

## 2. 프로젝트 개요

본 프로젝트는 **CloudFront 로그를 S3에서 수집 → 파싱/분석 → AI 인사이트 생성 → Slack 전송**까지 자동화하는 로그 분석 수집기입니다.

운영자는 Slack을 통해 **거의 실시간 로그 인사이트**를 확인할 수 있습니다.

## 3. 아키텍처 개요

<p align="center">
  <img src="https://github.com/user-attachments/assets/6575a254-a968-477f-b124-eea2dce0389f" width="600" alt="log_analysis_diagram"/>
</p>

## 4. 아키텍처 상세 흐름

1. **CloudFront → S3**
   - `.gz` 로그 파일을 분 단위로 S3 버킷에 적재합니다.
   - 로그는 지연되거나 순서가 뒤바뀌어 기록될 수 있습니다.

2. **Collector 동작**
   - 일정 주기(1~5분)로 실행됩니다.
   - `ListObjectsV2`로 **신규 로그 존재 여부**를 확인합니다.
   - 신규 로그가 없으면 즉시 종료하여 불필요한 리소스를 방지합니다.

3. **log_parser.py**
   - `.gz` 로그 파일을 해제하고 파싱합니다.
   - 주요 집계 항목: 요청 수, 4xx/5xx 건수, 에러율, Top Path, Top IP, 평균 응답시간 등

4. **gemini_client.py**
   - 집계 결과를 Gemini API에 전달하여 요약 인사이트를 생성합니다.
   - AI 호출이 불가할 경우, 룰 기반 탐지(에러율 임계치, 비정상 트래픽 급증 등)를 수행합니다.

5. **slack_notify.py**
   - KPI 요약 메시지 및 인사이트를 Slack 채널로 전송합니다.

6. **처리 완료 후 로그 삭제**
   - 분석 완료된 로그는 즉시 `DeleteObject` 처리합니다.
   - 항상 최신 로그만 남기며 사실상 실시간 처리 구조를 구현합니다.

## 5. 버전 히스토리

### v1 (초기 버전)
- 단순히 S3에서 로그를 가져오기만 수행하였습니다.
- 중복 처리 및 불필요한 리소스 낭비가 발생하였습니다.

### v2 (현재 버전)
- **신규 로그만 분석**하도록 개선되었습니다.
- **분석 완료 후 S3에서 즉시 삭제**되도록 변경되었습니다.
- **거의 실시간 처리**가 가능해졌습니다.
- 이로써 비용 절감 및 운영 단순화를 달성하였습니다.

## 6. 주요 파일 설명

- **main.py** : 전체 실행 플로우 제어
- **log_parser.py** : CloudFront 로그 파싱 및 집계
- **gemini_client.py** : Gemini API 호출 및 인사이트 생성
- **slack_notify.py** : Slack 메시지 전송
- **db_client.py** (옵션) : 공연/결제/알림 DB 데이터 조인

## 7. 실행 흐름

```bash
# 가상환경 생성 및 라이브러리 설치
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Collector 실행
python main.py

# Flask 서버 모드 실행 (옵션)
export FLASK_APP=main.py
flask run --host=0.0.0.0 --port=5000
```

## 8. 운영/보안/비용 고려사항

- **IAM 최소 권한**: `s3:GetObject`, `s3:ListBucket`, `s3:DeleteObject`
- **비용 최적화**: 처리 완료 로그 즉시 삭제, 오래된 로그 Glacier 전환
- **지연 대응**: 로그 생성 지연 시 1~5분 버퍼 적용
- **Slack 장애 대응**: 업로드 실패 시 재시도 및 로컬 로그 기록

## 9. 실험/시뮬레이션 테스트

Collector를 검증하기 위하여, **의도적으로 CloudFront 로그를 발생시키는 bash 스크립트**를 실행하여 다양한 에러 상황 및 봇 요청을 시뮬레이션할 수 있습니다.

```bash
#!/bin/bash
echo "🚨 CloudFront 로그 트리거용 시뮬레이션 시작"

# ❌ 에러 요청 유도
echo "▶️ 404 Not Found 테스트"
curl -s -o /dev/null -i https://www.podopicker.store/api/not-a-real-endpoint

echo "▶️ 405 Method Not Allowed 테스트"
curl -s -o /dev/null -X PUT https://www.podopicker.store/api/performance

echo "▶️ 403 Forbidden 테스트"
curl -s -o /dev/null -i https://www.podopicker.store/secure-admin

echo "▶️ SQL Injection 유사 쿼리"
curl -s -o /dev/null -G "https://www.podopicker.store/search" --data-urlencode "q=' OR 1=1 --"

echo "▶️ .php 파일 접근 시도"
curl -s -o /dev/null -i https://www.podopicker.store/index.php

# 🤖 봇 요청 시뮬레이션
echo "▶️ Googlebot"
curl -s -o /dev/null -A "Googlebot/2.1 (+http://www.google.com/bot.html)" https://www.podopicker.store/

echo "▶️ Baiduspider"
curl -s -o /dev/null -A "Baiduspider" https://www.podopicker.store/

echo "▶️ Bingbot"
curl -s -o /dev/null -A "bingbot/2.0" https://www.podopicker.store/

echo "▶️ YandexBot"
curl -s -o /dev/null -A "YandexBot/3.0" https://www.podopicker.store/

echo "✅ 테스트 완료. 5분 후 Slack 알림 또는 MCP 로그 확인"
```

### 시뮬레이션 목적
- CloudFront 로그에 다양한 패턴(404, 403, SQL Injection, 봇 UA 등)을 강제로 남깁니다.
- Collector가 정상적으로 로그를 수집·분석·Slack 알림을 전송하는지 확인할 수 있습니다.
- 실제 운영 환경에서 **이상 트래픽 대응 테스트** 용도로 활용 가능합니다.

## 10. Slack 알림 예시
<table>
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/0611efb9-418b-47ec-83e9-eb92a70c4fbb" width="400"/><br/>
      <sub><b>v1 (초기 Collector)</b></sub>
    </td>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/5e32a82b-9f2e-4bae-ba2c-2b07e96c9bef" width="400"/><br/>
      <sub><b>v2 (실시간 Collector)</b></sub>
    </td>
  </tr>
</table>

### 📌 버전 차이 요약
- **v1 (초기 Collector)**  
  - 단순히 S3에서 로그를 가져와 Slack으로 전달하는 방식  
  - 몇 건의 에러가 발생했는지 “숫자만 집계”하는 수준  
  - 중복 처리·불필요한 로그 누적 문제 발생  

- **v2 (실시간 Collector)**  
  - 신규 로그만 처리하고 분석 완료 후 즉시 삭제하여 최신 상태 유지  
  - “에러 건수 + 발생 원인 + 대응 인사이트”까지 Slack 알림으로 제공  
  - 운영자가 바로 조치할 수 있도록 **실시간 탐지 및 인사이트 제공 구조**로 발전  
