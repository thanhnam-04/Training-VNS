import json
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select, insert

# 1. KẾT NỐI (Tạo Engine) qua SQLAlchemy Core
# Mặc định sử dụng SQLite để dễ thực hành.
# Có thể đổi kết nối sang PostgreSQL: 'postgresql://user:pass@localhost:5432/dbname'
# Hoặc MySQL: 'mysql+pymysql://user:pass@localhost/dbname'
db_url = 'sqlite:///cars_database.db'

# Tham số `echo=True` giúp in ra câu lệnh SQL raw trên console để bạn dễ theo dõi
engine = create_engine(db_url, echo=False)

# 2. ĐỊNH NGHĨA SCHEMA (MetaData và Table)
metadata = MetaData()

# Chú ý: Đây là cách định nghĩa theo chuẩn Core (không phải ORM)
oto_table = Table(
    'cars', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String, nullable=False),
    Column('price', String, nullable=True)
)

# Tạo bảng ('cars') trong Database nếu chưa tồn tại
metadata.create_all(engine)

# 3. THAO TÁC VỚI DATABASE BẰNG CORE (Insert, Select)

def insert_car(name: str, price: str):
    """
    Sử dụng engine.begin() để tự động quản lý transaction (commit nếu thành công, rollback nếu lỗi)
    """
    with engine.begin() as conn:
        stmt = insert(oto_table).values(name=name, price=price)
        conn.execute(stmt)

def get_all_cars():
    """
    Sử dụng engine.connect() khi chỉ cần đọc (Select) dữ liệu
    """
    with engine.connect() as conn:
        stmt = select(oto_table)
        result = conn.execute(stmt)
        return result.fetchall()

def get_cars_by_name(search_name: str):
    """
    Tìm xe theo tên chính xác
    """
    with engine.connect() as conn:
        stmt = select(oto_table).where(oto_table.c.name == search_name)
        result = conn.execute(stmt)
        return result.fetchall()

def load_from_json_and_save(json_filepath: str):
    """Đọc file json hiện tại và lưu vào DB"""
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            with engine.begin() as conn:
                for item in data:
                    # Chú ý handle các field sao cho khớp file JSON của bạn
                    stmt = insert(oto_table).values(
                        name=item.get('name', 'Unknown'),
                        price=item.get('price', 'N/A')
                    )
                    conn.execute(stmt)
            print("Đã lưu dữ liệu từ JSON vào DB thành công!")
    except FileNotFoundError:
        print(f"Không tìm thấy file {json_filepath}")
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    print("--- Chạy thử Insert dữ liệu tĩnh ---")
    insert_car("Toyota Vios 2024", "450 Triệu")
    insert_car("Honda Civic Type R", "2 Tỷ")

    # Nếu bạn có file oto_data.json từ script crawl data của bạn (Day 3),
    # mở comment dòng dưới để chạy thử ném data crawl vào SQLite
    # load_from_json_and_save("oto_data.json")

    print("\n--- Danh sách dữ liệu trong DB ---")
    cars = get_all_cars()
    for car in cars:
        print(f"ID: {car.id} | Xe: {car.name} | Giá: {car.price}")

    print("\n--- Danh sách xe Honda Civic Type R ---")
    civics = get_cars_by_name("Honda Civic Type R")
    for car in civics:
        print(f"ID: {car.id} | Xe: {car.name} | Giá: {car.price}")
