# Chạy lại bài lab trên macOS

Bài của Nguyễn Văn Hưởng — 2A202602743, dùng ontology gợi ý.

## Môi trường

- Python 3.11 (lần đo dùng 3.11.16).
- Thư viện trong `requirements.txt`.
- Docker Desktop và Neo4j 5, cổng local 7474/7687.
- Điền `OPENAI_API_KEY` trong `.env`; lần đo dùng `LLM_PROVIDER=openai`, `EMBEDDING_PROVIDER=openai`, các model mặc định.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Nếu chưa có `.env`, sao chép `.env.example` thành `.env` rồi tự điền key.

Container đã tạo trên máy hiện tại: `neo4j-drug-kg`, Docker volume `neo4j-drug-kg-data`. Khi chuyển sang máy mới, tạo một lần:

```bash
docker run -d --name neo4j-drug-kg --restart unless-stopped \
  -p 127.0.0.1:7474:7474 -p 127.0.0.1:7687:7687 \
  -v neo4j-drug-kg-data:/data \
  -e NEO4J_AUTH=neo4j/password123 neo4j:5
```

Các lần sau bật Docker Desktop và dùng `docker start neo4j-drug-kg` nếu container đang dừng.

## Thứ tự kiểm tra và lấy kết quả

```bash
source .venv/bin/activate
python -m pytest tests/ -q
python bench_kg.py --check
python bench_kg.py --judge
python scripts/audit_kg.py
```

`--check` và `--judge` đều xóa/dựng lại dữ liệu trong database Neo4j được cấu hình. Chỉ trỏ `.env` tới database lab. Lệnh `--judge` gọi API và ghi `ket_qua_benchmark_kg.txt`. `audit_kg.py` chỉ đọc graph, ghi snapshot bằng chứng vào `report/validation/graph_audit.json`.

Lần nộp này: 48 tests pass; check đủ 7 `[OK]`; graph đầy đủ 206 node / 384 cạnh. Một lần chạy mới có thể tạo số node và số liệu khác do LLM/API, khi đó phải cập nhật đồng bộ báo cáo và ảnh. Không chạy `--check` sau khi chụp ảnh graph đầy đủ, trừ khi định dựng lại graph và cập nhật ảnh.

## Truy vấn cho ba ảnh

Mở http://localhost:7474, kết nối `neo4j://localhost:7687`, user `neo4j`, password `password123`. Chạy `:clear` trước mỗi truy vấn. Chụp nguyên cửa sổ, giữ ô truy vấn và Results overview (với kết quả Graph).

### kg_count.png

```cypher
MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC;
```

### kg_cross_kb.png

```cypher
MATCH p=(:Person)-[:INVOLVED_IN]->(:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(:Article)
RETURN p LIMIT 25;
```

### kg_my_case.png

```cypher
MATCH p=(:Person {name:'Cái Quang Huy'})-[:INVOLVED_IN]->(k:Case)
-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(:Article)
OPTIONAL MATCH q=(k)-[:INVOLVES|LOCATED_IN]->()
RETURN p, q;
```

## File bài nộp

- `src/graph.py`: KG-1 đến KG-4.
- `ket_qua_benchmark_kg.txt`: kết quả nguyên bản với judge.
- `report/ONTOLOGY.md`: thiết kế.
- `report/REPORT_KG.md`: số liệu, phân tích lỗi, kết luận, tự kiểm.
- `report/img/`: ba ảnh Neo4j.
- `report/validation/`: output kiểm tra và snapshot bằng chứng.

Repo theo quy cách môn học: `K4-DAY19-NguyenVanHuong-2A202602743`. Đưa bài lên repo cá nhân và nộp link trên vlearn. `.env` và `.venv/` đã được gitignore.
