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
