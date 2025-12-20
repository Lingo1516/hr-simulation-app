import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import platform
import os

# 忽略警告訊息
warnings.filterwarnings('ignore')

# ---------------------------------------------------------
# 1. 設定中文字型 (這是讓圖表顯示中文的關鍵)
# ---------------------------------------------------------
def set_chinese_font():
    system_name = platform.system()
    if system_name == "Windows":
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] # 微軟正黑體
    elif system_name == "Darwin": # Mac
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    else:
        plt.rcParams['font.sans-serif'] = ['SimHei'] # Linux/Colab
    plt.rcParams['axes.unicode_minus'] = False # 解決負號顯示問題

set_chinese_font()

# ---------------------------------------------------------
# 2. 資料讀取與預處理 (針對您的檔案格式特別優化)
# ---------------------------------------------------------
print("🔄 正在讀取 HR 員工離職資料...")

# 您的檔案名稱
file_name = 'HR-Employee-Attrition-完美中文版.xlsx - 工作表 1 - HR-Employee-Attrition-完.csv'

# 檢查檔案是否存在
if not os.path.exists(file_name):
    print(f"❌ 錯誤：找不到檔案 '{file_name}'")
    print("請確認檔案是否已下載，並放在與此程式相同的資料夾中。")
    exit()

try:
    # 關鍵修正：header=1 表示跳過第一列(檔案標題)，從第二列開始讀取欄位
    df = pd.read_csv(file_name, header=1)
    
    # 關鍵修正：將 '流失' 欄位改名為 '離職' 以配合後續程式
    if '流失' in df.columns:
        df.rename(columns={'流失': '離職'}, inplace=True)
    
    print(f"✅ 成功讀取！資料總覽：{df.shape[0]}筆員工資料，{df.shape[1]}個欄位")
    print("-" * 30)

except Exception as e:
    print(f"❌ 讀取檔案時發生未預期的錯誤：\n{e}")
    exit()

# ---------------------------------------------------------
# 3. 定義分析功能函數
# ---------------------------------------------------------

def 離職分析篩選():
    print("\n" + "="*60)
    print("🎯 功能 1：員工離職互動篩選")
    print("="*60)
    
    print("\n請依序輸入篩選條件 (直接按 Enter 可跳過)：")
    性別 = input("1. 性別 (男/女)：").strip()
    部門 = input("2. 部門關鍵字 (如：研發, 銷售)：").strip()
    加班 = input("3. 是否加班 (是/否)：").strip()
    
    # 複製一份資料來篩選
    filtered_df = df.copy()
    
    if 性別:
        filtered_df = filtered_df[filtered_df['性別'] == 性別]
    if 部門:
        filtered_df = filtered_df[filtered_df['部門'].str.contains(部門, na=False)]
    if 加班:
        filtered_df = filtered_df[filtered_df['加班'] == 加班]
    
    # 計算統計數據
    總人數 = len(filtered_df)
    離職人數 = len(filtered_df[filtered_df['離職'] == '是'])
    離職率 = (離職人數 / 總人數 * 100) if 總人數 > 0 else 0
    
    print(f"\n📊 篩選結果：")
    print(f"   符合條件人數：{總人數} 人")
    print(f"   其中離職人數：{離職人數} 人")
    print(f"   該族群離職率：{離職率:.1f}%")
    print(f"   (全公司平均離職率：{(df['離職']=='是').mean()*100:.1f}%)")
    
    return filtered_df

def 年齡分組分析():
    print("\n" + "="*50)
    print("🎂 功能 2：年齡分組離職分析")
    print("="*50)
    
    # 建立年齡區間
    df['年齡組'] = pd.cut(df['年齡'], bins=[0, 25, 35, 45, 55, 100], 
                        labels=['25歲以下', '25-34歲', '35-44歲', '45-54歲', '55歲以上'])
    
    age_analysis = df.groupby('年齡組').agg({
        '離職': lambda x: (x == '是').sum(),
        '年齡': 'count' # 計算總人數
    }).rename(columns={'離職': '離職人數', '年齡': '總人數'})
    
    age_analysis['離職率(%)'] = (age_analysis['離職人數'] / age_analysis['總人數'] * 100).round(1)
    
    print(age_analysis)
    
    # 繪圖
    plt.figure(figsize=(10, 6))
    bars = plt.bar(age_analysis.index, age_analysis['離職率(%)'], color='skyblue', alpha=0.8)
    plt.title('各年齡層離職率比較', fontsize=16)
    plt.ylabel('離職率 (%)')
    plt.xlabel('年齡組')
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    
    # 在柱狀圖上標示數字
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.show()
    print("\n💡 圖表已顯示，請查看彈出視窗。")

def 性別部門分析():
    print("\n" + "="*50)
    print("👫 功能 3：性別 x 部門交叉分析")
    print("="*50)
    
    # 製作交叉表
    pivot = df.pivot_table(index='部門', columns='性別', 
                         values='離職', aggfunc=lambda x: (x == '是').mean()*100)
    
    print("各部門性別離職率(%)：")
    print(pivot.round(1))
    
    # 繪圖
    pivot.plot(kind='bar', figsize=(10, 6), rot=0)
    plt.title('各部門性別離職率比較', fontsize=16)
    plt.ylabel('離職率 (%)')
    plt.legend(title='性別')
    plt.tight_layout()
    plt.show()
    print("\n💡 圖表已顯示，請查看彈出視窗。")

# ---------------------------------------------------------
# 4. 主程式執行迴圈
# ---------------------------------------------------------
if __name__ == "__main__":
    while True:
        print("\n" + "█"*30)
        print(" 🚀 HR 員工離職數據分析系統")
        print("█"*30)
        print("1. 互動篩選 (自訂條件查詢)")
        print("2. 年齡分組分析 (查看哪個年紀最容易走)")
        print("3. 性別與部門交叉分析")
        print("4. 查看所有欄位名稱")
        print("0. 結束程式")
        
        choice = input("\n請輸入選項 (0-4)：").strip()
        
        if choice == '1':
            離職分析篩選()
        elif choice == '2':
            年齡分組分析()
        elif choice == '3':
            性別部門分析()
        elif choice == '4':
            print(f"\n📝 欄位清單：\n{list(df.columns)}")
        elif choice == '0':
            print("👋 程式結束，謝謝使用！")
            break
        else:
            print("❌ 無效選項，請重新輸入！")
