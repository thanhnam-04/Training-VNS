import time
from abc import ABC, abstractmethod

class Employee(ABC):
    def __init__(self, emp_id, name, base_salary):
        self.emp_id = emp_id
        self.name = name
        self.base_salary = base_salary

    @abstractmethod
    def calculate_salary(self):
        pass

    def __str__(self):
        return f"[{self.emp_id}] {self.name} - Lương: ${self.calculate_salary():,.2f}"

class Manager(Employee):
    def __init__(self, emp_id, name, base_salary, bonus):
        super().__init__(emp_id, name, base_salary)
        self.bonus = bonus

    def calculate_salary(self):
        return self.base_salary + self.bonus
    
    def __str__(self):
        return super().__str__() + f" (Manager, Bonus: ${self.bonus})"

class Developer(Employee):
    def __init__(self, emp_id, name, base_salary, programming_language):
        super().__init__(emp_id, name, base_salary)
        self.programming_language = programming_language

    def calculate_salary(self):
        return self.base_salary
    
    def __str__(self):
        return super().__str__() + f" (Developer, Ngôn ngữ: {self.programming_language})"

class HRSystemManager:
    def __init__(self):
        self.employees = []

    def __enter__(self):
        print(">> [System] Đang khởi động Hệ thống quản lý nhân sự...")
        print(">> [System] Sẵn sàng nhận lệnh.\n")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("\n>> [System] Đang đóng Hệ thống quản lý...")
        if exc_type:
            print(f">> [System] Đã xảy ra lỗi: {exc_val}")
        print(">> [System] Đã lưu dữ liệu và thoát an toàn.")

    def add_employee(self, employee):
        self.employees.append(employee)
        print(f"-> Đã thêm nhân viên: {employee.name}")

    def edit_employee(self, emp_id, name, base_salary, extra_attr=None):
        for emp in self.employees:
            if emp.emp_id == emp_id:
                emp.name = name
                emp.base_salary = base_salary
                if isinstance(emp, Manager) and extra_attr is not None:
                    emp.bonus = extra_attr
                elif isinstance(emp, Developer) and extra_attr is not None:
                    emp.programming_language = extra_attr
                print(f"-> Đã cập nhật nhân viên: {emp_id}")
                return True
        print(f"-> Không tìm thấy nhân viên: {emp_id}")
        return False

    def delete_employee(self, emp_id):
        for emp in self.employees:
            if emp.emp_id == emp_id:
                self.employees.remove(emp)
                print(f"-> Đã xóa nhân viên: {emp_id}")
                return True
        print(f"-> Không tìm thấy nhân viên: {emp_id}")
        return False

def high_salary_generator(employees, min_salary):
    for emp in employees:
        if emp.calculate_salary() >= min_salary:
            yield emp

def main():
    with HRSystemManager() as hr:
        # Dữ liệu mẫu (có thể giữ lại để test nhanh)
        hr.add_employee(Manager("M01", "Nguyen Van A", 2000, 500))
        hr.add_employee(Developer("D01", "Tran Thi B", 1500, "Python"))

        while True:
            print("\n" + "="*40)
            print("HỆ THỐNG QUẢN LÝ NHÂN SỰ".center(40))
            print("="*40)
            print("1. Thêm nhân viên (Manager/Developer)")
            print("2. Sửa thông tin nhân viên")
            print("3. Xóa nhân viên")
            print("4. Hiển thị danh sách & tính lương")
            print("5. Danh sách nhân viên lương cao (>= $2000)")
            print("6. Thoát")
            print("="*40)
            
            choice = input("Vui lòng chọn chức năng (1-6): ")

            if choice == '1':
                emp_type = input("Loại nhân viên (1=Manager, 2=Developer): ")
                emp_id = input("Nhập ID: ")
                name = input("Nhập tên: ")
                try:
                    base_salary = float(input("Nhập lương cơ bản ($): "))
                except ValueError:
                    print("Lương không hợp lệ!")
                    continue
                
                if emp_type == '1':
                    try:
                        bonus = float(input("Nhập tiền thưởng ($): "))
                    except ValueError:
                        print("Tiền thưởng không hợp lệ!")
                        continue
                    hr.add_employee(Manager(emp_id, name, base_salary, bonus))
                elif emp_type == '2':
                    lang = input("Nhập ngôn ngữ lập trình: ")
                    hr.add_employee(Developer(emp_id, name, base_salary, lang))
                else:
                    print("Lựa chọn loại nhân viên không hợp lệ!")

            elif choice == '2':
                emp_id = input("Nhập ID nhân viên cần sửa: ")
                name = input("Nhập tên mới: ")
                try:
                    base_salary = float(input("Nhập lương cơ bản mới ($): "))
                except ValueError:
                    print("Lương không hợp lệ!")
                    continue
                
                # Check loại hiện tại để hỏi thuộc tính thêm
                found_emp = next((e for e in hr.employees if e.emp_id == emp_id), None)
                if found_emp:
                    if isinstance(found_emp, Manager):
                        try:
                            extra = float(input("Nhập tiền thưởng mới ($): "))
                        except ValueError:
                            print("Tiền thưởng không hợp lệ!")
                            continue
                    else:
                        extra = input("Nhập ngôn ngữ lập trình mới: ")
                    hr.edit_employee(emp_id, name, base_salary, extra)
                else:
                    print(f"-> Không tìm thấy nhân viên: {emp_id}")

            elif choice == '3':
                emp_id = input("Nhập ID nhân viên cần xóa: ")
                hr.delete_employee(emp_id)

            elif choice == '4':
                print(f"\n--- DANH SÁCH {len(hr.employees)} NHÂN VIÊN ---")
                if not hr.employees:
                    print("Chưa có nhân viên nào.")
                for emp in hr.employees:
                    print(emp)

            elif choice == '5':
                print("\n--- NHÂN VIÊN CÓ MỨC LƯƠNG CAO (>= $2000) ---")
                high_earners = list(high_salary_generator(hr.employees, 2000))
                if not high_earners:
                    print("Không có nhân viên nào đạt mức lương >= $2000.")
                for emp in high_earners:
                    print(emp)

            elif choice == '6':
                print("Đang chuẩn bị thoát chương trình...")
                break
            else:
                print("Lựa chọn không hợp lệ. Vui lòng chọn từ 1 đến 6.")

if __name__ == "__main__":
    main()
