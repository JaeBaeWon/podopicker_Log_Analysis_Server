import gzip
from datetime import datetime
from collections import defaultdict


def parse_log_file(file_path):
    results = {
        "errors": [],
        "bots": [],
        "repeated": defaultdict(list),  # IP -> list of datetime
    }

    with gzip.open(file_path, 'rt') as f:
        headers = []
        for line in f:
            if line.startswith("#Fields:"):
                headers = line.strip().split()[1:]
                continue
            if line.startswith("#") or line.strip() == "":
                continue

            fields = line.strip().split('\t')
            if not headers or len(fields) != len(headers):
                continue

            data = dict(zip(headers, fields))

            ip = data.get('c-ip', '')
            ua = data.get('cs(User-Agent)', '').lower()
            status = data.get('sc-status', '')
            try:
                date_str = f"{data.get('date')} {data.get('time')}"
                timestamp = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                continue

            # 에러 상태코드
            if status.startswith(('4', '5')):
                results["errors"].append({
                    "ip": ip,
                    "uri": data.get('cs-uri-stem'),
                    "status": status,
                    "time": timestamp.isoformat()
                })

            # 봇 감지
            if any(bot in ua for bot in ['bot', 'crawl', 'spider']):
                results["bots"].append({
                    "ip": ip,
                    "ua": ua,
                    "uri": data.get('cs-uri-stem'),
                    "time": timestamp.isoformat()
                })

            # 반복 요청 수집
            results["repeated"][ip].append(timestamp)

    return results
