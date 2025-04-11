import os
import sys
import tkinter as tk
from register_kiosk_org_pg.kiosk_admin_register import KioskAdminRegistrationApp

def main():
    """
    키오스크 관리자 등록 애플리케이션을 실행합니다.
    """
    root = tk.Tk()
    app = KioskAdminRegistrationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
