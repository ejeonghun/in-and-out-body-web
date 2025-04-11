import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json
import os
import sys
from PIL import Image, ImageTk
import io
import urllib.request
import wmi

def get_motherboard_serial():
    try:
        # Connect to the WMI service
        c = wmi.WMI()

        # Query the Win32_BIOS class to get the serial number
        bios = c.Win32_BIOS()[0]
        serial_number = bios.SerialNumber
        print(serial_number)
        return serial_number
    except Exception as e:
        messagebox.showerror("Error", f"시리얼 번호 추출 실패: {str(e)}")
        return None

class KioskAdminRegistrationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("기관 관리자 등록")
        self.root.geometry("800x900")
        self.root.resizable(True, True)
        
        # 서버 URL 설정
        self.server_url = "http://localhost:8000"  # 실제 서버 URL로 변경 필요
        
        # 변수 초기화
        self.selected_org = None
        self.search_results = []
        
        self.serial_number = get_motherboard_serial()

        # UI 구성
        self.create_widgets()
        
    def create_widgets(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="기관 관리자 등록", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        # 시리얼 번호 표시
        if self.serial_number:
            serial_label = ttk.Label(main_frame, text=f"시리얼 번호: {self.serial_number}")
            serial_label.pack(pady=5)
        
        else:
            serial_label = ttk.Label(main_frame, text="시리얼 번호를 찾을 수 없습니다.")
            serial_label.pack(pady=5)
        
        # 검색 프레임
        search_frame = ttk.LabelFrame(main_frame, text="기관 검색", padding="10")
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 검색 입력 및 버튼
        search_entry_frame = ttk.Frame(search_frame)
        search_entry_frame.pack(fill=tk.X, pady=5)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_entry_frame, textvariable=self.search_var, width=50)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        search_button = ttk.Button(search_entry_frame, text="검색", command=self.search_organization)
        search_button.pack(side=tk.LEFT, padx=5)
        
        # 검색 결과 트리뷰
        result_frame = ttk.LabelFrame(main_frame, text="검색 결과", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.result_tree = ttk.Treeview(result_frame, columns=("name", "address", "contact"), show="headings")
        self.result_tree.heading("name", text="기관명")
        self.result_tree.heading("address", text="주소")
        self.result_tree.heading("contact", text="연락처")
        
        self.result_tree.column("name", width=150)
        self.result_tree.column("address", width=300)
        self.result_tree.column("contact", width=150)
        
        self.result_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        # 선택 이벤트 바인딩
        self.result_tree.bind("<<TreeviewSelect>>", self.on_org_select)
        
        # 선택된 기관 정보 프레임
        self.selected_frame = ttk.LabelFrame(main_frame, text="선택된 기관 정보", padding="10")
        self.selected_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.org_name_label = ttk.Label(self.selected_frame, text="기관명: ")
        self.org_name_label.pack(anchor=tk.W, pady=2)
        
        self.org_address_label = ttk.Label(self.selected_frame, text="주소: ")
        self.org_address_label.pack(anchor=tk.W, pady=2)
        
        self.org_contact_label = ttk.Label(self.selected_frame, text="연락처: ")
        self.org_contact_label.pack(anchor=tk.W, pady=2)
        
        # 관리자 정보 입력 프레임
        admin_frame = ttk.LabelFrame(main_frame, text="관리자 정보 입력", padding="10")
        admin_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 관리자 ID
        admin_id_frame = ttk.Frame(admin_frame)
        admin_id_frame.pack(fill=tk.X, pady=5)
        
        admin_id_label = ttk.Label(admin_id_frame, text="관리자 ID:", width=15)
        admin_id_label.pack(side=tk.LEFT, padx=5)
        
        self.admin_id_var = tk.StringVar()
        admin_id_entry = ttk.Entry(admin_id_frame, textvariable=self.admin_id_var, width=30)
        admin_id_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 관리자 비밀번호
        admin_pw_frame = ttk.Frame(admin_frame)
        admin_pw_frame.pack(fill=tk.X, pady=5)
        
        admin_pw_label = ttk.Label(admin_pw_frame, text="비밀번호:", width=15)
        admin_pw_label.pack(side=tk.LEFT, padx=5)
        
        self.admin_pw_var = tk.StringVar()
        admin_pw_entry = ttk.Entry(admin_pw_frame, textvariable=self.admin_pw_var, width=30, show="*")
        admin_pw_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 관리자 비밀번호 확인
        admin_pw_confirm_frame = ttk.Frame(admin_frame)
        admin_pw_confirm_frame.pack(fill=tk.X, pady=5)
        
        admin_pw_confirm_label = ttk.Label(admin_pw_confirm_frame, text="비밀번호 확인:", width=15)
        admin_pw_confirm_label.pack(side=tk.LEFT, padx=5)
        
        self.admin_pw_confirm_var = tk.StringVar()
        admin_pw_confirm_entry = ttk.Entry(admin_pw_confirm_frame, textvariable=self.admin_pw_confirm_var, width=30, show="*")
        admin_pw_confirm_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 등록 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        register_button = ttk.Button(button_frame, text="등록하기", command=self.register_admin)
        register_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="취소", command=self.root.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def search_organization(self):
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("검색 오류", "검색어를 입력해주세요.")
            return
        
        try:
            # 카카오맵 API 호출
            response = requests.get(
                f"{self.server_url}/api/search-organization/",
                params={"query": query}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.search_results = data.get('results', [])
                
                # 트리뷰 초기화
                for item in self.result_tree.get_children():
                    self.result_tree.delete(item)
                
                # 검색 결과 표시
                for idx, org in enumerate(self.search_results):
                    self.result_tree.insert("", tk.END, values=(
                        org.get('name', ''),
                        org.get('address', ''),
                        org.get('contact', '')
                    ))
                
                if not self.search_results:
                    messagebox.showinfo("검색 결과", "검색 결과가 없습니다.")
            else:
                messagebox.showerror("검색 오류", f"서버 오류: {response.status_code}")
        
        except Exception as e:
            messagebox.showerror("검색 오류", f"오류가 발생했습니다: {str(e)}")
    
    def on_org_select(self, event):
        selected_items = self.result_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        idx = self.result_tree.index(item)
        
        if idx < len(self.search_results):
            self.selected_org = self.search_results[idx]
            
            # 선택된 기관 정보 표시
            self.org_name_label.config(text=f"기관명: {self.selected_org.get('name', '')}")
            self.org_address_label.config(text=f"주소: {self.selected_org.get('address', '')}")
            self.org_contact_label.config(text=f"연락처: {self.selected_org.get('contact', '')}")
    
    def register_admin(self):
        # 유효성 검사
        if not self.selected_org:
            messagebox.showwarning("등록 오류", "기관을 선택해주세요.")
            return
        
        admin_id = self.admin_id_var.get().strip()
        admin_pw = self.admin_pw_var.get()
        admin_pw_confirm = self.admin_pw_confirm_var.get()
        
        if not admin_id:
            messagebox.showwarning("등록 오류", "관리자 ID를 입력해주세요.")
            return
        
        if not admin_pw:
            messagebox.showwarning("등록 오류", "비밀번호를 입력해주세요.")
            return
        
        if admin_pw != admin_pw_confirm:
            messagebox.showwarning("등록 오류", "비밀번호가 일치하지 않습니다.")
            return
        
        try:
            # 기관 등록 및 관리자 계정 생성 API 호출
            response = requests.post(
                f"{self.server_url}/api/register-admin-organization/",
                json={
                    "org_name": self.selected_org.get('name', ''),
                    "address": self.selected_org.get('address', ''),
                    "contact_number": self.selected_org.get('contact', ''),
                    "admin_id": admin_id,
                    "admin_password": admin_pw
                }
            )
            
            if response.status_code == 200:
                messagebox.showinfo("등록 성공", "기관 및 관리자 계정이 성공적으로 등록되었습니다.")
                self.root.destroy()
            else:
                data = response.json()
                messagebox.showerror("등록 오류", f"서버 오류: {data.get('message', '알 수 없는 오류')}")
        
        except Exception as e:
            messagebox.showerror("등록 오류", f"오류가 발생했습니다: {str(e)}")

def main():
    root = tk.Tk()
    app = KioskAdminRegistrationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
